"""Causal correlation/regression baseline for crypto pairs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class StatArbConfig:
    regression_window: int = 240
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
        if min(self.regression_window, self.zscore_window, self.correlation_window) < 3:
            raise ValueError("rolling windows must contain at least 3 bars")
        if not 0 <= self.minimum_correlation <= 1:
            raise ValueError("minimum_correlation must be between 0 and 1")
        if not 0 <= self.exit_zscore < self.entry_zscore < self.stop_zscore:
            raise ValueError("require exit_zscore < entry_zscore < stop_zscore")


def align_pair(y: pd.DataFrame, x: pd.DataFrame) -> pd.DataFrame:
    """Inner-align two OHLC frames and retain close prices."""
    required = {"timestamp", "close"}
    for name, frame in (("y", y), ("x", x)):
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{name} frame is missing columns: {sorted(missing)}")
    pair = (
        y[["timestamp", "close"]]
        .rename(columns={"close": "y_close"})
        .merge(
            x[["timestamp", "close"]].rename(columns={"close": "x_close"}),
            on="timestamp",
            how="inner",
            validate="one_to_one",
        )
        .sort_values("timestamp")
        .drop_duplicates("timestamp")
        .reset_index(drop=True)
    )
    if pair.empty or (pair[["y_close", "x_close"]] <= 0).any().any():
        raise ValueError("aligned close prices must be non-empty and positive")
    return pair


def _rolling_ols(log_y: pd.Series, log_x: pd.Series, window: int) -> tuple[pd.Series, pd.Series]:
    """OLS coefficients known before each current bar (no look-ahead)."""
    mean_x = log_x.rolling(window).mean().shift(1)
    mean_y = log_y.rolling(window).mean().shift(1)
    covariance = log_x.rolling(window).cov(log_y).shift(1)
    variance = log_x.rolling(window).var().shift(1)
    beta = covariance / variance.replace(0.0, np.nan)
    intercept = mean_y - beta * mean_x
    return intercept, beta


def build_pair_features(
    y: pd.DataFrame, x: pd.DataFrame, config: StatArbConfig
) -> pd.DataFrame:
    """Build causal rolling correlation, hedge ratio, spread, and z-score."""
    config.validate()
    result = align_pair(y, x)
    log_y = np.log(result["y_close"])
    log_x = np.log(result["x_close"])
    result["y_return"] = log_y.diff()
    result["x_return"] = log_x.diff()
    result["correlation"] = (
        result["y_return"]
        .rolling(config.correlation_window)
        .corr(result["x_return"])
        .shift(1)
    )
    result["intercept"], result["beta"] = _rolling_ols(
        log_y, log_x, config.regression_window
    )
    result["spread"] = log_y - result["intercept"] - result["beta"] * log_x
    spread_mean = result["spread"].rolling(config.zscore_window).mean().shift(1)
    spread_std = result["spread"].rolling(config.zscore_window).std().shift(1)
    result["zscore"] = (result["spread"] - spread_mean) / spread_std.replace(0.0, np.nan)
    return result


def _positions(features: pd.DataFrame, config: StatArbConfig) -> pd.Series:
    position = 0
    values: list[int] = []
    for row in features.itertuples():
        zscore, correlation = row.zscore, row.correlation
        valid = pd.notna(zscore) and pd.notna(correlation)
        if position and (not valid or abs(zscore) <= config.exit_zscore or abs(zscore) >= config.stop_zscore):
            position = 0
        if position == 0 and valid and abs(correlation) >= config.minimum_correlation:
            if config.entry_zscore <= zscore < config.stop_zscore:
                position = -1  # y is rich: short y, long beta*x
            elif -config.stop_zscore < zscore <= -config.entry_zscore:
                position = 1
        values.append(position)
    return pd.Series(values, index=features.index, dtype="int8")


def backtest_stat_arb(
    y: pd.DataFrame, x: pd.DataFrame, config: StatArbConfig = StatArbConfig()
) -> pd.DataFrame:
    """Backtest signals at bar close and apply them to the following return."""
    result = build_pair_features(y, x, config)
    result["signal_position"] = _positions(result, config)
    result["position"] = result["signal_position"].shift(1).fillna(0).astype("int8")
    gross = 1.0 + result["beta"].abs()
    result["hedged_return"] = (
        result["y_return"] - result["beta"] * result["x_return"]
    ) / gross
    result["turnover"] = result["position"].diff().abs().fillna(result["position"].abs())
    result["strategy_return"] = (
        result["position"] * result["hedged_return"].fillna(0.0)
        - result["turnover"] * config.cost_per_unit_turnover
    )
    result["equity"] = np.exp(result["strategy_return"].cumsum())
    return result


def summarize_backtest(result: pd.DataFrame) -> dict[str, float | int]:
    returns = result["strategy_return"].fillna(0.0)
    equity = result["equity"]
    drawdown = equity / equity.cummax() - 1.0
    entries = ((result["position"] != 0) & (result["position"].shift(1).fillna(0) == 0)).sum()
    return {
        "bars": int(len(result)),
        "trades": int(entries),
        "total_return": float(equity.iloc[-1] - 1.0) if len(equity) else 0.0,
        "mean_bar_return": float(returns.mean()),
        "bar_sharpe": float(returns.mean() / returns.std()) if returns.std() > 0 else 0.0,
        "maximum_drawdown": float(drawdown.min()) if len(drawdown) else 0.0,
        "turnover": float(result["turnover"].sum()),
    }


def write_stat_arb_results(
    result: pd.DataFrame,
    output_dir: Path,
    config: StatArbConfig,
    y_symbol: str,
    x_symbol: str,
    interval: str,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_dir / "bars.csv", index=False)
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strategy": "RollingRegressionStatArb",
        "pair": f"{y_symbol}/{x_symbol}",
        "interval": interval,
        "start": result["timestamp"].min().isoformat() if len(result) else None,
        "end": result["timestamp"].max().isoformat() if len(result) else None,
        "config": asdict(config),
        "summary": summarize_backtest(result),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
