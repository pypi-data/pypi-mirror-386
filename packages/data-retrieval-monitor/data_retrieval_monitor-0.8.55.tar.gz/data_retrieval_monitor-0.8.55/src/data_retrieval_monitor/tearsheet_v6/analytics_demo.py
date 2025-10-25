# analytics_demo.py
from __future__ import annotations

import numpy as np
import polars as pl
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

from analytics_base import AnalyticsConfig, BacktestAnalytics, StatAnalytics
from dashboard import QuantStatsDashboard, DashboardManifest, CustomTable, CustomFigure


# ---------------------------
# 0) Synthetic data (fast; Polars-lazy compute)
# ---------------------------
np.random.seed(123)

# Dates
n_days = 260
start = datetime(2022, 1, 3)
end = start + timedelta(days=n_days - 1)
# NOTE: Older Polars may return Date here (not Datetime) for daily ranges.
dates = pl.date_range(start=start, end=end, interval="1d", eager=True)

# Strategy returns (wide)
alpha_ret = 0.0004 + 0.01 * np.random.randn(n_days)
beta_ret  = 0.0002 + 0.012 * np.random.randn(n_days)
bench_ret = 0.0003 + 0.009 * np.random.randn(n_days)

returns_wide = pl.DataFrame({
    "date": dates,            # may be pl.Date; we'll cast in analytics/dashboard
    "Alpha": alpha_ret,
    "Beta":  beta_ret,
}).lazy()

benchmark_wide = pl.DataFrame({
    "date": dates,            # may be pl.Date; we'll cast in analytics/dashboard
    "Benchmark": bench_ret,
}).lazy()

# Per-strategy weights over 3 assets; used for turnover
assets = ["A", "B", "C"]
names = ["Alpha", "Beta"]
rows = []
# NOTE: 'dates' may iterate as python date objects; use schema=pl.Date for safe construction.
for d in dates:
    for nm in names:
        w = np.random.dirichlet(alpha=[2.0, 2.0, 2.0])
        for a, wi in zip(assets, w):
            rows.append((d, nm, a, float(wi)))

weights_long = (
    pl.DataFrame(
        rows,
        schema=[("date", pl.Date), ("name", pl.Utf8), ("asset", pl.Utf8), ("weight", pl.Float64)],
        orient="row",  # avoid DataOrientationWarning and infer issues
    ).lazy()
)

# Predictions/targets for StatAnalytics (5 assets per day)
ids = ["X1", "X2", "X3", "X4", "X5"]
pred_rows, targ_rows = [], []
for d in dates:
    pred = np.random.randn(len(ids))
    target = 0.4 * pred + 0.6 * np.random.randn(len(ids))  # correlated with preds (rho≈0.4)
    for j, idv in enumerate(ids):
        pred_rows.append((d, idv, float(pred[j])))
        targ_rows.append((d, idv, float(target[j])))

preds_lf = pl.DataFrame(
    pred_rows,
    schema=[("date", pl.Date), ("id", pl.Utf8), ("pred", pl.Float64)],
    orient="row",
).lazy()

targets_lf = pl.DataFrame(
    targ_rows,
    schema=[("date", pl.Date), ("id", pl.Utf8), ("target", pl.Float64)],
    orient="row",
).lazy()


# ---------------------------
# 1) Instantiate analytics
# ---------------------------
cfg = AnalyticsConfig(date_col="date", name_col="name")

bt = BacktestAnalytics(returns_wide_lf=returns_wide, weights_long_lf=weights_long, cfg=cfg)
st = StatAnalytics(preds_lf=preds_lf, targets_lf=targets_lf, cfg=cfg)


# ---------------------------
# 2) Custom TABLES (compute in Polars, convert to pandas to render)
# ---------------------------
def tbl_backtest_metrics(_pdf, _bser):
    sh = bt.sharpe(periods_per_year=252).collect().to_pandas()
    to = bt.turnover().collect().to_pandas()
    out = sh.merge(to, on="name", how="outer").set_index("name").T
    out.index.name = "Backtest"
    return out

def tbl_stats_summary(_pdf, _bser):
    ic = st.ic_summary().collect().to_pandas().iloc[0].to_dict()
    r2 = st.r2_pooled().collect().to_pandas().iloc[0].to_dict()
    return (
        pl.DataFrame(
            {"Metric": ["IC_mean", "IC_sd", "IC_t", "R2"],
             "Value": [ic.get("IC_mean"), ic.get("IC_sd"), ic.get("IC_t"), r2.get("R2")]}
        ).to_pandas().set_index("Metric")
    )


# ---------------------------
# 3) Custom FIGURES (return matplotlib Figure; compute stays in Polars)
# ---------------------------
def fig_ic_hist(_pdf, _bser):
    ic_vals = st.ic_daily().collect().to_pandas()["ic"].dropna().values
    fig = plt.figure(figsize=(6, 3))
    ax = fig.gca()
    ax.hist(ic_vals, bins=30)
    ax.set_title("Daily IC (cross-sectional) — Histogram")
    ax.set_xlabel("IC")
    ax.set_ylabel("Frequency")
    ax.grid(True, alpha=0.3)
    return fig

def fig_turnover_bar(_pdf, _bser):
    tdf = bt.turnover().collect().to_pandas()
    fig = plt.figure(figsize=(5, 3))
    ax = fig.gca()
    ax.bar(tdf["name"], tdf["turnover"])
    ax.set_title("Average Turnover")
    ax.set_ylabel("Turnover")
    ax.grid(True, axis="y", alpha=0.3)
    return fig


# ---------------------------
# 4) Build Dashboard (reuse your tearsheet)
# ---------------------------
if __name__ == "__main__":
    manifest = DashboardManifest(
        figures=["snapshot", "returns", "monthly_heatmap"],
        tables=["metrics", "eoy", "drawdown_details"],
        custom_tables=[
            CustomTable(key="bt_metrics", title="Backtest — Core Metrics", builder=tbl_backtest_metrics, controlled=True),
            CustomTable(key="stat_summary", title="Statistics — IC & R²", builder=tbl_stats_summary, controlled=True),
        ],
        custom_figures=[
            CustomFigure(key="ic_hist", title="IC Histogram", builder=fig_ic_hist, per_strategy=False),
            CustomFigure(key="turnover_bar", title="Turnover", builder=fig_turnover_bar, per_strategy=False),
        ],
    )

    dash = QuantStatsDashboard(
        returns_df=returns_wide,   # Polars LazyFrame (OK)
        benchmark=benchmark_wide,  # Polars LazyFrame (OK)
        rf=0.0,
        manifest=manifest,
        periods_per_year=252,
        title="Analytics Demo — Integrated Tearsheet",
        output_dir="output/analytics_demo",
    )

    print(dash.html_path)