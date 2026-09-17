import unittest
import numpy as np
import pandas as pd
from trading_strategy.strategies.cointegration import CointegrationConfig, select_pairs, backtest_pair


class CointegrationTests(unittest.TestCase):
    def setUp(self):
        self.index = pd.date_range('2020-01-01', periods=420, freq='h', tz='UTC')
        rng = np.random.default_rng(12)
        x = 100 + np.cumsum(rng.normal(0, 0.4, len(self.index)))
        y = 2 * x + rng.normal(0, 0.3, len(x))
        self.closes = pd.DataFrame({'A': y, 'B': x}, index=self.index)
        self.bars = pd.DataFrame({'y_close': y, 'x_close': x, 'y_open': y, 'x_open': x}, index=self.index)
        self.split = self.index[300]
        self.config = CointegrationConfig(window=20)

    def test_train_selection_ignores_test(self):
        original = select_pairs(self.closes, self.split, self.config)
        self.assertTrue(original.selected.iloc[0])
        changed = self.closes.copy()
        changed.loc[self.split:, 'A'] *= 20
        pd.testing.assert_frame_equal(original, select_pairs(changed, self.split, self.config))

    def test_future_does_not_change_past(self):
        original = backtest_pair(self.bars, self.split, 0, 2, self.config)
        changed = self.bars.copy()
        changed.loc[self.index[390]:, 'y_close'] *= 1.1
        other = backtest_pair(changed, self.split, 0, 2, self.config)
        pd.testing.assert_frame_equal(original.iloc[:90], other.iloc[:90])

    def test_costs_terminal_exit_and_next_bar(self):
        result = backtest_pair(self.bars, self.split, 0, 2, self.config)
        self.assertGreater((result.event == 'entry').sum(), 0)
        np.testing.assert_allclose(result.cost, result.turnover * 0.0012)
        self.assertEqual(result.position.iloc[-1], 0)
        spread = self.bars.y_close - 2 * self.bars.x_close
        z = (spread - spread.shift().rolling(20).mean()) / spread.shift().rolling(20).std()
        np.testing.assert_allclose(result.signal_zscore, z.shift().loc[self.split:])

    def test_missing_prices_rejected(self):
        self.bars.iloc[310, 0] = np.nan
        with self.assertRaises(ValueError):
            backtest_pair(self.bars, self.split, 0, 2, self.config)

    def test_zero_crossing_exits(self):
        bars = self.bars.copy()
        bars.loc[self.index[299], 'y_close'] = 2 * bars.loc[self.index[299], 'x_close'] + 0.7
        bars.loc[self.index[300], 'y_close'] = 2 * bars.loc[self.index[300], 'x_close'] - 0.1
        result = backtest_pair(bars, self.split, 0, 2, self.config)
        self.assertEqual(result.event.iloc[0], 'entry')
        self.assertEqual(result.event.iloc[1], 'exit')


if __name__ == '__main__':
    unittest.main()
