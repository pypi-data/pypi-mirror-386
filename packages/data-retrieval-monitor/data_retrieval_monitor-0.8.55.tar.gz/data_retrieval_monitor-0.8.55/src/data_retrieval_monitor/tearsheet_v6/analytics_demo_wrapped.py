# analytics_demo_wrapped.py
from __future__ import annotations

"""
CLI demo using the wrapped helper to generate backtest + prediction dashboards.
Run:
    python3 analytics_demo_wrapped.py
"""

from wrapped_helper import make_backtest_bundle, make_prediction_bundle, build_dashboards


def main() -> None:
    backtest = make_backtest_bundle()
    prediction = make_prediction_bundle()
    paths = build_dashboards(
        backtest_bundle=backtest,
        prediction_bundle=prediction,
        backtest_figures=["returns", "drawdown"],
        backtest_tables=["metrics", "monthly"],
        prediction_figures=["IC", "t", "sign"],
        prediction_tables=["pred_metrics"],
        output_dir="output/demo_wrapped",
    )
    print("Dashboards generated:")
    for key, value in paths.items():
        print(f"  {key:>10}: {value}")


if __name__ == "__main__":
    main()
