import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from trading_strategy.utils.crypto import load_crypto_ohlc


class CryptoTimeframeTest(unittest.TestCase):
    def setUp(self):
        timestamp = pd.date_range(
            "2025-01-01", periods=30, freq="min", tz="UTC"
        )
        self.frame = pd.DataFrame(
            {
                "timestamp": timestamp,
                "symbol": "BTCUSDT",
                "open": range(30),
                "high": range(1, 31),
                "low": range(30),
                "close": range(1, 31),
                "volume": 1.0,
            }
        )

    @patch(
        "trading_strategy.utils.crypto.read_kline_archive"
    )
    @patch(
        "trading_strategy.utils.crypto.crypto_archive_paths"
    )
    def test_resamples_minute_data_to_15_minutes(self, paths, reader):
        paths.return_value = [Path("BTCUSDT.zip")]
        reader.return_value = self.frame
        result = load_crypto_ohlc(
            Path("data/raw"),
            "BTCUSDT",
            pd.Timestamp("2025-01-01", tz="UTC"),
            pd.Timestamp("2025-01-02", tz="UTC"),
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]["open"], 0)
        self.assertEqual(result.iloc[0]["close"], 15)

    def test_rejects_timeframes_below_15_minutes(self):
        with self.assertRaises(ValueError):
            load_crypto_ohlc(
                Path("data/raw"),
                "BTCUSDT",
                pd.Timestamp("2025-01-01", tz="UTC"),
                pd.Timestamp("2025-01-02", tz="UTC"),
                "5min",
            )


if __name__ == "__main__":
    unittest.main()
