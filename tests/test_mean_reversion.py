import unittest
from unittest.mock import patch
import importlib.util
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd

from trading_strategy.strategies.mean_reversion import (
    MeanReversionConfig, backtest_mean_reversion, build_features, select_pairs,
)


class MeanReversionTests(unittest.TestCase):
    def setUp(self):
        self.index = pd.date_range('2025-01-01', periods=420, freq='h', tz='UTC')
        rng = np.random.default_rng(12)
        x = 100 + rng.normal(0, 0.4, 420).cumsum()
        y = 2 * x + rng.normal(0, 0.3, 420)
        self.bars = pd.DataFrame(dict(y_close=y, x_close=x, y_open=y, x_open=x), index=self.index)
        self.split = self.index[300]
        self.config = MeanReversionConfig(window=20, regime_window=60, regime_every=10)

    def test_causality_and_train_selection(self):
        original, _ = backtest_mean_reversion(self.bars, self.split, 0, 2, self.config)
        altered = self.bars.copy()
        altered.loc[self.index[390]:, 'y_close'] *= 1.1
        changed, _ = backtest_mean_reversion(altered, self.split, 0, 2, self.config)
        pd.testing.assert_frame_equal(original.iloc[:90], changed.iloc[:90])
        closes = self.bars[['y_close', 'x_close']]
        modified = closes.copy()
        modified.loc[self.split:, 'y_close'] *= 5
        pd.testing.assert_frame_equal(select_pairs(closes, self.split, self.config),
                                      select_pairs(modified, self.split, self.config))

    def test_costs_ledger_and_next_open(self):
        result, trades = backtest_mean_reversion(self.bars, self.split, 0, 2, self.config)
        self.assertGreater(len(trades), 0)
        np.testing.assert_allclose(result.cost, result.turnover * 0.0012)
        self.assertEqual(result.position.iloc[-1], 0)
        self.assertAlmostEqual((1 + trades.net_return).prod(), result.equity.iloc[-1])
        features = build_features(self.bars, 0, 2, self.config)
        np.testing.assert_allclose(result.signal_zscore, features.zscore.shift().loc[self.split:])

    def controlled(self, zvalues, pvalues=None, shock=False, **overrides):
        config = MeanReversionConfig(window=20, regime_window=60, **overrides)
        bars = self.bars.iloc[:300 + len(zvalues)].copy()
        bars[['y_open', 'y_close']] = 200.
        bars[['x_open', 'x_close']] = 100.
        if shock:
            bars.loc[self.split:, 'y_close'] = 220.
            bars.loc[self.index[301]:, 'y_open'] = 220.
        features = pd.DataFrame({'spread': 0., 'zscore': 0., 'regime_pvalue': 0.01}, index=bars.index)
        features.iloc[299:299 + len(zvalues), features.columns.get_loc('zscore')] = zvalues
        if pvalues is not None:
            features.iloc[299:299 + len(zvalues), features.columns.get_loc('regime_pvalue')] = pvalues
        with patch('trading_strategy.strategies.mean_reversion.build_features', return_value=features):
            return backtest_mean_reversion(bars, self.split, 0, 2, config)

    def test_zero_crossing_both_directions_and_fixed_price_cost(self):
        for sign in (-1, 1):
            result, trades = self.controlled([sign * 2.5, -sign * 0.1, 0])
            self.assertEqual(trades.exit_reason.iloc[0], 'mean_crossing')
            self.assertEqual(trades.direction.iloc[0], -sign)
            self.assertAlmostEqual(result.equity.iloc[-1], 1 - 2 * .0012)

    def test_regime_exit_and_cooldown(self):
        result, trades = self.controlled([2.5] * 5, [.01, .5, .01, .01, .01], cooldown_bars=3)
        self.assertEqual(trades.exit_reason.iloc[0], 'regime_break')
        self.assertEqual((result.event == 'entry').sum(), 1)

    def test_z_stop_time_stop_and_terminal_cost(self):
        _, trades = self.controlled([2.5, 4., 0])
        self.assertEqual(trades.exit_reason.iloc[0], 'z_stop')
        _, trades = self.controlled([2.5] * 5, max_holding_bars=2)
        self.assertEqual(trades.exit_reason.iloc[0], 'time_stop')
        result, trades = self.controlled([2.5] * 3)
        self.assertEqual(trades.exit_reason.iloc[0], 'end_of_data')
        self.assertGreater(result.cost.iloc[-1], 0)

    def test_invalid_data_and_parameters(self):
        for name, value in [('regime_every', 0), ('regime_alpha', float('nan')),
                            ('stop_loss', 1), ('window', 2.5), ('fee_bps', -1)]:
            with self.assertRaises(ValueError):
                MeanReversionConfig(**{name: value}).validate()
        for bars in (self.bars.drop(self.index[305]), self.bars.assign(y_close=np.nan)):
            with self.assertRaises(ValueError):
                backtest_mean_reversion(bars, self.split, 0, 2, self.config)

    def test_loss_stop_uses_previous_close_and_next_open(self):
        result, trades = self.controlled([2.5] * 4, shock=True, stop_loss=.01)
        self.assertEqual(result.event.iloc[0], 'entry')
        self.assertEqual(result.exit_reason.iloc[1], 'loss_stop')
        self.assertLess(trades.net_return.iloc[0], -.01)

    def test_constant_spread_disables_entries(self):
        bars = self.bars.assign(y_close=200., x_close=100.)
        result, trades = backtest_mean_reversion(bars, self.split, 0, 2, self.config)
        self.assertTrue(trades.empty)
        self.assertTrue((result.equity == 1).all())

    def test_loader_rejects_partial_aggregate_bar(self):
        path = Path(__file__).resolve().parents[1] / 'research/runners/run_mean_reversion.py'
        spec = importlib.util.spec_from_file_location('mean_reversion_runner', path)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        start = pd.Timestamp('2025-07-01', tz='UTC')
        end = start + pd.Timedelta(hours=1)
        source = pd.DataFrame({'timestamp': pd.date_range(start, periods=60, freq='min'),
                               'open': 100., 'close': 101.})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / 'BTCUSDT/1m/BTCUSDT-1m-2025-07-01.zip'
            archive.parent.mkdir(parents=True)
            archive.touch()
            with patch.object(runner, 'read_kline_archive', return_value=source):
                result = runner.load_complete_bars(root, 'BTCUSDT', start, end, '1h')
                self.assertEqual(len(result), 1)
            with patch.object(runner, 'read_kline_archive', return_value=source.drop(20)):
                with self.assertRaisesRegex(ValueError, 'Missing source bars'):
                    runner.load_complete_bars(root, 'BTCUSDT', start, end, '1h')


if __name__ == '__main__':
    unittest.main()
