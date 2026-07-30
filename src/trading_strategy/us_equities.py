"""Compatibility exports for the unified weekly-pivot strategy.

New code should import strategy logic from
``trading_strategy.strategies.weekly_pivot_limit`` and reusable data helpers from
``trading_strategy.utils.stocks``.
"""

from .strategies.weekly_pivot_limit import (
    WeeklyPivotConfig,
    backtest_weekly_pivot,
    run_weekly_pivot_study,
)
from .utils.stocks import (
    DEFAULT_STOCK_SYMBOLS,
    confirmed_stock_weekly_pivots,
    download_stock_hourly,
)

DEFAULT_SYMBOLS = DEFAULT_STOCK_SYMBOLS
confirmed_weekly_pivots = confirmed_stock_weekly_pivots
download_yahoo_hourly = download_stock_hourly

__all__ = [
    "DEFAULT_SYMBOLS",
    "WeeklyPivotConfig",
    "backtest_weekly_pivot",
    "confirmed_weekly_pivots",
    "download_yahoo_hourly",
    "run_weekly_pivot_study",
]
