# analytics_demo_tabs.py
from __future__ import annotations

import os
from typing import Tuple, List

import numpy as np
import pandas as pd
import polars as pl

from dashboard import QuantStatsDashboard, DashboardManifest
from prediction_dashboard import PredictionDashboard, PredictionManifest
from multi_dashboard import TabSpec, TabbedDashboard


# ---------------------------
# Synthetic data builders
# ---------------------------

def make_synthetic_backtest(
    n: int = 750, seed: int = 42
) -> Tuple[pl.LazyFrame, pl.LazyFrame]:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n, freq="B")

    bench = rng.normal(loc=0.0001, scale=0.01, size=n)
    a = bench + rng.normal(0.00025, 0.008, n)
    b = 0.6 * bench + rng.normal(0.00005, 0.012, n)

    ret_df = pd.DataFrame({"date": dates, "strat_A": a, "strat_B": b})
    bench_df = pd.DataFrame({"date": dates, "Benchmark": bench})

    returns_lf = pl.from_pandas(ret_df).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
    bench_lf = pl.from_pandas(bench_df).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
    return returns_lf, bench_lf


def make_synthetic_prediction(
    n: int = 750, seed: int = 123, factors: List[str] = ("factor1", "factor2")
) -> Tuple[pl.LazyFrame, pl.LazyFrame]:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n, freq="B")

    true = rng.normal(0.0, 1.0, n).cumsum()
    base_ret = rng.normal(0.0, 0.01, n)

    preds, targs = {}, {}
    for i, f in enumerate(factors):
        p = (true + rng.normal(0, 0.5 + 0.1 * i, n))
        y = base_ret + 0.002 * p + rng.normal(0, 0.01 + 0.002 * i, n)
        preds[f] = p
        targs[f] = y

    preds_df = pd.DataFrame({"date": dates, **preds})
    targs_df = pd.DataFrame({"date": dates, **targs})

    preds_lf = pl.from_pandas(preds_df).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
    targs_lf = pl.from_pandas(targs_df).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
    return preds_lf, targs_lf


# ---------------------------
# Main
# ---------------------------

def main() -> None:
    outdir = "output/demo_tabs"
    os.makedirs(outdir, exist_ok=True)

    # --- Backtest tab ---
    returns_lf, bench_lf = make_synthetic_backtest()

    backtest_dash = QuantStatsDashboard(
        returns_df=returns_lf,
        benchmark=bench_lf,
        rf=0.0,
        manifest=DashboardManifest(
            figures=["snapshot","returns","monthly_heatmap","rolling_volatility","drawdown"],
            tables=["metrics","eoy","monthly","drawdown_top10"],
        ),
        periods_per_year=252,
        title="Backtest",
        output_dir=os.path.join(outdir, "backtest"),
    )

    # --- Prediction tab ---
    pred_lf, targs_lf = make_synthetic_prediction(factors=["factor1", "factor2"])

    pred_dash = PredictionDashboard(
    preds_lf=pred_lf,
    target_lf=targs_lf,
    title="Prediction",
    output_dir="output/demo_tabs/prediction",
    manifest=PredictionManifest(
        factors=["factor1", "factor2"],
        lags=[0,1,5,10],
        horizons=[1,5,20],
        summary_lag=1,          # <- now supported
        summary_horizon=5       # <- now supported
    ),
)

    # --- Tabbed container ---
    TabbedDashboard(
        tabs=[
            TabSpec(title="Backtest", file_path=backtest_dash.html_path),
            TabSpec(title="Prediction", file_path=pred_dash.html_path),
        ],
        title="Demo Tabs",
        output_dir=outdir,
    )


if __name__ == "__main__":
    main()