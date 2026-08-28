#!/usr/bin/env python3
"""Run the rolling-regression crypto pair baseline."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from trading_strategy.strategies.stat_arb import (
    StatArbConfig,
    backtest_stat_arb,
    write_stat_arb_results,
)
from trading_strategy.utils.crypto import load_crypto_ohlc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--y-symbol", default="ETHUSDT")
    parser.add_argument("--x-symbol", default="BTCUSDT")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--interval", choices=["15min", "30min", "1h", "4h"], default="1h")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("research/reports/crypto-stat-arb/latest"))
    parser.add_argument("--regression-window", type=int, default=240)
    parser.add_argument("--zscore-window", type=int, default=120)
    parser.add_argument("--correlation-window", type=int, default=120)
    parser.add_argument("--minimum-correlation", type=float, default=0.50)
    parser.add_argument("--entry-zscore", type=float, default=2.0)
    parser.add_argument("--exit-zscore", type=float, default=0.25)
    parser.add_argument("--stop-zscore", type=float, default=4.0)
    args = parser.parse_args()

    start, end = pd.Timestamp(args.start, tz="UTC"), pd.Timestamp(args.end, tz="UTC")
    y_symbol, x_symbol = args.y_symbol.upper(), args.x_symbol.upper()
    y = load_crypto_ohlc(args.data_dir, y_symbol, start, end, args.interval)
    x = load_crypto_ohlc(args.data_dir, x_symbol, start, end, args.interval)
    config = StatArbConfig(
        regression_window=args.regression_window,
        zscore_window=args.zscore_window,
        correlation_window=args.correlation_window,
        minimum_correlation=args.minimum_correlation,
        entry_zscore=args.entry_zscore,
        exit_zscore=args.exit_zscore,
        stop_zscore=args.stop_zscore,
    )
    result = backtest_stat_arb(y, x, config)
    metadata = write_stat_arb_results(
        result, args.output_dir, config, y_symbol, x_symbol, args.interval
    )
    print(metadata["summary"])


if __name__ == "__main__":
    main()
