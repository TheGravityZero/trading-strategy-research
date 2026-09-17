"""Rolling-regression spread baseline without a correlation filter."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .pair_reversion import position_from_zscore, simulate_pair
from .stat_arb import StatArbConfig, build_pair_features


@dataclass(frozen=True)
class RegressionSpreadConfig:
    regression_window: int = 240
    zscore_window: int = 120
    entry_zscore: float = 2.0
    exit_zscore: float = 0.25
    stop_zscore: float = 4.0
    fee_bps_per_side: float = 5.0
    slippage_bps_per_side: float = 2.0

    @property
    def cost_per_unit_turnover(self) -> float:
        return (self.fee_bps_per_side + self.slippage_bps_per_side) / 10_000

    def validate(self) -> None:
        if min(self.regression_window, self.zscore_window) < 3:
            raise ValueError("rolling windows must contain at least 3 bars")
        if not 0 <= self.exit_zscore < self.entry_zscore < self.stop_zscore:
            raise ValueError("require exit_zscore < entry_zscore < stop_zscore")


def build_regression_features(
    y: pd.DataFrame, x: pd.DataFrame, config: RegressionSpreadConfig
) -> pd.DataFrame:
    config.validate()
    internal = StatArbConfig(
        regression_window=config.regression_window,
        zscore_window=config.zscore_window,
        correlation_window=3,
        minimum_correlation=0.0,
        entry_zscore=config.entry_zscore,
        exit_zscore=config.exit_zscore,
        stop_zscore=config.stop_zscore,
        fee_bps_per_side=config.fee_bps_per_side,
        slippage_bps_per_side=config.slippage_bps_per_side,
    )
    return build_pair_features(y, x, internal)


def backtest_regression_spread(
    y: pd.DataFrame,
    x: pd.DataFrame,
    config: RegressionSpreadConfig = RegressionSpreadConfig(),
) -> pd.DataFrame:
    features = build_regression_features(y, x, config)
    signal = position_from_zscore(
        features["zscore"], entry=config.entry_zscore,
        exit_=config.exit_zscore, stop=config.stop_zscore,
    )
    return simulate_pair(features, signal, config.cost_per_unit_turnover)
