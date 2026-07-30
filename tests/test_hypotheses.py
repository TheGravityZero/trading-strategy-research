import unittest

import numpy as np
import pandas as pd

from cascades.hypotheses import cluster_bootstrap_ci


class HypothesisTest(unittest.TestCase):
    def test_cluster_bootstrap_is_deterministic(self):
        frame = pd.DataFrame(
            {
                "cluster_id": [0, 0, 1, 2],
                "value": [0.01, 0.02, -0.01, 0.03],
            }
        )
        first = cluster_bootstrap_ci(frame, "value", iterations=100)
        second = cluster_bootstrap_ci(frame, "value", iterations=100)
        self.assertEqual(first, second)
        self.assertTrue(np.isfinite(first).all())


if __name__ == "__main__":
    unittest.main()
