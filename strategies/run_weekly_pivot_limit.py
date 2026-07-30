#!/usr/bin/env python3
"""Run weekly-pivot limit strategy for one market sector."""

from __future__ import annotations

import argparse
from pathlib import Path

from cascades.strategies.confirmed_weekly_pivot import (
    WeeklyPivotLimitConfig,
    run_weekly_pivot_strategy,
)
from cascades.strategies.us_equity_weekly_pivot import (
    EquityPivotConfig,
    run_equity_study,
)
from cascades.utils.crypto import DEFAULT_CRYPTO_SYMBOLS
from cascades.utils.stocks import STOCK_UNIVERSES, stock_symbols


SECTORS = ["crypto", *STOCK_UNIVERSES]


def run_crypto(args: argparse.Namespace) -> None:
    symbols = [
        symbol.upper()
        for symbol in (args.symbols or DEFAULT_CRYPTO_SYMBOLS)
    ]
    output_dir = args.output_dir or Path(
        "strategies/reports/weekly-pivot-limit/crypto/"
        "entry5-stop25-hold90d"
    )
    run_weekly_pivot_strategy(
        args.data_dir or Path("data/raw"),
        args.events,
        output_dir,
        include_test=args.include_test,
        config=WeeklyPivotLimitConfig(
            entry_offset_percent=args.entry_offset_percent,
            order_lifetime_minutes=args.order_lifetime_hours * 60,
            initial_stop_loss_percent=args.stop_loss_percent,
            breakeven_after_minutes=None,
            maximum_holding_minutes=(
                (args.maximum_holding_days or 90) * 24 * 60
            ),
        ),
        symbols=symbols,
    )


def run_equities(args: argparse.Namespace) -> None:
    symbols = stock_symbols(args.sector, args.symbols)
    holding_days = args.maximum_holding_days or 60
    take_profit = (
        args.take_profit_percent
        if args.take_profit_percent is not None
        else 15.0
    )
    output_dir = args.output_dir or (
        Path("strategies/reports/weekly-pivot-limit")
        / args.sector
        / "long-tp15-hold60d"
    )
    run_equity_study(
        args.data_dir or Path("data/us-equities/hourly-1y"),
        output_dir,
        symbols,
        EquityPivotConfig(
            entry_offset_percent=args.entry_offset_percent,
            take_profit_percent=take_profit,
            stop_loss_percent=args.stop_loss_percent,
            order_lifetime_hours=args.order_lifetime_hours,
            maximum_holding_days=holding_days,
            long_only=True,
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sector", choices=SECTORS, required=True)
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=None,
        help="Explicit override for the selected sector universe",
    )
    parser.add_argument("--entry-offset-percent", type=float, default=5.0)
    parser.add_argument("--take-profit-percent", type=float, default=None)
    parser.add_argument("--stop-loss-percent", type=float, default=25.0)
    parser.add_argument("--order-lifetime-hours", type=int, default=4)
    parser.add_argument("--maximum-holding-days", type=int, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)

    parser.add_argument(
        "--events",
        type=Path,
        default=Path("data/processed/crypto-cascade-events.csv"),
        help="Crypto event file; ignored for equity sectors",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Override the default data directory for the selected sector",
    )
    parser.add_argument("--include-test", action="store_true")
    args = parser.parse_args()
    if args.sector == "crypto":
        run_crypto(args)
    else:
        run_equities(args)


if __name__ == "__main__":
    main()
