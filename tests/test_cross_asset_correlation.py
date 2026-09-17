import unittest

import numpy as np
import pandas as pd

from trading_strategy.analysis.cross_asset_correlation import (
    absolute_return_correlation,
    downside_correlation,
    lag_correlation,
    pearson_correlation,
    rolling_pearson,
    spearman_correlation,
)


class CrossAssetCorrelationTest(unittest.TestCase):
    def setUp(self):
        self.returns = pd.DataFrame(
            {
                "BTC": [1, 2, -1, -2, 1, 2],
                "ETH": [2, 4, -2, -4, 2, 4],
                "SPY": [1, 2, -1, -2, 1, 2],
                "NVDA": [-2, -1, 2, 1, -2, -1],
            },
            index=pd.date_range("2025-01-01", periods=6, freq="h", tz="UTC"),
        )
        self.crypto, self.stocks = ["BTC", "ETH"], ["SPY", "NVDA"]

    def test_static_estimators_return_cross_asset_block(self):
        for estimator in (pearson_correlation, spearman_correlation):
            matrix = estimator(self.returns, self.crypto, self.stocks)
            self.assertEqual(matrix.shape, (2, 2))
            self.assertAlmostEqual(matrix.loc["BTC", "SPY"], 1.0)

    def test_absolute_and_downside_are_separate_estimators(self):
        absolute = absolute_return_correlation(self.returns, self.crypto, self.stocks)
        downside = downside_correlation(self.returns, self.crypto, self.stocks)
        self.assertAlmostEqual(absolute.loc["BTC", "SPY"], 1.0)
        self.assertAlmostEqual(downside.loc["BTC", "SPY"], 1.0)

    def test_rolling_output_is_tidy(self):
        result = rolling_pearson(self.returns, self.crypto, self.stocks, window=3)
        self.assertEqual(set(result.columns), {"timestamp", "crypto", "stock", "correlation"})
        self.assertEqual(len(result), 16)

    def test_lags_do_not_cross_trading_dates(self):
        dates = pd.Series(
            [pd.Timestamp("2025-01-01").date()] * 3
            + [pd.Timestamp("2025-01-02").date()] * 3,
            index=self.returns.index,
        )
        result = lag_correlation(
            self.returns, dates, ["BTC"], ["SPY"], range(-1, 2)
        )
        self.assertEqual(result.loc[result.lag_hours == 1, "observations"].iloc[0], 4)


if __name__ == "__main__":
    unittest.main()
