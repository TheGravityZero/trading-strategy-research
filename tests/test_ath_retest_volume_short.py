import unittest

import pandas as pd

from trading_strategy.strategies.ath_retest_volume_short import (
    AthRetestVolumeConfig,
    _close_short,
    _upper_high_volume_node,
)


class AthRetestVolumeShortTest(unittest.TestCase):
    def test_volume_node_is_selected_from_upper_half(self):
        frame = pd.DataFrame(
            {
                "high": [55, 75, 91, 92],
                "low": [45, 65, 89, 90],
                "close": [50, 70, 90, 91],
                "volume": [10, 10, 1_000, 500],
            }
        )
        node, share = _upper_high_volume_node(
            frame,
            correction_low=40,
            ath=100,
            config=AthRetestVolumeConfig(profile_bins=6),
        )
        self.assertEqual(node, 95)
        self.assertGreater(share, 0.9)

    def test_explicit_structural_stop_is_used(self):
        frame = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(
                    ["2026-01-01", "2026-01-02"], utc=True
                ),
                "high": [101, 106],
                "low": [99, 90],
                "close": [100, 95],
            }
        )
        result = _close_short(
            frame,
            fill=0,
            entry=100,
            config=AthRetestVolumeConfig(stop_loss_percent=15),
            stop_price=105,
        )
        self.assertEqual(result["exit_reason"], "stop")
        self.assertEqual(result["exit_price"], 105)


if __name__ == "__main__":
    unittest.main()
