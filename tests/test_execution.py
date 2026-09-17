import unittest
import numpy as np
import pandas as pd
from trading_strategy.strategies.execution import simulate_account, account_summary, simulate_long_portfolio


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.index = pd.date_range('2025-01-01', periods=5, freq='h', tz='UTC')
        self.bars = pd.DataFrame(100., index=self.index, columns=['y_open', 'x_open', 'y_close', 'x_close'])
        self.signal = pd.Series([1, 1, 0, 0, 0], index=self.index)
        self.beta = pd.Series(1., index=self.index)

    def test_cash_conservation_and_cost_decomposition(self):
        result = simulate_account(self.bars, self.signal, self.beta, self.index[1])
        np.testing.assert_allclose(result.equity, result.cash + result.inventory_value)
        self.assertAlmostEqual(result.gross_pnl.sum(), 0.)
        self.assertAlmostEqual(result.equity.iloc[-1], 1 - result.fees.sum() - result.slippage.sum())
        self.assertEqual(result.qy.iloc[-1], 0.)
        self.assertEqual(result.qx.iloc[-1], 0.)

    def test_beta_change_charges_actual_rebalance(self):
        self.beta.iloc[1] = 3.
        result = simulate_account(self.bars, self.signal, self.beta, self.index[1], fee_bps=10, slippage_bps=0)
        self.assertGreater(result.rebalance_turnover.iloc[1], .49)
        self.assertGreater(result.fees.iloc[1], .00049)
        self.assertEqual(account_summary(result)['trades'], 1)

    def test_next_open_and_price_gap(self):
        self.bars.loc[self.index[1]:, ['y_open', 'y_close']] = 120.
        result = simulate_account(self.bars, self.signal, self.beta, self.index[1], fee_bps=0, slippage_bps=0)
        self.assertAlmostEqual(result.equity.iloc[-1], 1.)  # gap occurred before first fill
        self.assertAlmostEqual(result.qy.iloc[0], .5 / 120)

    def test_future_does_not_change_earlier_account(self):
        original = simulate_account(self.bars, self.signal, self.beta, self.index[1])
        self.bars.loc[self.index[-1], 'y_close'] *= 1.2
        modified = simulate_account(self.bars, self.signal, self.beta, self.index[1])
        pd.testing.assert_frame_equal(original.iloc[:-1], modified.iloc[:-1])

    def test_known_long_short_pnl_and_lagged_beta(self):
        self.bars.loc[self.index[1], 'y_close'] = 110.
        self.bars.loc[self.index[2]:, ['y_open', 'y_close']] = 110.
        signal = pd.Series([1, 0, 0, 0, 0], index=self.index)
        self.beta.iloc[1] = 9.  # close t=1 cannot change its opening fill
        result = simulate_account(self.bars, signal, self.beta, self.index[1], fee_bps=0, slippage_bps=0)
        self.assertAlmostEqual(result.qy.iloc[0], .005)
        self.assertAlmostEqual(result.equity.iloc[-1], 1.05)

    def test_idle_cash_and_invalid_beta(self):
        result = simulate_account(self.bars, self.signal * 0, self.beta, self.index[1])
        self.assertTrue((result.equity == 1).all())
        invalid = simulate_account(self.bars, self.signal, self.beta * np.nan, self.index[1])
        self.assertTrue((invalid.turnover == 0).all())

    def test_terminal_liquidation_and_direction_flip(self):
        signals = pd.Series([1, -1, -1, -1, -1], index=self.index)
        result = simulate_account(self.bars, signals, self.beta, self.index[1])
        self.assertEqual(result.entries.sum(), 2)
        self.assertGreater(result.turnover.iloc[1], 1.99)
        self.assertGreater(result.turnover.iloc[-1], .99)
        self.assertAlmostEqual(result.equity.iloc[-1] - 1, result.gross_pnl.sum() - result.fees.sum() - result.slippage.sum())

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            simulate_account(self.bars, self.signal, self.beta, self.index[1], fee_bps=-1)
        broken = self.bars.copy()
        broken.iloc[1, 0] = np.nan
        with self.assertRaises(ValueError):
            simulate_account(broken, self.signal, self.beta, self.index[1])

    def test_open_inventory_in_portfolio_and_overlap(self):
        frames = {'A': pd.DataFrame({'close': [100., 100., 90., 90., 80.]}, index=self.index),
                  'B': pd.DataFrame({'close': 100.}, index=self.index)}
        trade = dict(symbol='A', side='long', order_filled=True, entry_timestamp=self.index[1],
                     exit_timestamp=self.index[-1], entry_price=100., exit_price=80., exit_reason='open')
        trades = pd.DataFrame([trade, trade])
        result, summary = simulate_long_portfolio(frames, trades, fee_bps=0, slippage_bps=0)
        self.assertEqual(summary['accepted'], 1)
        self.assertEqual(summary['skipped_overlap'], 1)
        self.assertAlmostEqual(result.equity.iloc[2], .95)
        self.assertAlmostEqual(summary['net_return'], -.1)
        costly, summary = simulate_long_portfolio(frames, trades.iloc[:1], fee_bps=10, slippage_bps=0)
        expected = .5 + .5 / 1.001 * .8 * .999
        self.assertAlmostEqual(costly.equity.iloc[-1], expected)
        self.assertAlmostEqual(summary['gross_return'] - summary['costs'], summary['net_return'])


if __name__ == '__main__':
    unittest.main()
