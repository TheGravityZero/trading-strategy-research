#!/usr/bin/env python3
"""Run the unified weekly-pivot limit strategy for one market sector."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from trading_strategy.strategies.weekly_pivot_limit import (
    WeeklyPivotConfig,
    run_frames_study,
    run_weekly_pivot_study,
)
from trading_strategy.utils.crypto import (
    DEFAULT_CRYPTO_SYMBOLS,
    load_crypto_ohlc,
)
from trading_strategy.utils.stocks import STOCK_UNIVERSES, stock_symbols


SECTORS = ["crypto", *STOCK_UNIVERSES]


def config_from_args(args: argparse.Namespace) -> WeeklyPivotConfig:
    return WeeklyPivotConfig(
        entry_offset_percent=args.entry_offset_percent,
        take_profit_percent=args.take_profit_percent,
        stop_loss_percent=args.stop_loss_percent,
        order_lifetime_hours=args.order_lifetime_hours,
        maximum_holding_days=args.maximum_holding_days,
        long_only=True,
        fee_bps_per_side=5.0 if args.sector == "crypto" else 1.0,
        slippage_bps_per_side=2.0 if args.sector == "crypto" else 3.0,
        market_timezone="UTC" if args.sector == "crypto" else "America/New_York",
    )


def run_crypto(args: argparse.Namespace) -> None:
    symbols = [
        symbol.upper()
        for symbol in (args.symbols or DEFAULT_CRYPTO_SYMBOLS)
    ]
    start = pd.Timestamp(args.start, tz="UTC")
    end = pd.Timestamp(args.end, tz="UTC")
    frames = {}
    failures = {}
    for symbol in symbols:
        try:
            frames[symbol] = load_crypto_ohlc(
                args.data_dir or Path("data/raw"),
                symbol,
                start,
                end,
                args.crypto_interval,
            )
        except Exception as exc:
            failures[symbol] = str(exc)
            print(f"{symbol}: FAILED: {exc}", flush=True)
    output_dir = args.output_dir or (
        Path("research/reports/weekly-pivot-limit")
        / "crypto"
        / "latest"
    )
    run_frames_study(
        frames,
        output_dir,
        config_from_args(args),
        source="Binance Public Data",
        interval=args.crypto_interval,
        range_=f"{args.start}/{args.end}",
        failures=failures,
    )


def run_equities(args: argparse.Namespace) -> None:
    symbols = stock_symbols(args.sector, args.symbols)
    output_dir = args.output_dir or (
        Path("research/reports/weekly-pivot-limit")
        / args.sector
        / "latest"
    )
    run_weekly_pivot_study(
        args.data_dir or Path("data/us-equities/hourly-1y"),
        output_dir,
        symbols,
        config_from_args(args),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sector", choices=SECTORS, required=True)
    parser.add_argument("--symbols", nargs="+", default=None)
    parser.add_argument("--entry-offset-percent", type=float, default=5.0)
    parser.add_argument("--take-profit-percent", type=float, default=15.0)
    parser.add_argument("--stop-loss-percent", type=float, default=25.0)
    parser.add_argument("--order-lifetime-hours", type=int, default=4)
    parser.add_argument("--maximum-holding-days", type=int, default=60)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument(
        "--crypto-interval",
        choices=["15min", "30min", "1h", "4h"],
        default="15min",
    )
    parser.add_argument("--start", default="2025-07-01")
    parser.add_argument("--end", default="2026-07-01")
    args = parser.parse_args()
    if args.sector == "crypto":
        run_crypto(args)
    else:
        run_equities(args)


if __name__ == "__main__":
    main()
