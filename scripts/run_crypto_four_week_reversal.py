#!/usr/bin/env python3
"""Run the crypto four-week extreme reversal strategy."""

from __future__ import annotations

import argparse
from pathlib import Path

from cascades.strategies.four_week_reversal import run_four_week_strategy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--events",
        type=Path,
        default=Path("reports/study-2025-07_2026-06/events_and_trades.csv"),
    )
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/strategies/crypto-four-week-reversal"),
    )
    parser.add_argument("--include-test", action="store_true")
    args = parser.parse_args()
    run_four_week_strategy(
        args.raw_dir,
        args.events,
        args.output_dir,
        include_test=args.include_test,
    )


if __name__ == "__main__":
    main()
