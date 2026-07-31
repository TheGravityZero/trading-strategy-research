import unittest

import pandas as pd

from trading_strategy.strategies.defended_pivot_long import (
    DefendedPivotConfig,
    _defense_high_volume_zone,
    _pivot_volume_ratio,
)


class DefendedPivotLongTest(unittest.TestCase):
    def test_pivot_volume_uses_only_previous_weeks_as_baseline(self):
        timestamps = pd.date_range(
            "2025-01-06", periods=14, freq="7D", tz="UTC"
        )
        frame = pd.DataFrame(
            {
                "timestamp": timestamps,
                "open": 1.0,
                "high": 1.0,
                "low": 1.0,
                "close": 1.0,
                "volume": [100.0] * 12 + [200.0, 300.0],
                "symbol": "TEST",
            }
        )
        ratio = _pivot_volume_ratio(
            frame,
            DefendedPivotConfig(
                volume_lookback_weeks=12,
                market_timezone="UTC",
            ),
        )
        self.assertAlmostEqual(ratio.iloc[12], 2.0)
        self.assertAlmostEqual(ratio.iloc[13], 3.0)

    def test_hvn_is_selected_near_pivot(self):
        frame = pd.DataFrame(
            {
                "high": [96, 100, 101],
                "low": [94, 98, 99],
                "close": [95, 99, 100],
                "volume": [1, 100, 10],
            }
        )
        low, center, high, share = _defense_high_volume_zone(
            frame,
            pivot=100,
            atr=10,
            config=DefendedPivotConfig(profile_bins=10),
        )
        self.assertEqual((low, center, high), (98, 99, 100))
        self.assertGreater(share, 0.8)


if __name__ == "__main__":
    unittest.main()
