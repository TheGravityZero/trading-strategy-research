import unittest

import pandas as pd

from trading_strategy.strategies.ath_retest_volume_short import (
    AthRetestVolumeConfig,
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


if __name__ == "__main__":
    unittest.main()
