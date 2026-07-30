from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DetectorConfig:
    return_z: float = 2.5
    volume_z: float = 2.0
    range_z: float = 1.5
    directional_imbalance: float = 0.05
    cooldown_minutes: int = 30
    oi_drop_threshold: float | None = None


def detect_events(
    frame: pd.DataFrame, config: DetectorConfig = DetectorConfig()
) -> pd.DataFrame:
    required = {
        "timestamp",
        "symbol",
        "close",
        "direction",
        "return_z",
        "volume_z",
        "range_z",
        "directional_imbalance",
        "efficiency_ratio",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing feature columns: {sorted(missing)}")

    candidate = (
        (frame["return_z"].abs() >= config.return_z)
        & (frame["volume_z"] >= config.volume_z)
        & (frame["range_z"] >= config.range_z)
        & (frame["directional_imbalance"] >= config.directional_imbalance)
        & frame["direction"].ne(0)
    )
    if config.oi_drop_threshold is not None:
        if "oi_change_15m" not in frame:
            raise ValueError("OI filter requested but open-interest data is unavailable")
        candidate &= frame["oi_change_15m"] <= config.oi_drop_threshold
    indices: list[int] = []
    last_event: pd.Timestamp | None = None
    cooldown = pd.Timedelta(minutes=config.cooldown_minutes)
    for idx in frame.index[candidate]:
        timestamp = frame.at[idx, "timestamp"]
        if last_event is None or timestamp - last_event >= cooldown:
            indices.append(idx)
            last_event = timestamp

    columns = [
        "timestamp",
        "symbol",
        "close",
        "direction",
        "return_z",
        "volume_z",
        "range_z",
        "directional_imbalance",
        "efficiency_ratio",
    ]
    columns.extend(
        column
        for column in ("open_interest", "oi_change_15m", "oi_change_z")
        if column in frame
    )
    events = frame.loc[indices, columns].copy()
    events.insert(0, "event_id", np.arange(len(events), dtype=int))
    return events.reset_index(drop=True)


def attach_forward_returns(
    frame: pd.DataFrame,
    events: pd.DataFrame,
    horizons: tuple[int, ...] = (1, 5, 15, 30),
) -> pd.DataFrame:
    result = events.copy()
    close = frame.set_index("timestamp")["close"]
    for horizon in horizons:
        future = close.shift(-horizon)
        raw_return = future.div(close).sub(1)
        result[f"raw_return_{horizon}m"] = result["timestamp"].map(raw_return)
        result[f"continuation_{horizon}m"] = (
            result[f"raw_return_{horizon}m"] * result["direction"]
        )
        result[f"reversal_{horizon}m"] = -result[f"continuation_{horizon}m"]
    return result
