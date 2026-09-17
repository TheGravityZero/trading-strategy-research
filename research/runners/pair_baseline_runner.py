"""Shared CLI for simple crypto pair baselines."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from trading_strategy.strategies.correlation_divergence import (
    CorrelationDivergenceConfig,
    backtest_correlation_divergence,
)
from trading_strategy.strategies.pair_reversion import write_pair_results
from trading_strategy.strategies.regression_spread import (
    RegressionSpreadConfig,
    backtest_regression_spread,
)
from trading_strategy.utils.crypto import load_crypto_ohlc


def run_pair_baseline(kind: str) -> None:
    definitions = {
        "correlation-divergence": (
            "CorrelationDivergence",
            CorrelationDivergenceConfig,
            backtest_correlation_divergence,
        ),
        "regression-spread": (
            "RollingRegressionSpread",
            RegressionSpreadConfig,
            backtest_regression_spread,
        ),
    }
    strategy_name, config_type, backtest = definitions[kind]
    parser = argparse.ArgumentParser(description=f"Run {strategy_name} baseline")
    parser.add_argument("--y-symbol", default="ETHUSDT")
    parser.add_argument("--x-symbol", default="BTCUSDT")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--interval", choices=["15min", "30min", "1h", "4h"], default="1h")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("research/reports") / kind / "latest",
    )
    if kind == "regression-spread":
        parser.add_argument("--regression-window", type=int, default=240)
    else:
        parser.add_argument("--correlation-window", type=int, default=120)
        parser.add_argument("--minimum-correlation", type=float, default=0.50)
    parser.add_argument("--zscore-window", type=int, default=120)
    parser.add_argument("--entry-zscore", type=float, default=2.0)
    parser.add_argument("--exit-zscore", type=float, default=0.25)
    parser.add_argument("--stop-zscore", type=float, default=4.0)
    args = parser.parse_args()

    start, end = pd.Timestamp(args.start, tz="UTC"), pd.Timestamp(args.end, tz="UTC")
    y_symbol, x_symbol = args.y_symbol.upper(), args.x_symbol.upper()
    y = load_crypto_ohlc(args.data_dir, y_symbol, start, end, args.interval)
    x = load_crypto_ohlc(args.data_dir, x_symbol, start, end, args.interval)
    fields = {
        key: value for key, value in vars(args).items()
        if key in config_type.__dataclass_fields__
    }
    config = config_type(**fields)
    result = backtest(y, x, config)
    metadata = write_pair_results(
        result, args.output_dir, config, strategy=strategy_name,
        y_symbol=y_symbol, x_symbol=x_symbol, interval=args.interval,
    )
    print(metadata["summary"])
