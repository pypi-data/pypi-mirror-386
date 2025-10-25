# analytics_base.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from datetime import datetime

import math
import polars as pl


@dataclass
class AnalyticsConfig:
    date_col: str = "date"
    name_col: str = "name"


class Analytics:
    """Base analytics class (compute: Polars; convert to pandas only when rendering)."""
    def __init__(self, *, cfg: AnalyticsConfig | None = None) -> None:
        self.cfg = cfg or AnalyticsConfig()

    @property
    def date_col(self) -> str:
        return self.cfg.date_col

    @property
    def name_col(self) -> str:
        return self.cfg.name_col


class BacktestAnalytics(Analytics):
    """
    Backtest-style analytics:
      - returns_wide_lf : LazyFrame [date, strat1, strat2, ...]
      - optional weights_long_lf : LazyFrame [date, name, asset, weight]; used for turnover
    """
    def __init__(
        self,
        returns_wide_lf: pl.LazyFrame,
        *,
        weights_long_lf: Optional[pl.LazyFrame] = None,
        cfg: AnalyticsConfig | None = None,
    ) -> None:
        super().__init__(cfg=cfg)
        self.returns_wide_lf = self._ensure_dt_ns(returns_wide_lf)
        self.weights_long_lf = self._ensure_dt_ns(weights_long_lf) if weights_long_lf is not None else None

    def _ensure_dt_ns(self, lf: Optional[pl.LazyFrame]) -> Optional[pl.LazyFrame]:
        if lf is None:
            return None
        return lf.with_columns(pl.col(self.date_col).cast(pl.Datetime).dt.cast_time_unit("ns"))

    def returns_long(self) -> pl.LazyFrame:
        names = self.returns_wide_lf.collect_schema().names()
        series_cols = [c for c in names if c != self.date_col]
        return (
            self.returns_wide_lf
            .melt(id_vars=self.date_col, value_vars=series_cols, variable_name=self.name_col, value_name="ret")
        )

    # ----- Metrics (Polars-lazy) -----
    def sharpe(self, periods_per_year: int = 252) -> pl.LazyFrame:
        R = self.returns_long()
        r = pl.col("ret")
        return (
            R.group_by(self.name_col)
             .agg([r.mean().alias("_mu"), r.std(ddof=1).alias("_sd")])
             .with_columns(
                 pl.when(pl.col("_sd") == 0)
                   .then(pl.lit(float("nan")))
                   .otherwise(pl.col("_mu") / pl.col("_sd") * math.sqrt(periods_per_year))
                   .alias("sharpe")
             )
             .select([self.name_col, "sharpe"])
        )

    def turnover(self) -> pl.LazyFrame:
        """
        Portfolio turnover per strategy:
          turnover = mean_t ( sum_assets |w_t - w_{t-1}| ) / 2
        Expects weights_long_lf: [date, name, asset, weight].
        """
        if self.weights_long_lf is None:
            return pl.LazyFrame({self.name_col: pl.Series([], dtype=pl.Utf8), "turnover": pl.Series([], dtype=pl.Float64)})

        cols = self.weights_long_lf.collect_schema().names()
        need = {self.date_col, self.name_col, "asset", "weight"}
        if not need.issubset(set(cols)):
            raise ValueError(f"weights_long_lf must have columns: {sorted(need)}")

        w = self.weights_long_lf
        return (
            w.sort([self.name_col, "asset", self.date_col])
             .with_columns(pl.col("weight").diff().abs().over([self.name_col, "asset"]).alias("_abs_dw"))
             .group_by([self.name_col, self.date_col])
             .agg(pl.col("_abs_dw").sum().alias("_sum_abs"))
             .group_by(self.name_col)
             .agg((pl.col("_sum_abs").mean() / 2.0).alias("turnover"))
             .select([self.name_col, "turnover"])
        )

    def pnl_long(self, price_returns_long_lf: pl.LazyFrame, notional_per_name: float = 1_000_000.0) -> pl.LazyFrame:
        """
        Simple dollar PnL by name = notional * return (example).
        price_returns_long_lf must be [date, name, ret].
        """
        r = pl.col("ret")
        return (
            price_returns_long_lf
            .select([pl.col(self.date_col), pl.col(self.name_col), (pl.lit(float(notional_per_name)) * r).alias("pnl")])
        )


class StatAnalytics(Analytics):
    """
    Statistics-style analytics:
      - preds_lf   : [date, id, pred]
      - targets_lf : [date, id, target]
    Computes cross-sectional Information Coefficient (IC) and pooled R^2.
    """
    def __init__(
        self,
        preds_lf: pl.LazyFrame,
        targets_lf: pl.LazyFrame,
        *,
        id_col: str = "id",
        cfg: AnalyticsConfig | None = None,
    ) -> None:
        super().__init__(cfg=cfg)
        self.id_col = id_col
        self.preds_lf = self._ensure_dt_ns(preds_lf)
        self.targets_lf = self._ensure_dt_ns(targets_lf)

    def _ensure_dt_ns(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        return lf.with_columns(pl.col(self.date_col).cast(pl.Datetime).dt.cast_time_unit("ns"))

    def _join(self) -> pl.LazyFrame:
        return (
            self.preds_lf.join(self.targets_lf, on=[self.date_col, self.id_col], how="inner")
            .select([pl.col(self.date_col), pl.col(self.id_col), pl.col("pred"), pl.col("target")])
        )

    # ---------- helpers to compute corr from sufficient statistics ----------
    @staticmethod
    def _corr_from_sums(n: pl.Expr, sx: pl.Expr, sy: pl.Expr, sxx: pl.Expr, syy: pl.Expr, sxy: pl.Expr) -> pl.Expr:
        num = sxy - sx * sy / n
        den = ((sxx - sx * sx / n) * (syy - sy * sy / n)).sqrt()
        return pl.when(den == 0).then(pl.lit(float("nan"))).otherwise(num / den)

    def ic_daily(self) -> pl.LazyFrame:
        """Cross-sectional IC per date."""
        J = self._join()
        p, t = pl.col("pred"), pl.col("target")
        grp = (
            J.group_by(self.date_col)
             .agg([
                 pl.count().cast(pl.Float64).alias("_n"),
                 p.sum().alias("_sx"),
                 t.sum().alias("_sy"),
                 (p * p).sum().alias("_sxx"),
                 (t * t).sum().alias("_syy"),
                 (p * t).sum().alias("_sxy"),
             ])
        )
        return grp.with_columns(
            self._corr_from_sums(pl.col("_n"), pl.col("_sx"), pl.col("_sy"), pl.col("_sxx"), pl.col("_syy"), pl.col("_sxy")).alias("ic")
        ).select([pl.col(self.date_col), pl.col("ic")])

    def ic_summary(self) -> pl.LazyFrame:
        """Summary of daily IC: mean/sd/t."""
        IC = self.ic_daily()
        return (
            IC.select([
                pl.col("ic").mean().alias("IC_mean"),
                pl.col("ic").std(ddof=1).alias("IC_sd"),
                pl.count().alias("_n"),
            ])
            .with_columns(
                pl.when(pl.col("IC_sd") == 0).then(pl.lit(float("nan")))
                 .otherwise(pl.col("IC_mean") / pl.col("IC_sd") * pl.col("_n").cast(pl.Float64).sqrt())
                 .alias("IC_t")
            )
            .select(["IC_mean", "IC_sd", "IC_t"])
        )

    def r2_pooled(self) -> pl.LazyFrame:
        """Pooled (all rows) R^2 via corr^2."""
        J = self._join()
        p, t = pl.col("pred"), pl.col("target")
        s = J.select([
            pl.count().cast(pl.Float64).alias("_n"),
            p.sum().alias("_sx"),
            t.sum().alias("_sy"),
            (p * p).sum().alias("_sxx"),
            (t * t).sum().alias("_syy"),
            (p * t).sum().alias("_sxy"),
        ])
        corr = self._corr_from_sums(pl.col("_n"), pl.col("_sx"), pl.col("_sy"), pl.col("_sxx"), pl.col("_syy"), pl.col("_sxy"))
        return s.with_columns((corr * corr).alias("R2")).select(["R2"])