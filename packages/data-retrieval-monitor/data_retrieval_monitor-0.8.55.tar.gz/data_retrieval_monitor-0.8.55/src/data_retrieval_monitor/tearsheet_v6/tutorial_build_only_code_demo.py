# tutorial_build_only_code_demo.py
# -*- coding: utf-8 -*-
"""Minimal example: Build backtest/prediction dashboards and report paths."""

from __future__ import annotations

from pathlib import Path

from wrapped_helper import (
    make_backtest_bundle,
    make_prediction_bundle,
    build_dashboards,
)

def main():
    output_dir = Path("output/tutorial_build_only").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    backtest_bundle = make_backtest_bundle()
    prediction_bundle = make_prediction_bundle()

    paths = build_dashboards(
        backtest_bundle=backtest_bundle,
        prediction_bundle=prediction_bundle,
        backtest_figures=[
            'snapshot', 'yearly_returns', 'rolling_beta',
            'rolling_volatility', 'rolling_sharpe', 'rolling_sortino',
            'drawdowns_periods', 'drawdown', 'monthly_heatmap',
            'histogram', 'distribution',
        ],
        backtest_tables=["metrics", "eoy", "drawdown_top10"],
        prediction_figures=['IC', 'sign'],
        custom_backtest_figures=[],
        custom_prediction_tables=[],
        output_dir=str(output_dir),
    )

    print("Dashboard outputs:")
    for key, value in paths.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
