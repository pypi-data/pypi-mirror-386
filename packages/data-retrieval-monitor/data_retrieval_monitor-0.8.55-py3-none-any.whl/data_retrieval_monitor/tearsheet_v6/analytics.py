# analytics.py
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Iterable, List, Dict, Union, Sequence

import numpy as np
import polars as pl

# plotting (render-time only; no compute)
import pandas as pd
import matplotlib.pyplot as plt


__all__ = [
    "AnalyticsBase",
    "Backtest",
    "Statistics",
]


# =========================
# Shared helpers (lazy-only)
# =========================

@dataclass
class Context:
    ppy: int = 252          # periods per year
    rf: float = 0.0         # scalar RF (annual, decimal), only used if caller applies it
    capital0: float = 1_000_000.0


def _as_lazy(x: Union[pl.DataFrame, pl.LazyFrame]) -> pl.LazyFrame:
    return x.lazy() if isinstance(x, pl.DataFrame) else x


def _ensure_datetime_ns(lf: pl.LazyFrame, date_col: str) -> pl.LazyFrame:
    return lf.with_columns(pl.col(date_col).cast(pl.Datetime).dt.cast_time_unit("ns"))


def _schema_names(lf: pl.LazyFrame) -> List[str]:
    return lf.collect_schema().names()


def _detect_series_cols(names: Sequence[str], date_col: str) -> List[str]:
    return [c for c in names if c != date_col]


def _melt_wide(
    lf: pl.LazyFrame,
    *,
    date_col: str,
    name_col: str,
    value_name: str,
) -> pl.LazyFrame:
    """
    Wide -> long with standardized [date_col, name_col, value_name].
    """
    cols = _schema_names(lf)
    if name_col in cols and value_name in cols:
        # already long-ish
        return lf
    value_cols = _detect_series_cols(cols, date_col)
    if not value_cols:
        # return empty long
        return lf.select([pl.col(date_col)]).with_columns(pl.lit(None).alias(name_col), pl.lit(None).alias(value_name)).filter(pl.lit(False))
    return (
        lf.melt(id_vars=[date_col], value_vars=value_cols, variable_name=name_col, value_name=value_name)
          .with_columns(pl.col(value_name).cast(pl.Float64))
    )


def _pivot_to_wide(
    long_lf: pl.LazyFrame,
    *,
    index: str,
    columns: str,
    values: str,
) -> pl.LazyFrame:
    # Polars pivot is eager-only; to keep pipeline lazy-friendly, we allow caller to collect as needed.
    return long_lf.pivot(index=index, columns=columns, values=values)  # type: ignore[attr-defined]


def _per_step_rf_scalar(annual_rf: float, ppy: int) -> float:
    return (1.0 + float(annual_rf)) ** (1.0 / float(ppy)) - 1.0


# =========================
# Base class
# =========================

class AnalyticsBase:
    """
    Base analytics container:
      - Holds context (ppy, rf, capital0)
      - Normalizes/standardizes data lazily (date/name/value columns)
      - Provides namespaced accessors: `.metrics` and `.plot`
    """

    def __init__(
        self,
        *,
        date_col: str = "date",
        name_col: str = "name",
        ctx: Optional[Context] = None,
    ) -> None:
        self.date_col = date_col
        self.name_col = name_col
        self.ctx = ctx or Context()

        # attach namespaces (bound to this instance)
        self.metrics = self.Metrics(self)
        self.plot = self.Plots(self)

    # ---------- hooks to be implemented by children ----------
    class Metrics:
        def __init__(self, parent: "AnalyticsBase") -> None:
            self._p = parent

    class Plots:
        def __init__(self, parent: "AnalyticsBase") -> None:
            self._p = parent

    # ---------- shared helper utilities ----------
    def _ensure_lazy(self, lf: Union[pl.DataFrame, pl.LazyFrame]) -> pl.LazyFrame:
        return _ensure_datetime_ns(_as_lazy(lf), self.date_col)

    def _melt(self, lf: pl.LazyFrame, value_name: str) -> pl.LazyFrame:
        return _melt_wide(lf, date_col=self.date_col, name_col=self.name_col, value_name=value_name)

    # plotting-time converter (no compute logic here)
    @staticmethod
    def _to_pd_series(two_col_df: pl.DataFrame, *, date_col: str, val_col: str, name: Optional[str] = None) -> pd.Series:
        pdf = two_col_df.select([pl.col(date_col), pl.col(val_col)]).to_pandas()
        dt = pd.to_datetime(pdf[date_col], utc=False)
        s = pd.Series(pdf[val_col].to_numpy(), index=pd.DatetimeIndex(dt).tz_localize(None))
        s.name = name or val_col
        return s


# =========================
# Backtest analytics
# =========================

class Backtest(AnalyticsBase):
    """
    Analytics over strategy returns/weights/benchmark.
    All computations are Polars-lazy; plotting converts to pandas for rendering only.
    """

    def __init__(
        self,
        *,
        returns: Union[pl.DataFrame, pl.LazyFrame],     # wide: [date, strat...]
        benchmark: Optional[Union[pl.DataFrame, pl.LazyFrame]] = None,  # wide: [date, bench]
        weights: Optional[Union[pl.DataFrame, pl.LazyFrame]] = None,    # wide: [date, strat...]
        pnl: Optional[Union[pl.DataFrame, pl.LazyFrame]] = None,        # wide (optional): [date, strat...]
        returns_value_name: str = "ret",
        weights_value_name: str = "w",
        pnl_value_name: str = "pnl",
        date_col: str = "date",
        name_col: str = "name",
        ctx: Optional[Context] = None,
    ) -> None:
        super().__init__(date_col=date_col, name_col=name_col, ctx=ctx)

        self._returns_wide = self._ensure_lazy(returns)
        self._benchmark_wide = self._ensure_lazy(benchmark) if benchmark is not None else None
        self._weights_wide = self._ensure_lazy(weights) if weights is not None else None
        self._pnl_wide = self._ensure_lazy(pnl) if pnl is not None else None

        self._ret_name = returns_value_name
        self._w_name = weights_value_name
        self._pnl_name = pnl_value_name

    # -------- long views (standardized names) --------
    @property
    def returns_long(self) -> pl.LazyFrame:
        return self._melt(self._returns_wide, self._ret_name)

    @property
    def weights_long(self) -> Optional[pl.LazyFrame]:
        if self._weights_wide is None:
            return None
        return self._melt(self._weights_wide, self._w_name)

    @property
    def pnl_long(self) -> Optional[pl.LazyFrame]:
        if self._pnl_wide is None:
            return None
        return self._melt(self._pnl_wide, self._pnl_name)

    @property
    def benchmark_series(self) -> Optional[pl.LazyFrame]:
        if self._benchmark_wide is None:
            return None
        # discover the first non-date column as 'b'
        names = _schema_names(self._benchmark_wide)
        bcols = [c for c in names if c != self.date_col]
        if not bcols:
            return None
        bname = bcols[0]
        return self._ensure_lazy(self._benchmark_wide.select([pl.col(self.date_col), pl.col(bname).alias("b")]))

    # -------- metrics namespace --------
    class Metrics(AnalyticsBase.Metrics):
        # --- basic return metrics ---
        def comp(self) -> pl.LazyFrame:
            p = self._p
            r = pl.col(p._ret_name)
            return (
                p.returns_long
                .group_by(p.name_col)
                .agg(((1.0 + r).product() - 1.0).alias("comp"))
                .select([pl.col(p.name_col).alias("name"), pl.col("comp")])
            )

        def cagr(self) -> pl.LazyFrame:
            p = self._p
            r = pl.col(p._ret_name)
            n = pl.count()
            ppy = p.ctx.ppy
            g = (
                p.returns_long
                .group_by(p.name_col)
                .agg([
                    ((1.0 + r).product() - 1.0).alias("_comp"),
                    n.alias("_n"),
                ])
                .with_columns(((1.0 + pl.col("_comp")) ** (pl.lit(ppy) / pl.col("_n")) - 1.0).alias("cagr"))
                .select([pl.col(p.name_col).alias("name"), pl.col("cagr")])
            )
            return g

        def vol_ann(self) -> pl.LazyFrame:
            p = self._p
            r = pl.col(p._ret_name)
            return (
                p.returns_long
                .group_by(p.name_col)
                .agg(r.std(ddof=1).alias("_sd"))
                .with_columns((pl.col("_sd") * math.sqrt(p.ctx.ppy)).alias("vol_ann"))
                .select([pl.col(p.name_col).alias("name"), pl.col("vol_ann")])
            )

        def sharpe(self, *, rf_scalar_annual: Optional[float] = None) -> pl.LazyFrame:
            """
            Sharpe using (ret - rf/ppy). If rf_scalar_annual not provided, uses p.ctx.rf.
            """
            p = self._p
            r = pl.col(p._ret_name)
            rf_annual = p.ctx.rf if rf_scalar_annual is None else rf_scalar_annual
            per = _per_step_rf_scalar(rf_annual, p.ctx.ppy)
            return (
                p.returns_long
                .with_columns((r - per).alias("_er"))
                .group_by(p.name_col)
                .agg([
                    pl.col("_er").mean().alias("_mu"),
                    pl.col("_er").std(ddof=1).alias("_sd"),
                ])
                .with_columns(
                    pl.when(pl.col("_sd") == 0)
                     .then(pl.lit(float("nan")))
                     .otherwise(pl.col("_mu") / pl.col("_sd") * math.sqrt(p.ctx.ppy))
                     .alias("sharpe")
                )
                .select([pl.col(p.name_col).alias("name"), pl.col("sharpe")])
            )

        # --- turnover from weights ---
        def turnover(self) -> pl.LazyFrame:
            p = self._p
            W = p.weights_long
            if W is None:
                # empty
                return p.returns_long.select(pl.lit(None).alias("name")).filter(pl.lit(False))
            w = pl.col(p._w_name)
            return (
                W.sort([p.name_col, p.date_col])
                 .with_columns((w - w.shift(1).over(p.name_col)).abs().alias("_tw"))
                 .group_by(p.name_col).agg([
                    pl.col("_tw").mean().alias("turnover"),
                 ])
                 .with_columns((pl.col("turnover") * p.ctx.ppy).alias("turnover_ann"))
                 .select([pl.col(p.name_col).alias("name"), "turnover", "turnover_ann"])
            )

        # --- regression vs benchmark (alpha/beta/R²) ---
        def regression(self) -> pl.LazyFrame:
            p = self._p
            B = p.benchmark_series
            if B is None:
                return p.returns_long.select(pl.lit(None).alias("name")).filter(pl.lit(False))

            RL = p.returns_long.join(B, on=p.date_col, how="inner")
            x = pl.col(p._ret_name)  # strategy
            y = pl.col("b")          # benchmark
            n = pl.count()
            sums = (
                RL.group_by(p.name_col)
                  .agg([
                      n.alias("_n"),
                      x.sum().alias("_sx"),
                      y.sum().alias("_sy"),
                      (x * y).sum().alias("_sxy"),
                      (y * y).sum().alias("_syy"),
                      (x * x).sum().alias("_sxx"),
                  ])
            )
            # sample moments and coefficients
            out = (
                sums.with_columns([
                    (pl.col("_sx") / pl.col("_n")).alias("_mx"),
                    (pl.col("_sy") / pl.col("_n")).alias("_my"),
                ])
                .with_columns([
                    ((pl.col("_syy") - pl.col("_n") * (pl.col("_my") ** 2)) / (pl.col("_n") - 1.0)).alias("_var_y"),
                    ((pl.col("_sxx") - pl.col("_n") * (pl.col("_mx") ** 2)) / (pl.col("_n") - 1.0)).alias("_var_x"),
                    ((pl.col("_sxy") - pl.col("_n") * pl.col("_mx") * pl.col("_my")) / (pl.col("_n") - 1.0)).alias("_cov_xy"),
                ])
                .with_columns([
                    pl.when(pl.col("_var_y") <= 0)
                      .then(pl.lit(float("nan")))
                      .otherwise(pl.col("_cov_xy") / pl.col("_var_y"))
                      .alias("beta"),
                ])
                .with_columns([
                    (pl.col("_mx") - pl.col("beta") * pl.col("_my")).alias("_alpha"),
                ])
            )
            ppy = p.ctx.ppy
            result = out.with_columns([
                ((1.0 + pl.col("_alpha")) ** ppy - 1.0).alias("alpha_ann"),
                pl.when((pl.col("_var_x") <= 0) | (pl.col("_var_y") <= 0))
                  .then(pl.lit(float("nan")))
                  .otherwise((pl.col("_cov_xy") ** 2) / (pl.col("_var_x") * pl.col("_var_y")))
                  .alias("r2"),
            ]).select([pl.col(p.name_col).alias("name"), "alpha_ann", "beta", "r2"])
            return result

        # --- PnL summary (from returns or provided PnL) ---
        def pnl_summary(self) -> pl.LazyFrame:
            p = self._p
            if p.pnl_long is not None:
                pnl = pl.col(p._pnl_name)
                seq = p.pnl_long
            else:
                # build pnl from returns and capital
                r = pl.col(p._ret_name)
                cap0 = float(p.ctx.capital0)
                seq = (
                    p.returns_long
                    .sort([p.name_col, p.date_col])
                    .with_columns(((1.0 + r).cum_prod().over(p.name_col) * cap0).alias("equity"))
                    .with_columns(pl.col("equity").shift(1).over(p.name_col).fill_null(cap0).alias("_eq_prev"))
                    .with_columns((pl.col("_eq_prev") * r).alias("pnl"))
                )
                pnl = pl.col("pnl")

            return (
                seq.group_by(p.name_col)
                  .agg([
                      pnl.sum().alias("total_pnl"),
                      pnl.mean().alias("avg_daily_pnl"),
                      pnl.max().alias("best_day_pnl"),
                      pnl.min().alias("worst_day_pnl"),
                      (pnl.std(ddof=1) * math.sqrt(p.ctx.ppy)).alias("pnl_vol_ann"),
                  ])
                  .select([pl.col(p.name_col).alias("name"),
                           "total_pnl", "avg_daily_pnl", "best_day_pnl", "worst_day_pnl", "pnl_vol_ann"])
            )

    # -------- plots namespace (render-only) --------
    class Plots(AnalyticsBase.Plots):
        def linechart(self, *, name: str, what: str = "equity") -> plt.Figure:
            """
            what: "equity" (build from returns & capital0) or "returns" (per-step)
            """
            p = self._p
            if what == "returns":
                df = (
                    p._returns_wide
                    .select([pl.col(p.date_col), pl.col(name)])
                    .collect()
                )
                s = AnalyticsBase._to_pd_series(df, date_col=p.date_col, val_col=name, name=name).dropna()
                fig = plt.figure(figsize=(7, 2.2)); ax = fig.gca()
                s.plot(ax=ax)
                ax.set_title(f"Returns — {name}")
                ax.set_xlabel("")
                plt.tight_layout()
                return fig

            # equity
            r = pl.col(p._ret_name)
            cap0 = float(p.ctx.capital0)
            seq = (
                p.returns_long
                 .filter(pl.col(p.name_col) == name)
                 .sort(p.date_col)
                 .with_columns(((1.0 + r).cum_prod()).alias("_m"))
                 .with_columns((pl.lit(cap0) * pl.col("_m")).alias("equity"))
                 .select([pl.col(p.date_col), pl.col("equity")])
                 .collect()
            )
            s = AnalyticsBase._to_pd_series(seq, date_col=p.date_col, val_col="equity", name=f"{name} (equity)")
            fig = plt.figure(figsize=(7, 2.2)); ax = fig.gca()
            s.plot(ax=ax)
            ax.set_title(f"Equity Curve — {name}")
            ax.set_xlabel("")
            plt.tight_layout()
            return fig

        def hist(self, *, name: str, bins: int = 50) -> plt.Figure:
            p = self._p
            df = (
                p._returns_wide
                .select([pl.col(p.date_col), pl.col(name)])
                .collect()
            )
            s = AnalyticsBase._to_pd_series(df, date_col=p.date_col, val_col=name, name=name).dropna()
            fig = plt.figure(figsize=(6, 2.0)); ax = fig.gca()
            s.hist(bins=bins, ax=ax)
            ax.set_title(f"Return Distribution — {name}")
            plt.tight_layout()
            return fig


# =========================
# Statistics analytics
# =========================

class Statistics(AnalyticsBase):
    """
    Analytics over predictions vs targets (IC, regressions, residuals).
    Inputs are wide by date ([date, series...]); we standardize to long:
      - predictions -> value name "pred"
      - targets     -> value name "y"
    """

    def __init__(
        self,
        *,
        predictions: Union[pl.DataFrame, pl.LazyFrame],   # wide: [date, strat...]
        targets:     Union[pl.DataFrame, pl.LazyFrame],   # wide: [date, strat...] OR single [date, y]
        date_col: str = "date",
        name_col: str = "name",
        pred_value_name: str = "pred",
        target_value_name: str = "y",
        ctx: Optional[Context] = None,
    ) -> None:
        super().__init__(date_col=date_col, name_col=name_col, ctx=ctx)
        self._pred_wide = self._ensure_lazy(predictions)
        self._tgt_wide  = self._ensure_lazy(targets)
        self._pred_name = pred_value_name
        self._tgt_name  = target_value_name

    # ---- standardized long views ----
    @property
    def pred_long(self) -> pl.LazyFrame:
        return self._melt(self._pred_wide, self._pred_name)

    @property
    def tgt_long(self) -> pl.LazyFrame:
        """
        If targets has multiple series, we align per-name; if it has a single series,
        we broadcast that target to all names in predictions.
        """
        tgt_cols = _detect_series_cols(_schema_names(self._tgt_wide), self.date_col)
        if len(tgt_cols) == 1:
            one = self._tgt_wide.select([pl.col(self.date_col), pl.col(tgt_cols[0]).alias(self._tgt_name)])
            # broadcast later during join (no name)
            return _as_lazy(one)
        return self._melt(self._tgt_wide, self._tgt_name)

    # -------- metrics namespace --------
    class Metrics(AnalyticsBase.Metrics):
        def _joined(self) -> pl.LazyFrame:
            p = self._p  # type: Statistics
            P = p.pred_long
            T = p.tgt_long

            # If targets are single series: join on date only then replicate by name using predictions
            tgt_cols = _detect_series_cols(_schema_names(p._tgt_wide), p.date_col)
            if len(tgt_cols) == 1:
                J = P.join(T, on=p.date_col, how="inner")
                return J  # columns: [date, name, pred, y]
            else:
                # multi-target: align by date & name
                return P.join(T, on=[p.date_col, p.name_col], how="inner")

        # --- Pearson IC (per name) ---
        def ic_pearson(self) -> pl.LazyFrame:
            p = self._p  # type: Statistics
            J = self._joined()
            x = pl.col(p._pred_name)
            y = pl.col(p._tgt_name)
            n = pl.count()
            g = (
                J.group_by(p.name_col)
                 .agg([
                     n.alias("_n"),
                     x.sum().alias("_sx"),
                     y.sum().alias("_sy"),
                     (x * y).sum().alias("_sxy"),
                     (x * x).sum().alias("_sxx"),
                     (y * y).sum().alias("_syy"),
                 ])
                 .with_columns([
                     (pl.col("_sx") / pl.col("_n")).alias("_mx"),
                     (pl.col("_sy") / pl.col("_n")).alias("_my"),
                 ])
                 .with_columns([
                     ((pl.col("_sxy") - pl.col("_n") * pl.col("_mx") * pl.col("_my")) / (pl.col("_n") - 1.0)).alias("_cov"),
                     ((pl.col("_sxx") - pl.col("_n") * (pl.col("_mx") ** 2)) / (pl.col("_n") - 1.0)).alias("_varx"),
                     ((pl.col("_syy") - pl.col("_n") * (pl.col("_my") ** 2)) / (pl.col("_n") - 1.0)).alias("_vary"),
                 ])
                 .with_columns(
                     pl.when((pl.col("_varx") <= 0) | (pl.col("_vary") <= 0))
                      .then(pl.lit(float("nan")))
                      .otherwise(pl.col("_cov") / (pl.col("_varx") * pl.col("_vary")).sqrt())
                      .alias("ic_pearson")
                 )
                 .select([pl.col(p.name_col).alias("name"), "ic_pearson"])
            )
            return g

        # --- Spearman IC (per name) ---
        def ic_spearman(self) -> pl.LazyFrame:
            p = self._p  # type: Statistics
            J = self._joined().sort([p.name_col, p.date_col])
            # rank within name
            J2 = J.with_columns([
                pl.col(p._pred_name).rank().over(p.name_col).alias("_rx"),
                pl.col(p._tgt_name).rank().over(p.name_col).alias("_ry"),
            ])
            # Pearson corr of ranks
            x = pl.col("_rx"); y = pl.col("_ry"); n = pl.count()
            out = (
                J2.group_by(p.name_col)
                  .agg([
                      n.alias("_n"),
                      x.sum().alias("_sx"),
                      y.sum().alias("_sy"),
                      (x * y).sum().alias("_sxy"),
                      (x * x).sum().alias("_sxx"),
                      (y * y).sum().alias("_syy"),
                  ])
                  .with_columns([
                      (pl.col("_sx") / pl.col("_n")).alias("_mx"),
                      (pl.col("_sy") / pl.col("_n")).alias("_my"),
                  ])
                  .with_columns([
                      ((pl.col("_sxy") - pl.col("_n") * pl.col("_mx") * pl.col("_my")) / (pl.col("_n") - 1.0)).alias("_cov"),
                      ((pl.col("_sxx") - pl.col("_n") * (pl.col("_mx") ** 2)) / (pl.col("_n") - 1.0)).alias("_varx"),
                      ((pl.col("_syy") - pl.col("_n") * (pl.col("_my") ** 2)) / (pl.col("_n") - 1.0)).alias("_vary"),
                  ])
                  .with_columns(
                      pl.when((pl.col("_varx") <= 0) | (pl.col("_vary") <= 0))
                        .then(pl.lit(float("nan")))
                        .otherwise(pl.col("_cov") / (pl.col("_varx") * pl.col("_vary")).sqrt())
                        .alias("ic_spearman")
                  )
                  .select([pl.col(p.name_col).alias("name"), "ic_spearman"])
            )
            return out

        # --- OLS regression y ~ a + b * pred (per name): alpha, beta, r2, t_beta ---
        def regression(self) -> pl.LazyFrame:
            p = self._p  # type: Statistics
            J = self._joined()
            x = pl.col(p._pred_name); y = pl.col(p._tgt_name); n = pl.count()

            sums = (
                J.group_by(p.name_col)
                 .agg([
                     n.alias("_n"),
                     x.sum().alias("_sx"),
                     y.sum().alias("_sy"),
                     (x * y).sum().alias("_sxy"),
                     (x * x).sum().alias("_sxx"),
                     (y * y).sum().alias("_syy"),
                 ])
                 .with_columns([
                     (pl.col("_sx") / pl.col("_n")).alias("_mx"),
                     (pl.col("_sy") / pl.col("_n")).alias("_my"),
                 ])
                 .with_columns([
                     ((pl.col("_sxy") - pl.col("_n") * pl.col("_mx") * pl.col("_my")) / (pl.col("_n") - 1.0)).alias("_cov"),
                     ((pl.col("_sxx") - pl.col("_n") * (pl.col("_mx") ** 2)) / (pl.col("_n") - 1.0)).alias("_varx"),
                     ((pl.col("_syy") - pl.col("_n") * (pl.col("_my") ** 2)) / (pl.col("_n") - 1.0)).alias("_vary"),
                 ])
                 .with_columns([
                     pl.when(pl.col("_varx") <= 0)
                       .then(pl.lit(float("nan")))
                       .otherwise(pl.col("_cov") / pl.col("_varx"))
                       .alias("beta"),
                 ])
                 .with_columns((pl.col("_my") - pl.col("beta") * pl.col("_mx")).alias("alpha"))
            )

            # r2 and t-stat for beta
            # SSE = var(y) * (n-1) - beta^2 * var(x) * (n-1)
            # sigma^2 = SSE / (n-2)
            # se_beta = sqrt( sigma^2 / ( (n-1)*var(x) ) )
            out = (
                sums.with_columns([
                    # R^2
                    pl.when((pl.col("_varx") <= 0) | (pl.col("_vary") <= 0))
                      .then(pl.lit(float("nan")))
                      .otherwise((pl.col("_cov") ** 2) / (pl.col("_varx") * pl.col("_vary")))
                      .alias("r2"),
                    # SSE & sigma^2
                    ( (pl.col("_vary") * (pl.col("_n") - 1.0)) - (pl.col("beta") ** 2) * (pl.col("_varx") * (pl.col("_n") - 1.0)) ).alias("_sse"),
                ])
                .with_columns( (pl.col("_sse") / (pl.col("_n") - 2.0)).alias("_sigma2") )
                .with_columns(
                    pl.when((pl.col("_varx") <= 0) | (pl.col("_n") <= 2))
                      .then(pl.lit(float("nan")))
                      .otherwise((pl.col("_sigma2") / (pl.col("_varx") * (pl.col("_n") - 1.0))).sqrt())
                      .alias("_se_beta")
                )
                .with_columns(
                    (pl.col("beta") / pl.col("_se_beta")).alias("t_beta")
                )
                .select([pl.col(p.name_col).alias("name"), "alpha", "beta", "r2", "t_beta"])
            )
            return out

    # -------- plots namespace --------
    class Plots(AnalyticsBase.Plots):
        def hist(self, *, name: str, which: str = "pred", bins: int = 50) -> plt.Figure:
            """
            which: 'pred', 'target', or 'resid'
            """
            p = self._p  # type: Statistics
            J = p.metrics._joined().filter(pl.col(p.name_col) == name).collect()
            pdf = J.to_pandas()
            if which == "pred":
                data = pd.Series(pdf[p._pred_name]).dropna()
                title = f"Predictions — {name}"
            elif which == "target":
                data = pd.Series(pdf[p._tgt_name]).dropna()
                title = f"Targets — {name}"
            else:
                resid = (pdf[p._tgt_name] - pdf[p._pred_name]).astype(float)
                data = pd.Series(resid).dropna()
                title = f"Residuals — {name}"
            fig = plt.figure(figsize=(6, 2.0)); ax = fig.gca()
            data.hist(bins=bins, ax=ax)
            ax.set_title(title); ax.set_xlabel("")
            plt.tight_layout()
            return fig

        def scatter(self, *, name: str) -> plt.Figure:
            """Scatter of target vs prediction."""
            p = self._p  # type: Statistics
            J = p.metrics._joined().filter(pl.col(p.name_col) == name).collect()
            pdf = J.to_pandas()
            x = pd.Series(pdf[p._pred_name]).astype(float)
            y = pd.Series(pdf[p._tgt_name]).astype(float)
            fig = plt.figure(figsize=(4.5, 4.0)); ax = fig.gca()
            ax.scatter(x, y, s=8, alpha=0.6)
            ax.set_xlabel("Prediction")
            ax.set_ylabel("Target")
            ax.set_title(f"Prediction vs Target — {name}")
            plt.tight_layout()
            return fig