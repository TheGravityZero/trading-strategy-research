from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_zscore(series: pd.Series, window: int, min_periods: int) -> pd.Series:
    mean = series.rolling(window, min_periods=min_periods).mean().shift(1)
    std = series.rolling(window, min_periods=min_periods).std(ddof=0).shift(1)
    return (series - mean) / std.replace(0.0, np.nan)


def build_features(
    frame: pd.DataFrame,
    *,
    lookback: int = 360,
    min_periods: int = 120,
) -> pd.DataFrame:
    """Build strictly backward-looking features from one-minute futures klines."""
    result = frame.sort_values("timestamp").copy()
    result["return_1m"] = np.log(result["close"]).diff()
    result["return_5m"] = np.log(result["close"]).diff(5)
    result["direction"] = np.sign(result["return_5m"])
    result["realized_vol_30m"] = (
        result["return_1m"].rolling(30, min_periods=20).std(ddof=0).shift(1)
    )
    result["return_z"] = rolling_zscore(
        result["return_5m"], lookback, min_periods
    )
    result["volume_z"] = rolling_zscore(
        np.log1p(result["quote_volume"]), lookback, min_periods
    )
    taker_sell = (result["volume"] - result["taker_buy_volume"]).clip(lower=0)
    result["taker_imbalance"] = (
        (result["taker_buy_volume"] - taker_sell)
        / result["volume"].replace(0.0, np.nan)
    ).clip(-1, 1)
    result["directional_imbalance"] = (
        result["direction"] * result["taker_imbalance"]
    )
    result["range_bps"] = (
        10_000 * (result["high"] - result["low"]) / result["close"]
    )
    result["range_z"] = rolling_zscore(
        np.log1p(result["range_bps"]), lookback, min_periods
    )

    # Proxy for exhaustion: extreme activity whose marginal directional price
    # response is fading. Shifted rolling max makes the comparison causal.
    result["impulse_efficiency"] = (
        result["return_1m"].abs() / (np.log1p(result["quote_volume"]).abs() + 1e-9)
    )
    prior_efficiency = (
        result["impulse_efficiency"].rolling(5, min_periods=2).max().shift(1)
    )
    result["efficiency_ratio"] = (
        result["impulse_efficiency"] / prior_efficiency.replace(0.0, np.nan)
    )
    if "sum_open_interest" in result:
        result["open_interest"] = result["sum_open_interest"].ffill()
        result["oi_change_15m"] = result["open_interest"].pct_change(15)
        result["oi_change_z"] = rolling_zscore(
            result["oi_change_15m"], lookback, min_periods
        )
    return result
