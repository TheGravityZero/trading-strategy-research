"""Standalone trading strategies."""

from .ath_short import (
    AthShortConfig,
    backtest_ath_short,
    run_ath_short_equities,
    run_ath_short_frames,
)
from .ath_retest_volume_short import (
    AthRetestVolumeConfig,
    backtest_ath_retest_volume,
    run_ath_retest_equities,
    run_ath_retest_frames,
)
from .defended_pivot_long import (
    DefendedPivotConfig,
    backtest_defended_pivot,
    run_defended_pivot_equities,
    run_defended_pivot_frames,
)
from .weekly_pivot_limit import (
    WeeklyPivotConfig,
    backtest_weekly_pivot,
    run_weekly_pivot_study,
)
from .stat_arb import StatArbConfig, backtest_stat_arb, build_pair_features

from .mean_reversion import MeanReversionConfig, backtest_mean_reversion

__all__ = [
    "MeanReversionConfig",
    "backtest_mean_reversion",
    "AthShortConfig",
    "backtest_ath_short",
    "run_ath_short_equities",
    "run_ath_short_frames",
    "AthRetestVolumeConfig",
    "backtest_ath_retest_volume",
    "run_ath_retest_equities",
    "run_ath_retest_frames",
    "DefendedPivotConfig",
    "backtest_defended_pivot",
    "run_defended_pivot_equities",
    "run_defended_pivot_frames",
    "WeeklyPivotConfig",
    "backtest_weekly_pivot",
    "run_weekly_pivot_study",
    "StatArbConfig",
    "backtest_stat_arb",
    "build_pair_features",
]
