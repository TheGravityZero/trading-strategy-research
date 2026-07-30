"""Reusable Binance OHLC loading utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..data import read_kline_archive


DEFAULT_CRYPTO_SYMBOLS = [
    "HYPEUSDT",
    "BTCUSDT",
    "SOLUSDT",
    "ETHUSDT",
]


def crypto_archive_paths(raw_dir: Path, symbol: str) -> list[Path]:
    """Prefer cached 15m+ archives, with legacy 1m data as a fallback."""
    for interval in ("15m", "30m", "1h", "4h", "1d", "1m"):
        paths = sorted((raw_dir / symbol / interval).glob("**/*.zip"))
        if paths:
            return paths
    return []


def load_crypto_ohlc(
    raw_dir: Path,
    symbol: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    interval: str = "15min",
) -> pd.DataFrame:
    """Load Binance klines and aggregate them to an interval of at least 15m."""
    offset = pd.tseries.frequencies.to_offset(interval)
    if pd.Timedelta(offset) < pd.Timedelta(minutes=15):
        raise ValueError("Crypto strategy interval must be at least 15 minutes")
    paths = crypto_archive_paths(raw_dir, symbol)
    if not paths:
        raise FileNotFoundError(f"No kline archives for {symbol}")
    frame = pd.concat(
        [read_kline_archive(path, symbol) for path in paths],
        ignore_index=True,
    )
    frame = frame[
        (frame["timestamp"] >= start) & (frame["timestamp"] < end)
    ].sort_values("timestamp")
    return (
        frame.set_index("timestamp")
        .resample(interval)
        .agg(
            symbol=("symbol", "first"),
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )
