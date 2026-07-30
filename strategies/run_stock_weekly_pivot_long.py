#!/usr/bin/env python3
"""Run the selected long-only US-equity weekly-pivot strategy."""

from __future__ import annotations

import argparse
from pathlib import Path

from cascades.strategies.us_equity_weekly_pivot import (
    EquityPivotConfig,
    run_equity_study,
)
from cascades.utils.stocks import STOCK_UNIVERSES, stock_symbols


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sector",
        choices=[*STOCK_UNIVERSES, "all"],
        default="it",
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=None,
        help="Explicit override for --sector",
    )
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data/us-equities/hourly-1y")
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
    )
    parser.add_argument("--entry-offset-percent", type=float, default=5.0)
    parser.add_argument("--take-profit-percent", type=float, default=15.0)
    parser.add_argument("--stop-loss-percent", type=float, default=25.0)
    parser.add_argument("--order-lifetime-hours", type=int, default=4)
    parser.add_argument("--maximum-holding-days", type=int, default=60)
    args = parser.parse_args()
    symbols = stock_symbols(args.sector, args.symbols)
    output_dir = args.output_dir or Path(
        "strategies/reports/stock-weekly-pivot"
    ) / args.sector / "long-tp15-hold60d"
    config = EquityPivotConfig(
        entry_offset_percent=args.entry_offset_percent,
        take_profit_percent=args.take_profit_percent,
        stop_loss_percent=args.stop_loss_percent,
        order_lifetime_hours=args.order_lifetime_hours,
        maximum_holding_days=args.maximum_holding_days,
        long_only=True,
    )
    run_equity_study(
        args.data_dir,
        output_dir,
        symbols,
        config,
    )


if __name__ == "__main__":
    main()
