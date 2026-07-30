from __future__ import annotations

import numpy as np
import pandas as pd


def make_synthetic_klines(rows: int = 10_000, seed: int = 7) -> pd.DataFrame:
    """Create deterministic data for an offline smoke test, not for research."""
    rng = np.random.default_rng(seed)
    timestamp = pd.date_range("2025-01-01", periods=rows, freq="min", tz="UTC")
    returns = rng.normal(0, 0.00045, rows)
    volume = rng.lognormal(8, 0.5, rows)
    for start, sign in [(1500, -1), (4100, 1), (7200, -1), (8900, 1)]:
        if start + 8 > rows:
            continue
        returns[start : start + 5] += sign * np.array(
            [0.002, 0.003, 0.004, 0.002, 0.001]
        )
        volume[start : start + 8] *= np.array([4, 7, 12, 10, 8, 6, 4, 2])
    close = 50_000 * np.exp(np.cumsum(returns))
    open_ = np.r_[close[0], close[:-1]]
    spread = np.abs(rng.normal(0.0003, 0.0001, rows))
    high = np.maximum(open_, close) * (1 + spread)
    low = np.minimum(open_, close) * (1 - spread)
    base_volume = volume / close
    imbalance = np.clip(0.5 + 40 * returns + rng.normal(0, 0.08, rows), 0.01, 0.99)
    return pd.DataFrame(
        {
            "timestamp": timestamp,
            "symbol": "SYNTHUSDT",
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": base_volume,
            "quote_volume": volume,
            "trades": rng.integers(50, 500, rows),
            "taker_buy_volume": base_volume * imbalance,
            "taker_buy_quote_volume": volume * imbalance,
        }
    )
