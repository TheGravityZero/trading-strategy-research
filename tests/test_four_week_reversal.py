import unittest

import numpy as np
import pandas as pd

from trading_strategy.strategies.four_week_reversal import (
    FourWeekReversalConfig,
    _classify_event,
    add_four_week_levels,
)


class FourWeekLevelTest(unittest.TestCase):
    def test_levels_use_only_completed_weeks(self):
        timestamp = pd.date_range(
            "2025-01-06", periods=6 * 7 * 24, freq="h", tz="UTC"
        )
        week = ((timestamp - timestamp[0]).days // 7).to_numpy()
        frame = pd.DataFrame(
            {
                "timestamp": timestamp,
                "high": 100 + week,
                "low": 90 - week,
                "close": 95 + np.zeros(len(timestamp)),
            }
        )
        result = add_four_week_levels(frame)
        sixth_week = result[result["week_start"] == pd.Timestamp("2025-02-10", tz="UTC")]
        self.assertEqual(sixth_week["four_week_high"].iloc[0], 104)
        self.assertEqual(sixth_week["four_week_low"].iloc[0], 86)

    def test_four_percent_long_limit_fill(self):
        timestamp = pd.date_range("2025-01-01", periods=3, freq="min", tz="UTC")
        frame = pd.DataFrame(
            {
                "timestamp": timestamp,
                "open": [100, 98, 96],
                "high": [101, 99, 97],
                "low": [99, 97, 95.9],
                "close": [100, 98, 96.5],
                "four_week_low": [100.0] * 3,
                "four_week_high": [110.0] * 3,
                "trend_return": [-0.01] * 3,
            }
        )
        event = pd.Series({"direction": -1.0})
        result = _classify_event(
            frame,
            0,
            event,
            FourWeekReversalConfig(
                entry_offset_percent=4,
                entry_window_minutes=2,
                horizons=(),
            ),
        )
        self.assertTrue(result["eligible"])
        self.assertEqual(result["entry_price"], 96.0)
        self.assertEqual(result["entry_delay_minutes"], 2)


if __name__ == "__main__":
    unittest.main()
