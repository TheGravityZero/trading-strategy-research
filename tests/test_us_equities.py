import unittest
from unittest.mock import patch

import pandas as pd

from trading_strategy.us_equities import EquityPivotConfig, backtest_equity
from trading_strategy.utils.stocks import STOCK_UNIVERSES, stock_symbols


class EquityBacktestTest(unittest.TestCase):
    def test_sector_universes_are_separate(self):
        sectors = [set(symbols) for symbols in STOCK_UNIVERSES.values()]
        for index, left in enumerate(sectors):
            for right in sectors[index + 1 :]:
                self.assertFalse(left & right)
        self.assertEqual(stock_symbols("oil")[:3], ["XOM", "CVX", "COP"])
        self.assertEqual(stock_symbols("it", ["msft"]), ["MSFT"])

    def test_fills_breakdown_and_takes_profit(self):
        timestamps = pd.date_range("2025-01-06 15:30", periods=12, freq="7D", tz="UTC")
        frame = pd.DataFrame(
            {
                "timestamp": timestamps,
                "open": [105, 104, 100, 102, 104, 105, 106, 99, 94, 96, 100, 101],
                "high": [106, 105, 102, 104, 106, 107, 108, 101, 96, 101, 102, 103],
                "low": [103, 101, 95, 99, 102, 103, 104, 97, 90, 94, 98, 99],
                "close": [104, 102, 100, 103, 105, 106, 107, 98, 95, 100, 101, 102],
                "volume": 1_000,
                "symbol": "TEST",
            }
        )
        pivots = pd.DataFrame(
            [{
                "kind": "low", "level": 100.0,
                "pivot_week": pd.Timestamp("2025-01-01", tz="UTC"),
                "available_at": timestamps[6],
            }]
        )
        config = EquityPivotConfig(entry_offset_percent=5, order_lifetime_hours=200)
        with patch(
            "trading_strategy.strategies.us_equity_weekly_pivot."
            "confirmed_stock_weekly_pivots",
            return_value=pivots,
        ):
            result = backtest_equity(frame, config)
        self.assertTrue(result.iloc[0].order_filled)
        self.assertEqual(result.iloc[0].entry_price, 95)
        self.assertEqual(result.iloc[0].exit_reason, "take_profit")

    def test_short_stop_is_loss_relative_to_entry(self):
        frame = pd.DataFrame(
            {
                "timestamp": pd.date_range(
                    "2025-01-06 15:30", periods=2, freq="h", tz="UTC"
                ),
                "open": [99, 105],
                "high": [99, 132],
                "low": [98, 104],
                "close": [99, 130],
                "volume": 1_000,
                "symbol": "TEST",
            }
        )
        pivots = pd.DataFrame(
            [{
                "kind": "high", "level": 100.0,
                "pivot_week": pd.Timestamp("2024-12-01", tz="UTC"),
                "available_at": frame.iloc[0].timestamp,
            }]
        )
        with patch(
            "trading_strategy.strategies.us_equity_weekly_pivot."
            "confirmed_stock_weekly_pivots",
            return_value=pivots,
        ):
            result = backtest_equity(frame, EquityPivotConfig())
        self.assertAlmostEqual(result.iloc[0].gross_return, -0.25)
