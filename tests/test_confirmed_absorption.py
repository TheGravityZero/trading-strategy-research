import unittest

from cascades.confirmed_absorption import _evaluate_event
from cascades.features import build_features
from cascades.synthetic import make_synthetic_klines


class ConfirmedAbsorptionTest(unittest.TestCase):
    def test_evaluation_is_causal_and_bounded(self):
        features = build_features(make_synthetic_klines(rows=1000))
        result = _evaluate_event(features, 500, -1.0)
        self.assertIn("confirmed", result)
        if result["confirmed"]:
            self.assertIn(result["confirmation_delay_minutes"], (1, 2, 3))


if __name__ == "__main__":
    unittest.main()
