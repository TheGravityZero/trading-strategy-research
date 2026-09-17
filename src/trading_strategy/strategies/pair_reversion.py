"""Shared causal simulation helpers for pair mean-reversion baselines."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def position_from_zscore(
    zscore: pd.Series,
    *,
    entry: float,
    exit_: float,
    stop: float,
    eligible: pd.Series | None = None,
) -> pd.Series:
    """Create a stateful position using information on the current bar only."""
    allowed = eligible if eligible is not None else pd.Series(True, index=zscore.index)
    position = 0
    values: list[int] = []
    for z, can_enter in zip(zscore, allowed):
        valid = pd.notna(z)
        if position and (not valid or abs(z) <= exit_ or abs(z) >= stop):
            position = 0
        if position == 0 and valid and bool(can_enter):
            if entry <= z < stop:
                position = -1
            elif -stop < z <= -entry:
                position = 1
        values.append(position)
    return pd.Series(values, index=zscore.index, dtype="int8")


def simulate_pair(
    features: pd.DataFrame,
    signal_position: pd.Series,
    cost_per_unit_turnover: float,
) -> pd.DataFrame:
    """Apply close-bar signals to the following bar's normalized pair return."""
    result = features.copy()
    result["signal_position"] = signal_position
    result["position"] = signal_position.shift(1).fillna(0).astype("int8")
    gross_exposure = 1.0 + result["beta"].abs()
    result["hedged_return"] = (
        result["y_return"] - result["beta"] * result["x_return"]
    ) / gross_exposure
    result["turnover"] = result["position"].diff().abs().fillna(
        result["position"].abs()
    )
    result["strategy_return"] = (
        result["position"] * result["hedged_return"].fillna(0.0)
        - result["turnover"] * cost_per_unit_turnover
    )
    result["equity"] = np.exp(result["strategy_return"].cumsum())
    return result


def summarize_pair_backtest(result: pd.DataFrame) -> dict[str, float | int]:
    returns = result["strategy_return"].fillna(0.0)
    equity = result["equity"]
    drawdown = equity / equity.cummax() - 1.0
    entries = (
        (result["position"] != 0)
        & (result["position"].shift(1).fillna(0) == 0)
    ).sum()
    return {
        "bars": int(len(result)),
        "trades": int(entries),
        "total_return": float(equity.iloc[-1] - 1.0) if len(equity) else 0.0,
        "mean_bar_return": float(returns.mean()),
        "bar_sharpe": float(returns.mean() / returns.std())
        if returns.std() > 0
        else 0.0,
        "maximum_drawdown": float(drawdown.min()) if len(drawdown) else 0.0,
        "turnover": float(result["turnover"].sum()),
    }


def write_pair_results(
    result: pd.DataFrame,
    output_dir: Path,
    config: Any,
    *,
    strategy: str,
    y_symbol: str,
    x_symbol: str,
    interval: str,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_dir / "bars.csv", index=False)
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strategy": strategy,
        "pair": f"{y_symbol}/{x_symbol}",
        "interval": interval,
        "start": result["timestamp"].min().isoformat() if len(result) else None,
        "end": result["timestamp"].max().isoformat() if len(result) else None,
        "config": asdict(config),
        "summary": summarize_pair_backtest(result),
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata
