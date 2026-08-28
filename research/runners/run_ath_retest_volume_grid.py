#!/usr/bin/env python3
"""Run the ATH-retest parameter grid with structural stop levels."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from trading_strategy.strategies.ath_retest_volume_short import (
    AthRetestVolumeConfig,
    run_ath_retest_frames,
)
from trading_strategy.utils.crypto import DEFAULT_CRYPTO_SYMBOLS, load_crypto_ohlc
from trading_strategy.utils.stocks import (
    STOCK_UNIVERSES,
    download_stock_hourly,
    load_stock_hourly,
    stock_symbols,
)


CORRECTIONS = (7, 10, 12)
RETEST_DISTANCES = (3, 5, 7)
STOP_MODES = ("ath", "hvn")
TAKE_PROFITS = (10, 15, 20)


def load_frames(args: argparse.Namespace) -> tuple[dict, dict, str, str, str]:
    frames = {}
    failures = {}
    if args.sector == "crypto":
        symbols = [s.upper() for s in (args.symbols or DEFAULT_CRYPTO_SYMBOLS)]
        start = pd.Timestamp(args.start, tz="UTC")
        end = pd.Timestamp(args.end, tz="UTC")
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
        return (
            frames,
            failures,
            "Binance Public Data",
            args.crypto_interval,
            f"{args.start}/{args.end}",
        )
    symbols = stock_symbols(args.sector, args.symbols)
    data_dir = args.data_dir or Path("data/us-equities/hourly-1y")
    for symbol in symbols:
        try:
            frames[symbol] = load_stock_hourly(
                download_stock_hourly(symbol, data_dir)
            )
        except Exception as exc:
            failures[symbol] = str(exc)
    return frames, failures, "Yahoo Finance chart API", "1h", "1y"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sector", choices=["crypto", *STOCK_UNIVERSES], required=True)
    parser.add_argument("--symbols", nargs="+", default=None)
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--crypto-interval", default="15min")
    parser.add_argument("--start", default="2025-07-01")
    parser.add_argument("--end", default="2026-07-01")
    args = parser.parse_args()
    frames, failures, source, interval, range_ = load_frames(args)
    root = args.output_root or (
        Path("research/reports/ath-retest-volume-short/grid") / args.sector
    )
    for correction in CORRECTIONS:
        for retest in RETEST_DISTANCES:
            for stop_mode in STOP_MODES:
                for take_profit in TAKE_PROFITS:
                    name = (
                        f"corr{correction:02d}-retest{retest:02d}-"
                        f"stop-{stop_mode}-tp{take_profit:02d}"
                    )
                    config = AthRetestVolumeConfig(
                        minimum_correction_percent=correction,
                        ath_retest_distance_percent=retest,
                        stop_mode=stop_mode,
                        take_profit_percent=take_profit,
                        fee_bps_per_side=5.0 if args.sector == "crypto" else 1.0,
                        slippage_bps_per_side=2.0 if args.sector == "crypto" else 3.0,
                    )
                    print(f"\n[{args.sector}] {name}", flush=True)
                    run_ath_retest_frames(
                        frames,
                        root / name,
                        config,
                        source=source,
                        interval=interval,
                        range_=range_,
                        failures=failures,
                    )


if __name__ == "__main__":
    main()
