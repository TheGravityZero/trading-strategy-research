import unittest

import pandas as pd

from trading_strategy.strategies.ath_short import (
    AthShortConfig,
    backtest_ath_short,
)


class AthShortTest(unittest.TestCase):
    def test_enters_seven_percent_above_prior_ath_and_takes_profit(self):
        frame = pd.DataFrame(
            {
                "timestamp": pd.date_range(
                    "2025-01-01", periods=5, freq="h", tz="UTC"
                ),
                "open": [95, 99, 105, 107, 98],
                "high": [100, 101, 108, 109, 100],
                "low": [94, 98, 104, 105, 95],
                "close": [99, 100, 107, 106, 96],
                "volume": 1_000,
                "symbol": "TEST",
            }
        )
        config = AthShortConfig(
            entry_offset_percent=7,
            take_profit_percent=10,
            stop_loss_percent=15,
            order_lifetime_hours=4,
        )
        result = backtest_ath_short(frame, config)
        filled = result[result.order_filled]
        self.assertEqual(len(filled), 1)
        self.assertAlmostEqual(filled.iloc[0].ath_level, 100)
        self.assertAlmostEqual(filled.iloc[0].entry_price, 107)
        self.assertEqual(filled.iloc[0].exit_reason, "take_profit")
        self.assertAlmostEqual(filled.iloc[0].gross_return, 0.10)


if __name__ == "__main__":
    unittest.main()
