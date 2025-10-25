# backtest_analytics.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Iterable
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import polars as pl

# Import your dashboard types for seamless plug-in
from dashboard import DashboardManifest, CustomFigure, CustomTable, QuantStatsDashboard

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _ensure_datetime_ns(lf: pl.LazyFrame, date_col: str = "date") -> pl.LazyFrame:
    return lf.with_columns(pl.col(date_col).cast(pl.Datetime).dt.cast_time_unit("ns"))

def _pd_from_pl_df(df: pl.DataFrame, date_col: Optional[str] = None, index_from_date: bool = False) -> pd.DataFrame:
    pdf = df.to_pandas()
    if index_from_date and date_col and (date_col in pdf.columns):
        dt = pd.to_datetime(pdf[date_col], errors="coerce")
        try:
            dt = dt.dt.tz_localize(None)
        except Exception:
            dt = pd.DatetimeIndex(dt).tz_localize(None)
        pdf = pdf.drop(columns=[date_col])
        pdf.index = pd.DatetimeIndex(dt)
        pdf.sort_index(inplace=True)
    return pdf

def _pd_series_from_pl_two_cols(df: pl.DataFrame, date_col: str, val_col: str, name: Optional[str] = None) -> pd.Series:
    pdf = _pd_from_pl_df(df.select([pl.col(date_col), pl.col(val_col)]), date_col=date_col, index_from_date=True)
    s = pdf.iloc[:, 0]
    s.name = str(name or val_col)
    return s

# ---------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------

@dataclass
class BacktestAnalytics:
    """
    Wraps lazy returns/benchmark/weights and exposes:
      - manifest for tearsheet grouping (Backtest vs Other)
      - custom figures & tables
    """
    returns_lf: pl.LazyFrame            # wide: ["date", strat1, strat2, ...] (excess or raw)
    benchmark_lf: Optional[pl.LazyFrame] = None  # ["date", "Benchmark"] optional
    weights_long_lf: Optional[pl.LazyFrame] = None  # ["date","name","asset","weight"] optional

    # Which metrics should belong to the 'Backtest' group label (display names from your dashboard)
    backtest_display_labels: Tuple[str, ...] = (
        "Cumulative Return", "CAGR﹪", "Sharpe", "Sortino", "Volatility (ann.)", "Calmar",
        "Time in Market", "Avg. Win", "Avg. Loss", "Payoff Ratio", "Win Days",
    )

    def _turnover_series(self) -> Optional[pd.Series]:
        """
        Turnover per date per strategy: 0.5 * sum_assets |w_t - w_{t-1}| (sum over assets).
        Returns pandas Series (sum over strategies) just for an easy, legible demo plot.
        """
        if self.weights_long_lf is None:
            return None
        W = _ensure_datetime_ns(self.weights_long_lf)
        # diff within (name, asset), then sum abs diffs per date/name; finally aggregate across names
        diffs = (
            W.with_columns([
                (pl.col("weight") - pl.col("weight").shift(1).over(["name", "asset"]))
                .abs()
                .alias("_d")
            ])
            .group_by(["date", "name"])
            .agg((pl.col("_d").sum() * 0.5).alias("turnover"))
            .group_by("date")
            .agg(pl.col("turnover").sum().alias("turnover_all"))
            .sort("date")
            .collect()
        )
        return _pd_series_from_pl_two_cols(diffs, "date", "turnover_all", name="Turnover")

    def _weights_heatmap_df(self) -> Optional[pd.DataFrame]:
        """
        Build a simple weights pivot (last 60 dates by default) for a compact heatmap.
        """
        if self.weights_long_lf is None:
            return None
        W = _ensure_datetime_ns(self.weights_long_lf)
        last60 = (
            W.sort("date")
             .tail(60)
             .select(["date","asset","weight"])
             .pivot(index="date", columns="asset", values="weight")
             .sort("date")
             .collect()
        )
        pdf = _pd_from_pl_df(last60, date_col="date", index_from_date=True)
        return pdf

    # ----------------- Custom figures -----------------

    def custom_figures(self) -> List[CustomFigure]:
        figs: List[CustomFigure] = []

        def fig_turnover():
            s = self._turnover_series()
            if s is None or s.empty:
                return None
            fig = plt.figure(figsize=(7, 3))
            ax = fig.add_subplot(111)
            ax.plot(s.index, s.values)
            ax.set_title("Portfolio Turnover (sum over strategies)")
            ax.set_ylabel("0.5 * Σ|Δw|")
            ax.grid(True, alpha=0.3)
            fig.autofmt_xdate()
            return fig

        def fig_weights_heatmap():
            pdf = self._weights_heatmap_df()
            if pdf is None or pdf.empty:
                return None
            fig = plt.figure(figsize=(7, 4))
            ax = fig.add_subplot(111)
            # basic heatmap with matplotlib imshow
            data = pdf.to_numpy()
            im = ax.imshow(data, aspect="auto", origin="lower")
            ax.set_title("Weights (last 60 dates)")
            ax.set_yticks(np.arange(len(pdf.index))[::max(1, len(pdf.index)//6)])
            ax.set_yticklabels([d.strftime("%Y-%m-%d") for d in pdf.index[::max(1, len(pdf.index)//6)]], fontsize=8)
            ax.set_xticks(np.arange(len(pdf.columns)))
            ax.set_xticklabels(pdf.columns, rotation=90, fontsize=8)
            fig.colorbar(im, ax=ax, fraction=0.032, pad=0.04)
            return fig

        figs.append(CustomFigure(key="bt_turnover", title="Turnover", builder=lambda *_: fig_turnover(), per_strategy=False))
        figs.append(CustomFigure(key="bt_weights",  title="Weights Heatmap", builder=lambda *_: fig_weights_heatmap(), per_strategy=False))
        return figs

    # ----------------- Custom tables -----------------

    def custom_tables(self) -> List[CustomTable]:
        # Example: tiny live snapshot table of last returns per strategy (pure rendering)
        def tbl_last_returns(pdf: pd.DataFrame, bench: Optional[pd.Series]) -> pd.DataFrame:
            # ignore provided pdf; use our lazy returns
            lf = _ensure_datetime_ns(self.returns_lf)
            cols = [c for c in lf.collect_schema().names() if c != "date"]
            last = lf.sort("date").tail(1).collect()
            pdf2 = last.to_pandas().set_index("date")
            out = pdf2[cols].T
            out.columns = ["Last Return"]
            return out

        return [
            CustomTable(key="bt_last", title="Last Step Returns", builder=tbl_last_returns, controlled=True)
        ]

    # ----------------- Manifest for the tearsheet -----------------

    def build_manifest(self) -> DashboardManifest:
        """
        - Put every QuantStats figure in
        - Group metrics with 'Backtest' labels; leave leftovers to 'Other' via strict_metric_groups=False
        - Include all standard tables
        - Attach our custom figures/tables
        """
        bt_group = {"Backtest": list(self.backtest_display_labels)}
        return DashboardManifest(
            figures=[
                # full set of figures already supported by your tearsheet
                "snapshot", "earnings", "returns", "log_returns", "yearly_returns",
                "daily_returns", "rolling_beta", "rolling_volatility", "rolling_sharpe",
                "rolling_sortino", "drawdowns_periods", "drawdown", "monthly_heatmap",
                "histogram", "distribution",
            ],
            tables=["metrics", "eoy", "monthly_returns", "drawdown_details"],
            metric_groups=[bt_group],              # only 'Backtest' ; leftovers => "Other"
            strict_metric_groups=False,            # important: let leftovers auto-render as "Other"
            custom_tables=self.custom_tables(),
            custom_figures=self.custom_figures(),
        )

    # ----------------- Builder -----------------

    def build_dashboard(
        self,
        *,
        title: str = "Backtest Tearsheet",
        output_dir: str = "output/dash_backtest",
        periods_per_year: int = 252,
        rf: float | int | None = 0.0,
    ) -> QuantStatsDashboard:
        m = self.build_manifest()
        return QuantStatsDashboard(
            returns_df=self.returns_lf,       # already lazy, wide
            benchmark=self.benchmark_lf,      # optional lazy
            rf=rf,
            title=title,
            output_dir=output_dir,
            manifest=m,
            periods_per_year=periods_per_year,
        )