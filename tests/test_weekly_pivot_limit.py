import unittest

import pandas as pd

from trading_strategy.strategies.confirmed_weekly_pivot import (
    WeeklyPivotLimitConfig,
    _simulate,
)


class WeeklyPivotLimitTest(unittest.TestCase):
    def test_breakeven_activates_after_five_minutes(self):
        timestamp = pd.date_range("2025-01-01", periods=7, freq="min", tz="UTC")
        frame = pd.DataFrame(
            {
                "timestamp": timestamp,
                "open": [100] * 7,
                "high": [101] * 7,
                "low": [99.5] * 5 + [99.0, 99.0],
                "close": [100] * 7,
            }
        )
        result = _simulate(
            frame, 0, 100.0, 110.0, -1.0, WeeklyPivotLimitConfig()
        )
        self.assertEqual(result["exit_reason"], "breakeven")
        self.assertEqual(result["holding_minutes"], 5)


if __name__ == "__main__":
    unittest.main()
