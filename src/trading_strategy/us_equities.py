"""Compatibility exports for the refactored US-equity strategy.

New code should import strategy logic from
``trading_strategy.strategies.us_equity_weekly_pivot`` and reusable data helpers from
``trading_strategy.utils.stocks``.
"""

from .strategies.us_equity_weekly_pivot import (
    EquityPivotConfig,
    backtest_equity,
    run_equity_study,
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
    "EquityPivotConfig",
    "backtest_equity",
    "confirmed_weekly_pivots",
    "download_yahoo_hourly",
    "run_equity_study",
]
