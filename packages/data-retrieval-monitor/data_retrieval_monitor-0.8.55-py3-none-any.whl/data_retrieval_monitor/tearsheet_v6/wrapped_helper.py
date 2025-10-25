from __future__ import annotations

"""Utility helpers for producing wrapped dashboards (backtest + prediction)."""

import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl

from dashboard import (
    CustomFigureSpec as BTCustomFigure,
    CustomTableSpec as BTCustomTable,
    DashboardManifest,
    QuantStatsDashboard,
)
from prediction_dashboard import (
    CustomFigureSpec as PRCustomFigure,
    CustomTableSpec as PRCustomTable,
    PredictionDashboard,
    PredictionManifest,
)
from multi_dashboard import TabSpec, TabbedDashboard


@dataclass
class BacktestData:
    tracking_pnl: pl.LazyFrame
    benchmark: pl.LazyFrame
    active_tracking_pnl: pl.LazyFrame


@dataclass
class PredictionData:
    preds_lf: pl.LazyFrame
    target_lf: pl.LazyFrame
    residuals_lf: pl.LazyFrame


# -----------------------------------------------------------------------------
# Synthetic demo generators
# -----------------------------------------------------------------------------
def make_backtest_bundle(n: int = 500, seed: int = 42) -> BacktestData:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n, freq="B")

    bench = rng.normal(0.0002, 0.01, size=n)
    strat = bench + rng.normal(0.0003, 0.008, size=n)

    tracking = pl.from_pandas(pd.DataFrame({"date": dates, "Strategy": strat})).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
    benchmark = pl.from_pandas(pd.DataFrame({"date": dates, "Benchmark": bench})).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
    active = pl.from_pandas(pd.DataFrame({"date": dates, "Active": strat - bench})).with_columns(pl.col("date").cast(pl.Datetime)).lazy()

    return BacktestData(tracking_pnl=tracking, benchmark=benchmark, active_tracking_pnl=active)


def make_prediction_bundle(
    n: int = 500,
    seed: int = 7,
    factors: List[str] = ("Value", "Momentum"),
) -> PredictionData:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n, freq="B")

    preds_dict: Dict[str, Any] = {"date": dates}
    target_dict: Dict[str, Any] = {"date": dates}
    residual_dict: Dict[str, Any] = {"date": dates}

    for i, factor in enumerate(factors):
        baseline = rng.normal(0, 1.0 + 0.2 * i, size=n).cumsum()
        pred = baseline + rng.normal(0, 0.4 + 0.1 * i, size=n)
        target = 0.003 * pred + rng.normal(0, 0.01 + 0.003 * i, size=n)

        preds_dict[factor] = pred
        target_dict[factor] = target
        residual_dict[factor] = target - pred

    preds = pl.from_pandas(pd.DataFrame(preds_dict)).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
    targets = pl.from_pandas(pd.DataFrame(target_dict)).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
    residuals = pl.from_pandas(pd.DataFrame(residual_dict)).with_columns(pl.col("date").cast(pl.Datetime)).lazy()

    return PredictionData(preds_lf=preds, target_lf=targets, residuals_lf=residuals)


# -----------------------------------------------------------------------------
# Helpers for coercing user-provided bundles
# -----------------------------------------------------------------------------
def _ensure_lazy(frame: Any) -> pl.LazyFrame:
    if isinstance(frame, pl.LazyFrame):
        return frame
    if isinstance(frame, pl.DataFrame):
        return frame.lazy()
    if isinstance(frame, pd.DataFrame):
        return pl.from_pandas(frame).lazy()
    raise TypeError("Expected Polars LazyFrame/DataFrame or pandas DataFrame.")


def _coerce_backtest_bundle(bundle: Any) -> BacktestData:
    if isinstance(bundle, BacktestData):
        return bundle

    if isinstance(bundle, dict):
        tracking = bundle.get("tracking_pnl")
        benchmark = bundle.get("benchmark")
        active = bundle.get("active_tracking_pnl")
    else:
        tracking = getattr(bundle, "tracking_pnl", None)
        benchmark = getattr(bundle, "benchmark", None)
        active = getattr(bundle, "active_tracking_pnl", None)

    if tracking is None or benchmark is None:
        raise ValueError("backtest bundle requires 'tracking_pnl' and 'benchmark'.")

    tracking_lazy = _ensure_lazy(tracking)
    benchmark_lazy = _ensure_lazy(benchmark)

    if active is None:
        tracking_pd = tracking_lazy.collect().to_pandas()
        benchmark_pd = benchmark_lazy.collect().to_pandas()
        bench_cols = [c for c in benchmark_pd.columns if c != "date"]
        if not bench_cols:
            raise ValueError("benchmark must contain at least one non-date column.")
        bench_series = benchmark_pd[bench_cols[0]]
        active_dict = {"date": tracking_pd["date"]}
        for col in tracking_pd.columns:
            if col == "date":
                continue
            active_dict[f"{col} Active"] = tracking_pd[col] - bench_series
        active_lazy = pl.from_pandas(pd.DataFrame(active_dict)).lazy()
    else:
        active_lazy = _ensure_lazy(active)

    return BacktestData(
        tracking_pnl=tracking_lazy,
        benchmark=benchmark_lazy,
        active_tracking_pnl=active_lazy,
    )


def _coerce_prediction_bundle(bundle: Any) -> PredictionData:
    if isinstance(bundle, PredictionData):
        return bundle

    if isinstance(bundle, dict):
        preds = bundle.get("preds_lf")
        target = bundle.get("target_lf")
        residuals = bundle.get("residuals_lf")
    else:
        preds = getattr(bundle, "preds_lf", None)
        target = getattr(bundle, "target_lf", None)
        residuals = getattr(bundle, "residuals_lf", None)

    if preds is None or target is None:
        raise ValueError("prediction bundle requires 'preds_lf' and 'target_lf'.")

    preds_lazy = _ensure_lazy(preds)
    target_lazy = _ensure_lazy(target)

    if residuals is None:
        preds_pd = preds_lazy.collect().to_pandas()
        target_pd = target_lazy.collect().to_pandas()
        residual_pd = target_pd.copy()
        for col in residual_pd.columns:
            if col == "date":
                continue
            residual_pd[col] = residual_pd[col] - preds_pd[col]
        residual_lazy = pl.from_pandas(residual_pd).lazy()
    else:
        residual_lazy = _ensure_lazy(residuals)

    return PredictionData(preds_lf=preds_lazy, target_lf=target_lazy, residuals_lf=residual_lazy)


# -----------------------------------------------------------------------------
# Default custom builders
# -----------------------------------------------------------------------------
def _active_cumulative(active_lf: pl.LazyFrame, *_):
    df = active_lf.collect().to_pandas().set_index("date")
    if df.empty:
        return None
    fig, ax = plt.subplots(figsize=(5, 2.4))
    df.iloc[:, 0].cumsum().plot(ax=ax, lw=1.4, color="#2E7D32")
    ax.set_title("Cumulative Active Return")
    ax.set_ylabel("Active Return")
    ax.grid(alpha=0.25)
    return {"label": "Active", "figure": fig, "prefix": "active"}


def _active_summary(active_lf: pl.LazyFrame, *_):
    df = active_lf.collect().to_pandas()
    if df.empty:
        return ""
    series = df.iloc[:, 1] if df.columns[0] == "date" else df.iloc[:, 0]
    stats = series.agg(["mean", "std", "median"]).to_frame(name="Active")
    stats = stats.mul(10000).round(2)
    stats = stats.reset_index().rename(columns={"index": "Metric"})
    return stats.to_html(border=0, escape=False, index=False)


def _residual_histograms(residual_lf: pl.LazyFrame, *_):
    df = residual_lf.collect().to_pandas().set_index("date")
    if df.empty:
        return None
    tiles = []
    for col in df.columns:
        fig, ax = plt.subplots(figsize=(4.2, 2.4))
        ax.hist(df[col].dropna(), bins=40, color="#3949AB", alpha=0.75)
        ax.set_title(f"Residual Distribution — {col}")
        ax.axvline(df[col].mean(), color="#F44336", lw=1.0, linestyle="--")
        ax.set_xlabel("Residual")
        ax.set_ylabel("Frequency")
        ax.grid(alpha=0.2)
        tiles.append({"label": col, "figure": fig, "prefix": f"resid_{col.lower()}", "column": col})
    return tiles


def _residual_summary(residual_lf: pl.LazyFrame, *_):
    df = residual_lf.collect().to_pandas()
    if df.empty:
        return ""
    summary = pd.DataFrame(
        {
            "Mean": df.mean(),
            "Std Dev": df.std(),
            "Skew": df.skew(),
            "Kurtosis": df.kurtosis(),
        }
    ).round(3)
    summary = summary.reset_index().rename(columns={"index": "Factor"})
    return summary.to_html(border=0, escape=False, index=False)


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------
def build_dashboards(
    *,
    backtest_bundle: BacktestData | dict | object,
    prediction_bundle: PredictionData | dict | object,
    backtest_figures: Optional[List[str]] = None,
    backtest_tables: Optional[List[str]] = None,
    prediction_figures: Optional[List[str]] = None,
    prediction_tables: Optional[List[str]] = None,
    custom_backtest_figures: Optional[List[Callable]] = None,
    custom_backtest_tables: Optional[List[Callable]] = None,
    custom_prediction_figures: Optional[List[Callable]] = None,
    custom_prediction_tables: Optional[List[Callable]] = None,
    output_dir: str = "output/demo_wrapped",
) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)

    backtest_data = _coerce_backtest_bundle(backtest_bundle)
    prediction_data = _coerce_prediction_bundle(prediction_bundle)

    bt_manifest = DashboardManifest(
        figures=backtest_figures or ["returns", "drawdown"],
        tables=backtest_tables or ["metrics", "monthly"],
        data_overrides={
            "returns": "tracking_pnl",
            "benchmark": "benchmark",
            "active_tracking_pnl": "active_tracking_pnl",
        },
        custom_figures=(
            [
                BTCustomFigure(
                    key="active_cumulative",
                    data_key="active_tracking_pnl",
                    builder=_active_cumulative,
                    title="Active Contribution",
                    output_prefix="active",
                )
            ]
            if not custom_backtest_figures
            else [
                BTCustomFigure(
                    key=f.__name__,
                    data_key="returns",
                    builder=f,
                    title=f.__name__.replace("_", " ").title(),
                )
                for f in custom_backtest_figures
            ]
        ),
        custom_tables=(
            [
                BTCustomTable(
                    key="active_summary",
                    data_key="active_tracking_pnl",
                    builder=_active_summary,
                    title="Active Summary (bp)",
                    controlled=True,
                )
            ]
            if not custom_backtest_tables
            else [
                BTCustomTable(
                    key=f.__name__,
                    data_key="active_tracking_pnl",
                    builder=f,
                    title=f.__name__.replace("_", " ").title(),
                )
                for f in custom_backtest_tables
            ]
        ),
    )

    bt_dash = QuantStatsDashboard(
        returns_df=None,
        benchmark=None,
        rf=0.0,
        manifest=bt_manifest,
        title="Strategy Backtest",
        output_dir=os.path.join(output_dir, "backtest"),
        data_source=backtest_data,
    )

    prediction_manifest = PredictionManifest(
        factors=[c for c in prediction_data.preds_lf.collect_schema().names() if c != "date"],
        lags=[0, 1, 5, 10],
        horizons=[1, 5, 20],
        summary_lag=1,
        summary_horizon=5,
        data_overrides={
            "preds": "preds_lf",
            "target": "target_lf",
            "residuals": "residuals_lf",
        },
        custom_figures=(
            [
                PRCustomFigure(
                    key="residual_histograms",
                    data_key="residuals",
                    builder=_residual_histograms,
                    title="Residual Diagnostics",
                    output_prefix="resid",
                )
            ]
            if not custom_prediction_figures
            else [
                PRCustomFigure(
                    key=f.__name__,
                    data_key="residuals",
                    builder=f,
                    title=f.__name__.replace("_", " ").title(),
                )
                for f in custom_prediction_figures
            ]
        ),
        custom_tables=(
            [
                PRCustomTable(
                    key="residual_summary",
                    data_key="residuals",
                    builder=_residual_summary,
                    title="Residual Summary",
                    controlled=True,
                )
            ]
            if not custom_prediction_tables
            else [
                PRCustomTable(
                    key=f.__name__,
                    data_key="residuals",
                    builder=f,
                    title=f.__name__.replace("_", " ").title(),
                )
                for f in custom_prediction_tables
            ]
        ),
    )

    pr_dash = PredictionDashboard(
        preds_lf=None,
        target_lf=None,
        manifest=prediction_manifest,
        title="Prediction Diagnostics",
        output_dir=os.path.join(output_dir, "prediction"),
        data_source=prediction_data,
    )

    index_path = TabbedDashboard(
        tabs=[
            TabSpec(title="Backtest", file_path=bt_dash.html_path),
            TabSpec(title="Prediction", file_path=pr_dash.html_path),
        ],
        title="Wrapped Dashboards",
        output_dir=output_dir,
    ).html_path

    return {
        "backtest": bt_dash.html_path,
        "prediction": pr_dash.html_path,
        "index": index_path,
    }
