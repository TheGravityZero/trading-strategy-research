import tempfile
import unittest
from pathlib import Path

from cascades.backtest import BacktestConfig, run_event_backtest, summarize
from cascades.events import DetectorConfig, attach_forward_returns, detect_events
from cascades.features import build_features
from cascades.pipeline import run_pipeline
from cascades.synthetic import make_synthetic_klines


class PrototypeTest(unittest.TestCase):
    def setUp(self):
        self.klines = make_synthetic_klines(rows=10_000)

    def test_features_are_causal_at_boundary(self):
        first = build_features(self.klines.iloc[:5000])
        second = build_features(self.klines.iloc[:6000])
        columns = ["return_z", "volume_z", "range_z", "taker_imbalance"]
        for column in columns:
            self.assertAlmostEqual(
                first.iloc[-1][column], second.iloc[4999][column], places=12
            )

    def test_detector_and_backtest(self):
        features = build_features(self.klines)
        events = attach_forward_returns(features, detect_events(features))
        self.assertGreater(len(events), 0)
        trades = run_event_backtest(events)
        metrics = summarize(trades)
        self.assertEqual(metrics["trades"], len(trades.dropna(subset=["net_return"])))

    def test_fixed_strategy_modes(self):
        features = build_features(self.klines)
        events = attach_forward_returns(features, detect_events(features))
        continuation = run_event_backtest(
            events, BacktestConfig(strategy_mode="continuation")
        )
        reversal = run_event_backtest(
            events, BacktestConfig(strategy_mode="reversal")
        )
        self.assertTrue((continuation["strategy"] == "continuation").all())
        self.assertTrue((reversal["strategy"] == "reversal").all())

    def test_pipeline_writes_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            metrics = run_pipeline(self.klines, output)
            self.assertTrue((output / "summary.json").exists())
            self.assertTrue((output / "events_and_trades.csv").exists())
            self.assertGreater(metrics["trades"], 0)

    def test_oi_filter_rejects_non_deleveraging_event(self):
        klines = self.klines.copy()
        klines["sum_open_interest"] = 1000.0
        features = build_features(klines)
        events = detect_events(
            features, DetectorConfig(oi_drop_threshold=-0.002)
        )
        self.assertEqual(len(events), 0)


if __name__ == "__main__":
    unittest.main()
