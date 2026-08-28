#!/usr/bin/env python3
"""Run the volume-backed defended weekly-pivot long strategy."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from trading_strategy.strategies.defended_pivot_long import (
    DefendedPivotConfig,
    run_defended_pivot_equities,
    run_defended_pivot_frames,
)
from trading_strategy.utils.crypto import (
    DEFAULT_CRYPTO_SYMBOLS,
    load_crypto_ohlc,
)
from trading_strategy.utils.stocks import STOCK_UNIVERSES, stock_symbols


SECTORS = ["crypto", *STOCK_UNIVERSES]


def config_from_args(args: argparse.Namespace) -> DefendedPivotConfig:
    return DefendedPivotConfig(
        volume_lookback_weeks=args.volume_lookback_weeks,
        minimum_volume_ratio=args.minimum_volume_ratio,
        touch_zone_atr=args.touch_zone_atr,
        minimum_bounce_atr=args.minimum_bounce_atr,
        bounce_window_days=args.bounce_window_days,
        entry_offset_percent=args.entry_offset_percent,
        take_profit_percent=args.take_profit_percent,
        stop_loss_percent=args.stop_loss_percent,
        order_lifetime_hours=args.order_lifetime_hours,
        maximum_holding_days=args.maximum_holding_days,
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
    run_defended_pivot_frames(
        frames,
        args.output_dir
        or Path("research/reports/defended-pivot-long/crypto/latest"),
        config_from_args(args),
        source="Binance Public Data",
        interval=args.crypto_interval,
        range_=f"{args.start}/{args.end}",
        failures=failures,
    )


def run_equities(args: argparse.Namespace) -> None:
    run_defended_pivot_equities(
        args.data_dir or Path("data/us-equities/hourly-1y"),
        args.output_dir
        or Path("research/reports/defended-pivot-long")
        / args.sector
        / "latest",
        stock_symbols(args.sector, args.symbols),
        config_from_args(args),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sector", choices=SECTORS, required=True)
    parser.add_argument("--symbols", nargs="+", default=None)
    parser.add_argument("--volume-lookback-weeks", type=int, default=12)
    parser.add_argument("--minimum-volume-ratio", type=float, default=1.5)
    parser.add_argument("--touch-zone-atr", type=float, default=0.5)
    parser.add_argument("--minimum-bounce-atr", type=float, default=1.5)
    parser.add_argument("--bounce-window-days", type=int, default=5)
    parser.add_argument("--entry-offset-percent", type=float, default=5.0)
    parser.add_argument("--take-profit-percent", type=float, default=10.0)
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
