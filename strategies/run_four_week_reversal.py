#!/usr/bin/env python3
"""Run the four-week extreme reversal strategy for one sector."""

from __future__ import annotations

import argparse
from pathlib import Path

from trading_strategy.strategies.four_week_reversal import (
    FourWeekReversalConfig,
    run_four_week_strategy,
)
from trading_strategy.utils.crypto import DEFAULT_CRYPTO_SYMBOLS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sector", choices=["crypto"], default="crypto")
    parser.add_argument(
        "--events",
        type=Path,
        default=Path("data/processed/crypto-cascade-events.csv"),
    )
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--symbols", nargs="+", default=DEFAULT_CRYPTO_SYMBOLS
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "strategies/reports/four-week-reversal/crypto/offset-4pct"
        ),
    )
    parser.add_argument(
        "--entry-mode",
        choices=["offset_limit", "reclaim"],
        default="offset_limit",
    )
    parser.add_argument("--entry-offset-percent", type=float, default=4.0)
    parser.add_argument("--entry-window-minutes", type=int, default=60)
    parser.add_argument("--reclaim-minutes", type=int, default=5)
    parser.add_argument("--include-test", action="store_true")
    args = parser.parse_args()
    run_four_week_strategy(
        args.raw_dir,
        args.events,
        args.output_dir,
        include_test=args.include_test,
        config=FourWeekReversalConfig(
            entry_mode=args.entry_mode,
            entry_offset_percent=args.entry_offset_percent,
            entry_window_minutes=args.entry_window_minutes,
            reclaim_minutes=args.reclaim_minutes,
        ),
        symbols=[symbol.upper() for symbol in args.symbols],
    )


if __name__ == "__main__":
    main()
