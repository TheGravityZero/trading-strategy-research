from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class BacktestConfig:
    continuation_horizon: int = 5
    reversal_horizon: int = 15
    exhaustion_threshold: float = 0.65
    fee_bps_per_side: float = 5.0
    slippage_bps_per_side: float = 2.0
    strategy_mode: str = "auto"


def run_event_backtest(
    events: pd.DataFrame, config: BacktestConfig = BacktestConfig()
) -> pd.DataFrame:
    result = events.copy()
    if config.strategy_mode not in {"auto", "continuation", "reversal"}:
        raise ValueError(f"Unknown strategy mode: {config.strategy_mode}")
    if config.strategy_mode == "reversal":
        exhausted = pd.Series(True, index=result.index)
    elif config.strategy_mode == "continuation":
        exhausted = pd.Series(False, index=result.index)
    else:
        exhausted = result["efficiency_ratio"] <= config.exhaustion_threshold
    result["strategy"] = exhausted.map({True: "reversal", False: "continuation"})
    continuation = result[f"continuation_{config.continuation_horizon}m"]
    reversal = result[f"reversal_{config.reversal_horizon}m"]
    result["gross_return"] = continuation.where(~exhausted, reversal)
    round_trip_cost = 2 * (
        config.fee_bps_per_side + config.slippage_bps_per_side
    ) / 10_000
    result["cost"] = round_trip_cost
    result["net_return"] = result["gross_return"] - result["cost"]
    result["equity"] = (1 + result["net_return"].fillna(0)).cumprod()
    return result


def summarize(trades: pd.DataFrame) -> dict[str, float | int]:
    valid = trades.dropna(subset=["net_return"])
    if valid.empty:
        return {
            "trades": 0,
            "net_return": 0.0,
            "mean_trade": 0.0,
            "hit_rate": 0.0,
            "max_drawdown": 0.0,
        }
    equity = (1 + valid["net_return"]).cumprod()
    drawdown = equity.div(equity.cummax()).sub(1)
    return {
        "trades": len(valid),
        "net_return": float(equity.iloc[-1] - 1),
        "mean_trade": float(valid["net_return"].mean()),
        "hit_rate": float((valid["net_return"] > 0).mean()),
        "max_drawdown": float(drawdown.min()),
    }
