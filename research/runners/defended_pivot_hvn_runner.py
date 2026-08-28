"""Shared launcher implementation for defended-pivot HVN strategies."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from trading_strategy.strategies.defended_pivot_long import (
    DefendedPivotConfig,
    run_defended_pivot_equities,
    run_defended_pivot_frames,
)
from trading_strategy.utils.crypto import DEFAULT_CRYPTO_SYMBOLS, load_crypto_ohlc
from trading_strategy.utils.stocks import STOCK_UNIVERSES, stock_symbols


SECTORS = ["crypto", *STOCK_UNIVERSES]


def run(entry_mode: str, report_slug: str) -> None:
    parser = argparse.ArgumentParser(
        description=f"Run defended-pivot strategy with {entry_mode} entry."
    )
    parser.add_argument("--sector", choices=SECTORS, required=True)
    parser.add_argument("--symbols", nargs="+", default=None)
    parser.add_argument("--minimum-volume-ratio", type=float, default=1.5)
    parser.add_argument("--touch-zone-atr", type=float, default=0.5)
    parser.add_argument("--minimum-bounce-atr", type=float, default=1.5)
    parser.add_argument("--bounce-window-days", type=int, default=5)
    parser.add_argument("--profile-bins", type=int, default=30)
    parser.add_argument("--profile-range-atr", type=float, default=1.0)
    parser.add_argument("--volume-entry-window-days", type=int, default=5)
    parser.add_argument("--take-profit-percent", type=float, default=10.0)
    parser.add_argument("--stop-loss-percent", type=float, default=25.0)
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
    config = DefendedPivotConfig(
        minimum_volume_ratio=args.minimum_volume_ratio,
        touch_zone_atr=args.touch_zone_atr,
        minimum_bounce_atr=args.minimum_bounce_atr,
        bounce_window_days=args.bounce_window_days,
        entry_mode=entry_mode,
        profile_bins=args.profile_bins,
        profile_range_atr=args.profile_range_atr,
        volume_entry_window_days=args.volume_entry_window_days,
        take_profit_percent=args.take_profit_percent,
        stop_loss_percent=args.stop_loss_percent,
        maximum_holding_days=args.maximum_holding_days,
        fee_bps_per_side=5.0 if args.sector == "crypto" else 1.0,
        slippage_bps_per_side=2.0 if args.sector == "crypto" else 3.0,
        market_timezone="UTC" if args.sector == "crypto" else "America/New_York",
    )
    output = args.output_dir or (
        Path("research/reports") / report_slug / args.sector / "latest"
    )
    if args.sector != "crypto":
        run_defended_pivot_equities(
            args.data_dir or Path("data/us-equities/hourly-1y"),
            output,
            stock_symbols(args.sector, args.symbols),
            config,
        )
        return
    symbols = [
        symbol.upper() for symbol in (args.symbols or DEFAULT_CRYPTO_SYMBOLS)
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
        output,
        config,
        source="Binance Public Data",
        interval=args.crypto_interval,
        range_=f"{args.start}/{args.end}",
        failures=failures,
    )
