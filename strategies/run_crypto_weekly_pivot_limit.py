#!/usr/bin/env python3
"""Run the confirmed weekly-pivot crypto limit strategy."""

from __future__ import annotations

import argparse
from pathlib import Path

from cascades.strategies.confirmed_weekly_pivot import (
    WeeklyPivotLimitConfig,
    run_weekly_pivot_strategy,
)
from cascades.utils.crypto import DEFAULT_CRYPTO_SYMBOLS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
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
            "strategies/reports/crypto-weekly-pivot-limit/"
            "entry5-stop25-hold90d"
        ),
    )
    parser.add_argument("--entry-offset-percent", type=float, default=5.0)
    parser.add_argument("--stop-loss-percent", type=float, default=25.0)
    parser.add_argument("--order-lifetime-hours", type=int, default=4)
    parser.add_argument("--maximum-holding-days", type=int, default=90)
    parser.add_argument("--include-test", action="store_true")
    args = parser.parse_args()
    config = WeeklyPivotLimitConfig(
        entry_offset_percent=args.entry_offset_percent,
        order_lifetime_minutes=args.order_lifetime_hours * 60,
        initial_stop_loss_percent=args.stop_loss_percent,
        breakeven_after_minutes=None,
        maximum_holding_minutes=args.maximum_holding_days * 24 * 60,
    )
    run_weekly_pivot_strategy(
        args.raw_dir,
        args.events,
        args.output_dir,
        include_test=args.include_test,
        config=config,
        symbols=[symbol.upper() for symbol in args.symbols],
    )


if __name__ == "__main__":
    main()
