"""Correlation-filtered relative-price divergence baseline."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .pair_reversion import position_from_zscore, simulate_pair
from .stat_arb import align_pair


@dataclass(frozen=True)
class CorrelationDivergenceConfig:
    zscore_window: int = 120
    correlation_window: int = 120
    minimum_correlation: float = 0.50
    entry_zscore: float = 2.0
    exit_zscore: float = 0.25
    stop_zscore: float = 4.0
    fee_bps_per_side: float = 5.0
    slippage_bps_per_side: float = 2.0

    @property
    def cost_per_unit_turnover(self) -> float:
        return (self.fee_bps_per_side + self.slippage_bps_per_side) / 10_000

    def validate(self) -> None:
        if min(self.zscore_window, self.correlation_window) < 3:
            raise ValueError("rolling windows must contain at least 3 bars")
        if not 0 <= self.minimum_correlation <= 1:
            raise ValueError("minimum_correlation must be between 0 and 1")
        if not 0 <= self.exit_zscore < self.entry_zscore < self.stop_zscore:
            raise ValueError("require exit_zscore < entry_zscore < stop_zscore")


def build_correlation_features(
    y: pd.DataFrame, x: pd.DataFrame, config: CorrelationDivergenceConfig
) -> pd.DataFrame:
    config.validate()
    result = align_pair(y, x)
    log_y, log_x = np.log(result["y_close"]), np.log(result["x_close"])
    result["y_return"], result["x_return"] = log_y.diff(), log_x.diff()
    result["correlation"] = (
        result["y_return"].rolling(config.correlation_window)
        .corr(result["x_return"]).shift(1)
    )
    result["beta"] = 1.0
    result["spread"] = log_y - log_x
    mean = result["spread"].rolling(config.zscore_window).mean().shift(1)
    std = result["spread"].rolling(config.zscore_window).std().shift(1)
    result["zscore"] = (result["spread"] - mean) / std.replace(0.0, np.nan)
    return result


def backtest_correlation_divergence(
    y: pd.DataFrame,
    x: pd.DataFrame,
    config: CorrelationDivergenceConfig = CorrelationDivergenceConfig(),
) -> pd.DataFrame:
    features = build_correlation_features(y, x, config)
    eligible = features["correlation"].abs() >= config.minimum_correlation
    signal = position_from_zscore(
        features["zscore"], entry=config.entry_zscore,
        exit_=config.exit_zscore, stop=config.stop_zscore, eligible=eligible,
    )
    return simulate_pair(features, signal, config.cost_per_unit_turnover)
