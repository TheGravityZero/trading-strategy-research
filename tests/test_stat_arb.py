import unittest

import numpy as np
import pandas as pd

from trading_strategy.strategies.stat_arb import (
    StatArbConfig,
    backtest_stat_arb,
    build_pair_features,
)
from trading_strategy.strategies.correlation_divergence import (
    CorrelationDivergenceConfig,
    backtest_correlation_divergence,
    build_correlation_features,
)
from trading_strategy.strategies.regression_spread import (
    RegressionSpreadConfig,
    backtest_regression_spread,
)


def frame(symbol: str, close: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-01", periods=len(close), freq="h", tz="UTC"),
            "symbol": symbol,
            "close": close,
        }
    )


class StatArbTest(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(7)
        x_log = 4.0 + np.cumsum(rng.normal(0, 0.01, 180))
        residual = rng.normal(0, 0.005, 180)
        residual[100] = 0.08
        self.x = frame("BTCUSDT", np.exp(x_log))
        self.y = frame("ETHUSDT", np.exp(0.4 + 1.2 * x_log + residual))
        self.config = StatArbConfig(
            regression_window=30,
            zscore_window=20,
            correlation_window=20,
            minimum_correlation=0.0,
            entry_zscore=2.0,
            exit_zscore=0.25,
            stop_zscore=20.0,
            fee_bps_per_side=0,
            slippage_bps_per_side=0,
        )

    def test_rolling_coefficients_do_not_use_current_bar(self):
        before = build_pair_features(self.y, self.x, self.config)
        changed = self.y.copy()
        changed.loc[100, "close"] *= 2
        after = build_pair_features(changed, self.x, self.config)
        self.assertAlmostEqual(before.loc[100, "beta"], after.loc[100, "beta"])
        self.assertNotAlmostEqual(before.loc[101, "beta"], after.loc[101, "beta"])

    def test_positive_spread_opens_short_on_following_bar(self):
        result = backtest_stat_arb(self.y, self.x, self.config)
        self.assertEqual(result.loc[100, "signal_position"], -1)
        self.assertEqual(result.loc[100, "position"], 0)
        self.assertEqual(result.loc[101, "position"], -1)

    def test_cost_is_charged_on_position_turnover(self):
        costly = StatArbConfig(**{
            **self.config.__dict__, "fee_bps_per_side": 5, "slippage_bps_per_side": 2
        })
        result = backtest_stat_arb(self.y, self.x, costly)
        active = result[result["turnover"] > 0]
        self.assertTrue(len(active) > 0)
        row = active.iloc[0]
        expected = row.position * row.hedged_return - row.turnover * 0.0007
        self.assertAlmostEqual(row.strategy_return, expected)

    def test_correlation_baseline_uses_equal_weight_spread(self):
        config = CorrelationDivergenceConfig(
            zscore_window=20, correlation_window=20,
            minimum_correlation=0, stop_zscore=20,
            fee_bps_per_side=0, slippage_bps_per_side=0,
        )
        result = build_correlation_features(self.y, self.x, config)
        self.assertTrue((result["beta"] == 1.0).all())
        changed = self.y.copy()
        changed.loc[100, "close"] *= 2
        after = build_correlation_features(changed, self.x, config)
        self.assertAlmostEqual(result.loc[100, "correlation"], after.loc[100, "correlation"])

    def test_regression_baseline_does_not_require_correlation(self):
        config = RegressionSpreadConfig(
            regression_window=30, zscore_window=20,
            entry_zscore=2, exit_zscore=0.25, stop_zscore=20,
            fee_bps_per_side=0, slippage_bps_per_side=0,
        )
        result = backtest_regression_spread(self.y, self.x, config)
        self.assertEqual(result.loc[100, "signal_position"], -1)

    def test_correlation_baseline_executes_on_following_bar(self):
        config = CorrelationDivergenceConfig(
            zscore_window=20, correlation_window=20,
            minimum_correlation=0, entry_zscore=2,
            exit_zscore=0.25, stop_zscore=20,
            fee_bps_per_side=0, slippage_bps_per_side=0,
        )
        result = backtest_correlation_divergence(self.y, self.x, config)
        entries = result.index[result["signal_position"].ne(0)]
        first = int(entries[0])
        self.assertEqual(result.loc[first, "position"], 0)
        self.assertEqual(result.loc[first + 1, "position"], result.loc[first, "signal_position"])


if __name__ == "__main__":
    unittest.main()
