#!/usr/bin/env python3
"""Run the failed-ATH-retest volume-node short strategy."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from trading_strategy.strategies.ath_retest_volume_short import (
    AthRetestVolumeConfig,
    run_ath_retest_equities,
    run_ath_retest_frames,
)
from trading_strategy.utils.crypto import (
    DEFAULT_CRYPTO_SYMBOLS,
    load_crypto_ohlc,
)
from trading_strategy.utils.stocks import STOCK_UNIVERSES, stock_symbols


SECTORS = ["crypto", *STOCK_UNIVERSES]


def config_from_args(args: argparse.Namespace) -> AthRetestVolumeConfig:
    return AthRetestVolumeConfig(
        minimum_correction_percent=args.minimum_correction_percent,
        ath_retest_distance_percent=args.ath_retest_distance_percent,
        profile_bins=args.profile_bins,
        upper_profile_fraction=args.upper_profile_fraction,
        entry_lifetime_days=args.entry_lifetime_days,
        take_profit_percent=args.take_profit_percent,
        stop_mode=args.stop_mode,
        stop_loss_percent=args.stop_loss_percent,
        maximum_holding_days=args.maximum_holding_days,
        fee_bps_per_side=5.0 if args.sector == "crypto" else 1.0,
        slippage_bps_per_side=2.0 if args.sector == "crypto" else 3.0,
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
    run_ath_retest_frames(
        frames,
        args.output_dir
        or Path("strategies/reports/ath-retest-volume-short/crypto/latest"),
        config_from_args(args),
        source="Binance Public Data",
        interval=args.crypto_interval,
        range_=f"{args.start}/{args.end}",
        failures=failures,
    )


def run_equities(args: argparse.Namespace) -> None:
    run_ath_retest_equities(
        args.data_dir or Path("data/us-equities/hourly-1y"),
        args.output_dir
        or Path("strategies/reports/ath-retest-volume-short")
        / args.sector
        / "latest",
        stock_symbols(args.sector, args.symbols),
        config_from_args(args),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sector", choices=SECTORS, required=True)
    parser.add_argument("--symbols", nargs="+", default=None)
    parser.add_argument("--minimum-correction-percent", type=float, default=15.0)
    parser.add_argument("--ath-retest-distance-percent", type=float, default=3.0)
    parser.add_argument("--profile-bins", type=int, default=30)
    parser.add_argument("--upper-profile-fraction", type=float, default=0.5)
    parser.add_argument("--entry-lifetime-days", type=int, default=5)
    parser.add_argument("--take-profit-percent", type=float, default=10.0)
    parser.add_argument(
        "--stop-mode", choices=["percent", "ath", "hvn"], default="percent"
    )
    parser.add_argument("--stop-loss-percent", type=float, default=15.0)
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
