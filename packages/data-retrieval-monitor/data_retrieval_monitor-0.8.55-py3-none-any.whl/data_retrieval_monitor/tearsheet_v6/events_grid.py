# events_grid.py
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from bisect import bisect_right
import math

import numpy as np
import polars as pl

__all__ = [
    "uniformize_events_to_global_grid",
    "infer_base_step_seconds",
    "daterange_grid",
]

# -----------------------------------------------------------------------------
# Public helpers you can reuse anywhere
# -----------------------------------------------------------------------------

def infer_base_step_seconds(event_map: Dict[str, pl.DataFrame], date_col: str = "date") -> int:
    """
    Infer a reasonable base grid step (in seconds) from all positive deltas across series.
    Compatible with older Polars: compute deltas via datetime->ns->int64.
    """
    deltas: List[int] = []
    for df in event_map.values():
        if not isinstance(df, pl.DataFrame) or df.height < 2 or date_col not in df.columns:
            continue

        s = (
            df.select(pl.col(date_col))
              .drop_nulls()
              .with_columns(pl.col(date_col).cast(pl.Datetime))  # ensure datetime
              .sort(date_col)
        )

        # datetime (ns) -> int -> diff -> seconds as float, then list
        d_sec = (
            s.with_columns(
                 pl.col(date_col)
                   .dt.cast_time_unit("ns")
                   .cast(pl.Int64)
                   .diff()                                   # ns difference as int
                   .cast(pl.Float64)
                   .abs()
                   .truediv(1_000_000_000.0)                # convert ns to seconds
                   .alias("_diff_sec")
             )
             .select("_diff_sec")
             .drop_nulls()
             .to_series()
             .to_list()
        )

        for x in d_sec:
            if x and x > 0:
                deltas.append(max(1, int(x)))

    if not deltas:
        return 24 * 60 * 60  # default: daily

    deltas.sort()
    q_idx = max(0, int(len(deltas) * 0.25) - 1)  # robust-ish: ~25th percentile
    return max(1, int(deltas[q_idx]))


def daterange_grid(start: datetime, end: datetime, step_sec: int) -> pl.Series:
    """
    Inclusive datetime grid [start, end] with fixed step (seconds).
    Uses string interval for broad Polars compatibility.
    """
    if start > end:
        start, end = end, start
    return pl.datetime_range(
        start=start,
        end=end,
        interval=f"{int(step_sec)}s",
        closed="both",
        eager=True,
    )

# -----------------------------------------------------------------------------
# Internal helpers (kept small & unit-testable)
# -----------------------------------------------------------------------------

def _normalize_event_series(df: pl.DataFrame, *, date_col: str) -> Tuple[pl.DataFrame, str]:
    """
    Ensure df has a datetime 'date_col' and exactly one returns/value column (float64).
    Returns (normalized_df, value_col_name).
    """
    if not isinstance(df, pl.DataFrame):
        raise TypeError("Each series must be a Polars DataFrame.")

    if date_col not in df.columns:
        raise ValueError(f"DataFrame is missing date column '{date_col}'.")

    value_cols = [c for c in df.columns if c != date_col]
    if not value_cols:
        raise ValueError(f"DataFrame has no value column besides '{date_col}'.")
    val_col = value_cols[0]

    dfx = (
        df.select([
            pl.col(date_col).cast(pl.Datetime),
            pl.col(val_col).cast(pl.Float64).alias(val_col),
        ])
        .drop_nulls(subset=[date_col])
        .sort(date_col)
    )
    return dfx, val_col


def _collect_series_meta(
    event_map: Dict[str, pl.DataFrame],
    *,
    date_col: str,
) -> Tuple[List[Tuple[str, pl.DataFrame, str]], Optional[datetime], Optional[datetime]]:
    """
    Normalize all series and collect global min/max datetimes.
    Returns (series_meta, min_dt, max_dt) where
      series_meta = list of (name, normalized_df, value_col).
    """
    series_meta: List[Tuple[str, pl.DataFrame, str]] = []
    min_dt: Optional[datetime] = None
    max_dt: Optional[datetime] = None

    for name, df in event_map.items():
        if not isinstance(df, pl.DataFrame) or df.height == 0:
            continue
        dfx, val_col = _normalize_event_series(df, date_col=date_col)
        if dfx.height == 0:
            continue

        s_min = dfx.select(pl.col(date_col).min()).item()
        s_max = dfx.select(pl.col(date_col).max()).item()
        min_dt = s_min if (min_dt is None or s_min < min_dt) else min_dt
        max_dt = s_max if (max_dt is None or s_max > max_dt) else max_dt

        series_meta.append((name, dfx, val_col))

    return series_meta, min_dt, max_dt


def _grid_index_at_or_before(grid_list: List[datetime], t: datetime) -> int:
    """Largest index i such that grid_list[i] <= t; clamped to [0, n-1]."""
    i = bisect_right(grid_list, t) - 1
    return max(0, min(len(grid_list) - 1, i))


def _apply_impulse(buf: List[float], idx: int, r_total: float) -> None:
    """Place the entire return on a single bucket."""
    buf[idx] += float(r_total)


def _apply_split(
    buf: List[float],
    *,
    left: int,
    right: int,
    r_total: float,
    clamp_step_return: Optional[float],
) -> None:
    """
    Geometric split of total return r_total across [left, right) steps.
    If r_total <= -1.0, apply -100% at the last step only (crash handling).
    """
    n_steps = max(1, right - left)

    if r_total <= -1.0:
        idx = max(left, right - 1)
        buf[idx] += -1.0
        return

    step_r = (1.0 + float(r_total)) ** (1.0 / n_steps) - 1.0
    if clamp_step_return is not None:
        cap = float(clamp_step_return)
        if step_r > cap:
            step_r = cap
        elif step_r < -cap:
            step_r = -cap

    for k in range(left, right):
        buf[k] += step_r  # additive per-step; comp happens downstream


def _build_series_on_grid(
    *,
    name: str,
    dfx: pl.DataFrame,
    val_col: str,
    date_col: str,
    grid_list: List[datetime],
    fill_mode: str,
    clamp_step_return: Optional[float],
) -> pl.Series:
    """
    Materialize one series onto the fixed grid as per the chosen fill mode.
    """
    nG = len(grid_list)
    buf = [0.0] * nG
    returns = pl.col(val_col)  # stylistic alias

    # Extract event times & returns as lists
    ev_times = dfx.select(pl.col(date_col)).to_series().to_list()
    ev_rets  = dfx.select(returns).to_series().fill_null(0.0).to_list()

    if not ev_times:
        return pl.Series(name, buf, dtype=pl.Float64)

    prev_t = ev_times[0]

    for i in range(len(ev_times)):
        t       = ev_times[i]
        r_total = ev_rets[i]
        if not isinstance(r_total, (int, float)) or not math.isfinite(float(r_total)):
            r_total = 0.0

        # strictly after prev_t and up to t (inclusive)
        left  = bisect_right(grid_list, prev_t)
        right = bisect_right(grid_list, t)

        if fill_mode == "impulse":
            idx = _grid_index_at_or_before(grid_list, t)
            _apply_impulse(buf, idx, r_total)
        else:
            _apply_split(
                buf,
                left=left,
                right=right,
                r_total=r_total,
                clamp_step_return=clamp_step_return,
            )

        prev_t = t

    return pl.Series(name, buf, dtype=pl.Float64)

# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def uniformize_events_to_global_grid(
    event_map: Dict[str, pl.DataFrame],
    *,
    date_col: str = "date",
    fill_mode: str = "split",          # "split" or "impulse"
    step_seconds: int | None = None,   # if None, inferred
    clamp_step_return: float | None = None,  # absolute cap per step for "split" mode (e.g., 0.002 = 20 bps)
) -> pl.DataFrame:
    """
    Convert irregular event returns (per series) to a regular time grid (wide Polars frame):
      - Input for each series is a Polars DataFrame with at least [date_col, <series_column>]
      - The series column is taken as the first non-date column in each df
      - Returns are assumed as DECIMAL FRACTIONS (e.g., 0.01 = +1%)

    fill_mode:
      - "split": For each event at time t_i with total return r_i (from previous event to t_i),
                 split r_i evenly across N grid steps: (1+r_i)^(1/N)-1.
                 Optional `clamp_step_return` caps per-step magnitude (abs).
      - "impulse": Put the entire r_i on the grid bucket at t_i (previous steps 0).

    Returns:
      Polars DataFrame: ["date", <col1>, <col2>, ...] with grid-aligned returns per step.
    """
    if not event_map:
        return pl.DataFrame({"date": []})

    # 1) Normalize per-series frames and detect global [min_dt, max_dt]
    series_meta, min_dt, max_dt = _collect_series_meta(event_map, date_col=date_col)
    if not series_meta:
        return pl.DataFrame({"date": []})

    # 2) Build grid
    step_sec = int(step_seconds) if step_seconds else infer_base_step_seconds(event_map, date_col=date_col)
    grid = daterange_grid(min_dt, max_dt, step_sec)
    grid_list = grid.to_list()
    if not grid_list:
        return pl.DataFrame({"date": []})
    date_series = pl.Series("date", grid_list, dtype=pl.Datetime)

    # 3) Build each series on the grid
    cols: List[pl.Series] = []
    fmode = "impulse" if str(fill_mode).lower() == "impulse" else "split"

    for name, dfx, val_col in series_meta:
        col = _build_series_on_grid(
            name=name,
            dfx=dfx,
            val_col=val_col,
            date_col=date_col,
            grid_list=grid_list,
            fill_mode=fmode,
            clamp_step_return=clamp_step_return,
        )
        cols.append(col)

    # 4) Assemble wide frame
    out = pl.DataFrame([date_series] + cols)
    return out