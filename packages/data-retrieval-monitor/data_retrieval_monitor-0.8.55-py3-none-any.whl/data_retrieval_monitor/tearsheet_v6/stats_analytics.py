# stats_analytics.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from math import erf, sqrt, log
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import polars as pl

from dashboard import DashboardManifest, CustomFigure, CustomTable, QuantStatsDashboard


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


@dataclass
class StatisticsAnalytics:
    """
    Prediction/Target analytics.

    Inputs (lazy):
      - pred_lf:   ["date", "pred"]           (or your preferred column name)
      - target_lf: ["date", "target"]
    """
    pred_lf: pl.LazyFrame
    target_lf: pl.LazyFrame
    pred_col: str = "pred"
    target_col: str = "target"

    # ----------------- Core joins -----------------

    def _aligned(self) -> pl.LazyFrame:
        P = _ensure_datetime_ns(self.pred_lf)
        T = _ensure_datetime_ns(self.target_lf)
        return (
            P.select(["date", pl.col(self.pred_col).alias("pred")])
             .join(T.select(["date", pl.col(self.target_col).alias("target")]), on="date", how="inner")
             .sort("date")
        )

    # ----------------- IC grid (lags x horizons) -----------------

    def _ic_agg(self, lag: int, horizon: int) -> Dict[str, float]:
        """
        Compute Pearson correlation between pred(t-lag) and mean(target[t+1...t+horizon]).
        Fully in Polars for sums; small final math in Python (no pandas).
        """
        base = self._aligned()

        # Predictor lag
        X = base.with_columns(pl.col("pred").shift(lag).alias("x"))

        # Future target average over horizon
        if horizon <= 0:
            raise ValueError("horizon must be >= 1")
        if horizon == 1:
            Y = X.with_columns(pl.col("target").shift(-1).alias("y"))
        else:
            # avg of lead 1..h
            leads = [pl.col("target").shift(-j) for j in range(1, horizon + 1)]
            Y = X.with_columns((sum(leads) / float(horizon)).alias("y"))

        # Drop rows with any nulls and aggregate raw sums
        AG = (
            Y.select([
                pl.col("x"),
                pl.col("y"),
                (pl.col("x") * pl.col("y")).alias("_xy"),
                (pl.col("x") * pl.col("x")).alias("_xx"),
                (pl.col("y") * pl.col("y")).alias("_yy"),
                pl.lit(1.0).alias("_one"),
            ])
            .drop_nulls()
            .select([
                pl.sum("_xy").alias("sxy"),
                pl.sum("_xx").alias("sxx"),
                pl.sum("_yy").alias("syy"),
                pl.sum("x").alias("sx"),
                pl.sum("y").alias("sy"),
                pl.count().alias("n"),
            ])
            .collect()
        )

        if AG.height == 0:
            return {"ic": float("nan"), "t": float("nan"), "p": float("nan"), "n": 0.0}

        sxy = float(AG["sxy"][0]); sxx = float(AG["sxx"][0]); syy = float(AG["syy"][0])
        sx  = float(AG["sx"][0]);  sy  = float(AG["sy"][0]);  n   = float(AG["n"][0])

        if n < 3:
            return {"ic": float("nan"), "t": float("nan"), "p": float("nan"), "n": n}

        # sample covariance/std
        cov = (sxy - sx * sy / n) / (n - 1.0)
        varx = (sxx - (sx * sx) / n) / (n - 1.0)
        vary = (syy - (sy * sy) / n) / (n - 1.0)
        if varx <= 0.0 or vary <= 0.0:
            return {"ic": float("nan"), "t": float("nan"), "p": float("nan"), "n": n}

        r = cov / (sqrt(varx) * sqrt(vary))
        r = max(-0.999999, min(0.999999, r))

        # t-stat approx for Pearson r
        t = r * sqrt((n - 2.0) / (1.0 - r * r))
        # p-value via Fisher z ~ N(0,1) approx (fast, no scipy)
        z = 0.5 * log((1.0 + r) / (1.0 - r)) * sqrt(max(1.0, n - 3.0))
        # Phi(z)
        Phi = 0.5 * (1.0 + erf(abs(z) / sqrt(2.0)))
        p = 2.0 * (1.0 - Phi)

        return {"ic": r, "t": t, "p": p, "n": n}

    def ic_matrix(self, lags: List[int], horizons: List[int]) -> pd.DataFrame:
        """
        Returns a pandas DataFrame shaped (len(lags), len(horizons))
        with IC values. Rows=lags, Cols=horizons.
        """
        lags = [int(x) for x in lags]
        horizons = [int(h) for h in horizons]
        mat = np.full((len(lags), len(horizons)), np.nan, dtype=float)
        for i, k in enumerate(lags):
            for j, h in enumerate(horizons):
                a = self._ic_agg(k, h)
                mat[i, j] = a["ic"]
        df = pd.DataFrame(mat, index=[f"lag_{k}" for k in lags], columns=[f"H{h}" for h in horizons])
        return df

    def ic_diag_table(self, lags: List[int], horizons: List[int]) -> pd.DataFrame:
        """
        A compact table for a few selected (lag, horizon) pairs.
        """
        rows = []
        for k in lags:
            for h in horizons:
                a = self._ic_agg(k, h)
                rows.append({"Lag": k, "H": h, "IC": a["ic"], "t-stat": a["t"], "p-value": a["p"], "N": a["n"]})
        return pd.DataFrame(rows)

    # ----------------- Accuracy/Errors/R² -----------------

    def summary_table(self) -> pd.DataFrame:
        """
        Accuracy, MAE, MSE, R² computed on (pred, target) aligned without lag/lead.
        """
        base = self._aligned().select(["pred", "target"]).drop_nulls().collect().to_pandas()
        if base.empty:
            return pd.DataFrame({"Metric": [], "Value": []}).set_index("Metric")
        y = base["target"].to_numpy()
        p = base["pred"].to_numpy()
        # naive thresholds for 'accuracy' demo (sign hit-rate)
        acc = np.mean(np.sign(p) == np.sign(y))
        mae = float(np.mean(np.abs(p - y)))
        mse = float(np.mean((p - y) ** 2))
        # R² (time-series)
        ybar = float(np.mean(y))
        ss_res = float(np.sum((y - p) ** 2))
        ss_tot = float(np.sum((y - ybar) ** 2))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else np.nan

        # Information ratio of prediction residual improvements
        # For a simple demo, use IC at (lag=0,h=1) as IR proxy
        ic01 = self._ic_agg(lag=0, horizon=1)["ic"]
        ir = ic01 / (np.std(p - y) + 1e-12)

        tbl = pd.DataFrame(
            {"Metric": ["Accuracy", "MAE", "MSE", "R²", "IC (lag0→H1)", "Information Ratio"],
             "Value": [acc, mae, mse, r2, ic01, ir]}
        ).set_index("Metric")
        return tbl

    # ----------------- Custom figures & tables for dashboard -----------------

    def custom_figures(self, lags: List[int], horizons: List[int]) -> List[CustomFigure]:
        def fig_ic_heatmap():
            df = self.ic_matrix(lags, horizons)
            if df.empty:
                return None
            fig = plt.figure(figsize=(7, 4))
            ax = fig.add_subplot(111)
            im = ax.imshow(df.to_numpy(), aspect="auto", origin="lower")
            ax.set_title("Information Coefficient (IC): lags × horizons")
            ax.set_yticks(np.arange(len(df.index)))
            ax.set_yticklabels(df.index, fontsize=9)
            ax.set_xticks(np.arange(len(df.columns)))
            ax.set_xticklabels(df.columns, fontsize=9)
            fig.colorbar(im, ax=ax, fraction=0.032, pad=0.04)
            return fig

        def fig_ic_vs_lag():
            df = self.ic_matrix(lags, horizons=[1])
            if df.empty:
                return None
            fig = plt.figure(figsize=(7, 3))
            ax = fig.add_subplot(111)
            xs = [int(s.split("_")[1]) for s in df.index]
            ys = df["H1"].to_numpy()
            ax.plot(xs, ys, marker="o")
            ax.set_title("IC vs Lag (H=1)")
            ax.set_xlabel("Lag")
            ax.set_ylabel("IC")
            ax.grid(True, alpha=0.3)
            return fig

        return [
            CustomFigure(key="stats_ic_heatmap", title="IC Heatmap", builder=lambda *_: fig_ic_heatmap(), per_strategy=False),
            CustomFigure(key="stats_ic_vs_lag",  title="IC vs Lag", builder=lambda *_: fig_ic_vs_lag(),  per_strategy=False),
        ]

    def custom_tables(self, lags: List[int], horizons: List[int]) -> List[CustomTable]:
        def tbl_ic_grid(_pdf: pd.DataFrame, _b: Optional[pd.Series]) -> pd.DataFrame:
            return self.ic_matrix(lags, horizons)

        def tbl_diag(_pdf: pd.DataFrame, _b: Optional[pd.Series]) -> pd.DataFrame:
            return self.ic_diag_table(lags, horizons)

        def tbl_summary(_pdf: pd.DataFrame, _b: Optional[pd.Series]) -> pd.DataFrame:
            return self.summary_table()

        return [
            CustomTable(key="stats_summary", title="Statistics — Summary", builder=tbl_summary, controlled=True),
            CustomTable(key="stats_ic_grid", title="IC Matrix", builder=tbl_ic_grid, controlled=True),
            CustomTable(key="stats_ic_diag", title="IC Diagnostics", builder=tbl_diag, controlled=True),
        ]

    # ----------------- Render via your existing tearsheet -----------------

    def build_dashboard(
        self,
        *,
        title: str = "Statistics Dashboard",
        output_dir: str = "output/dash_stats",
        periods_per_year: int = 252,
        lags: List[int] = (0, 1, 5, 10),
        horizons: List[int] = (1, 5, 10),
    ) -> QuantStatsDashboard:
        """
        We reuse QuantStatsDashboard purely as a renderer:
          - Provide trivial returns (zeros) to satisfy the API.
          - figures=[] and tables=[]; we inject custom tables/figures only.
        """
        # Build dummy minimal returns for the left pane to initialize;  (few points, zeros)
        j = self._aligned().select(["date"]).collect()
        if j.height == 0:
            # fallback: a single date
            from datetime import datetime, timedelta
            dates = pl.Series("date", [datetime.now()])
            ret = pl.DataFrame({"date": dates, "stats_dummy": [0.0]}).lazy()
        else:
            ret = j.with_columns(pl.lit(0.0).alias("stats_dummy")).lazy()

        man = DashboardManifest(
            figures=[],  # we will only show custom figs
            tables=[],   # we will only show custom tables
            custom_figures=self.custom_figures(list(lags), list(horizons)),
            custom_tables=self.custom_tables(list(lags), list(horizons)),
        )
        return QuantStatsDashboard(
            returns_df=ret,
            benchmark=None,
            rf=0.0,
            title=title,
            output_dir=output_dir,
            manifest=man,
            periods_per_year=periods_per_year,
        )