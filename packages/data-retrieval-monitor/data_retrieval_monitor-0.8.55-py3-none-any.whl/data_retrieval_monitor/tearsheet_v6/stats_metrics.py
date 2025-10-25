# stats_metrics.py
from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple
import math
import polars as pl

__all__ = [
    "ic_grid",
    "ic_summary_for_table",
    "stats_metrics_for_display",
]

# small eps for numerical guards
_EPS = 1e-12


def _ensure_datetime_ns(lf: pl.LazyFrame, date_col: str = "date") -> pl.LazyFrame:
    return lf.with_columns(pl.col(date_col).cast(pl.Datetime).dt.cast_time_unit("ns"))


def _base_norm(
    pred_target_lf: pl.LazyFrame,
    *,
    date_col: str = "date",
    name_col: str = "name",
    pred_col: str = "pred",
    target_col: str = "y",
) -> pl.LazyFrame:
    """
    Force canonical schema and sortedness:
      ['date'(ns), 'name'(Utf8), 'pred'(f64), 'y'(f64)]
    """
    lf = _ensure_datetime_ns(pred_target_lf, date_col=date_col)
    # ensure required cols exist
    cols = lf.collect_schema().names()
    for c in (date_col, name_col, pred_col, target_col):
        if c not in cols:
            raise ValueError(f"Missing column '{c}' in pred_target_lf.")
    return (
        lf.select([
            pl.col(date_col).alias("date"),
            pl.col(name_col).cast(pl.Utf8).alias("name"),
            pl.col(pred_col).cast(pl.Float64).alias("pred"),
            pl.col(target_col).cast(pl.Float64).alias("y"),
        ])
        .sort(["name", "date"])
    )


def _future_h_mean_expr(y: pl.Expr, h: int) -> pl.Expr:
    """
    Average of future horizons: mean(y_{t+1..t+h}), ignoring nulls.
    Implemented as an average of h lead-shifted series.
    """
    leads = [(y.shift(-k).over("name")) for k in range(1, h + 1)]
    # sum of non-null terms / count of non-null terms
    sums = None
    cnts = None
    for e in leads:
        term = e
        is_valid = term.is_not_null().cast(pl.Float64)
        sums = term.fill_null(0.0) if sums is None else (sums + term.fill_null(0.0))
        cnts = is_valid if cnts is None else (cnts + is_valid)
    return pl.when(cnts > 0.0).then(sums / cnts).otherwise(None)


def _corr_t_r2_group_agg(x: pl.Expr, y: pl.Expr) -> List[pl.Expr]:
    """
    Build aggregations required to compute corr/t/R2 with one group_by.
    We only aggregate over valid (non-null) pairs.
    """
    valid = x.is_not_null() & y.is_not_null()
    xm = pl.when(valid).then(x).otherwise(None)
    ym = pl.when(valid).then(y).otherwise(None)

    # sums ignore nulls
    Sx  = xm.sum().alias("_Sx")
    Sy  = ym.sum().alias("_Sy")
    Sxx = (xm * xm).sum().alias("_Sxx")
    Syy = (ym * ym).sum().alias("_Syy")
    Sxy = (xm * ym).sum().alias("_Sxy")
    N   = xm.count().alias("_N")

    return [Sx, Sy, Sxx, Syy, Sxy, N]


def _finish_corr_t_r2() -> List[pl.Expr]:
    """
    Turn the aggregated sums into IC (corr), t-stat and R^2.
    """
    N   = pl.col("_N").cast(pl.Float64)
    Sx  = pl.col("_Sx")
    Sy  = pl.col("_Sy")
    Sxx = pl.col("_Sxx")
    Syy = pl.col("_Syy")
    Sxy = pl.col("_Sxy")

    # Pearson correlation
    num = N * Sxy - Sx * Sy
    den = ((N * Sxx - Sx * Sx) * (N * Syy - Sy * Sy)).sqrt()
    corr = pl.when((den.abs() > _EPS) & (N > 2)).then(num / den).otherwise(None).alias("IC")

    # t-stat for correlation
    one = pl.lit(1.0)
    tval = pl.when((N > 2) & corr.is_not_null() & (corr.abs() < 1.0 - 1e-15)) \
             .then(corr * ((N - 2.0) / (one - corr * corr)).sqrt()) \
             .otherwise(None) \
             .alias("t")

    r2 = (corr * corr).alias("R2")

    return [corr, tval, r2, pl.col("_N").cast(pl.Int64).alias("N")]


def ic_grid(
    pred_target_lf: pl.LazyFrame,
    *,
    lags: Sequence[int] = tuple(range(0, 6)),
    horizons: Sequence[int] = (1, 5, 10, 20),
    date_col: str = "date",
    name_col: str = "name",
    pred_col: str = "pred",
    target_col: str = "y",
) -> pl.LazyFrame:
    """
    Compute IC / t-stat / R² for every (lag, horizon) combo, per 'name'.

    Returns LazyFrame columns:
      ['name','lag','horizon','IC','t','R2','N']
    """
    base = _base_norm(pred_target_lf, date_col=date_col, name_col=name_col, pred_col=pred_col, target_col=target_col)

    parts: List[pl.LazyFrame] = []
    for lag in lags:
        # x = pred lagged by 'lag'
        x = pl.col("pred").shift(lag).over("name")
        for h in horizons:
            y = _future_h_mean_expr(pl.col("y"), int(h))
            agg = (
                base.with_columns([x.alias("_x"), y.alias("_y")])
                    .group_by("name")
                    .agg(_corr_t_r2_group_agg(pl.col("_x"), pl.col("_y")))
                    .with_columns(_finish_corr_t_r2())
                    .select([
                        pl.col("name"),
                        pl.lit(int(lag)).alias("lag"),
                        pl.lit(int(h)).alias("horizon"),
                        pl.col("IC"),
                        pl.col("t"),
                        pl.col("R2"),
                        pl.col("N"),
                    ])
            )
            parts.append(agg)

    return pl.concat(parts) if parts else base.select([
        pl.col("name"),
        pl.lit(0).alias("lag"),
        pl.lit(1).alias("horizon"),
        pl.lit(None).cast(pl.Float64).alias("IC"),
        pl.lit(None).cast(pl.Float64).alias("t"),
        pl.lit(None).cast(pl.Float64).alias("R2"),
        pl.lit(0).cast(pl.Int64).alias("N"),
    ])


def ic_summary_for_table(ic_long: pl.LazyFrame) -> pl.LazyFrame:
    """
    Produce a compact summary per 'name' from the long IC grid:
      ['name','IC(avg)','IC(max|abs)','t(|max|)','R2(avg)','N(total)']
    """
    return (
        ic_long
        .group_by("name")
        .agg([
            pl.col("IC").mean().alias("IC_avg"),
            pl.col("IC").abs().max().alias("IC_abs_max"),
            pl.col("t").abs().max().alias("t_abs_max"),
            pl.col("R2").mean().alias("R2_avg"),
            pl.col("N").sum().alias("N_total"),
        ])
        .select(["name", "IC_avg", "IC_abs_max", "t_abs_max", "R2_avg", "N_total"])
    )


def stats_metrics_for_display(
    pred_target_lf: pl.LazyFrame,
    *,
    lags: Sequence[int],
    horizons: Sequence[int],
    date_col: str = "date",
    name_col: str = "name",
    pred_col: str = "pred",
    target_col: str = "y",
) -> Tuple[pl.DataFrame, pl.DataFrame]:
    """
    Convenience:
      - compute ic_grid()
      - compute ic_summary_for_table()
      - return both as eager Polars DataFrames (render-only)
    """
    ic_long = ic_grid(
        pred_target_lf,
        lags=lags,
        horizons=horizons,
        date_col=date_col,
        name_col=name_col,
        pred_col=pred_col,
        target_col=target_col,
    )
    ic_df = ic_long.collect()
    summary_df = ic_summary_for_table(ic_long).collect()
    return ic_df, summary_df