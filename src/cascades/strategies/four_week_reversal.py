from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..hypotheses import cluster_bootstrap_ci
from ..utils.crypto import load_crypto_symbol


@dataclass(frozen=True)
class FourWeekReversalConfig:
    """Causal four-week extreme sweep/reclaim strategy."""

    lookback_weeks: int = 4
    entry_mode: str = "offset_limit"
    entry_offset_percent: float = 4.0
    entry_window_minutes: int = 60
    touch_zone_bps: float = 10.0
    max_sweep_bps: float = 100.0
    reclaim_minutes: int = 5
    trend_lookback_minutes: int = 240
    minimum_aligned_trend_bps: float = 10.0
    stop_buffer_bps: float = 5.0
    fee_bps_per_side: float = 5.0
    slippage_bps_per_side: float = 2.0
    horizons: tuple[int, ...] = (15, 30, 60)

    @property
    def round_trip_cost(self) -> float:
        return 2 * (self.fee_bps_per_side + self.slippage_bps_per_side) / 10_000


def add_four_week_levels(
    frame: pd.DataFrame, lookback_weeks: int = 4
) -> pd.DataFrame:
    """Attach levels from the four completed Monday-Sunday UTC weeks."""
    result = frame.sort_values("timestamp").copy()
    week_start = (
        result["timestamp"].dt.normalize()
        - pd.to_timedelta(result["timestamp"].dt.dayofweek, unit="D")
    )
    result["week_start"] = week_start
    weekly = (
        result.groupby("week_start", sort=True)
        .agg(week_high=("high", "max"), week_low=("low", "min"))
    )
    weekly["four_week_high"] = (
        weekly["week_high"].rolling(lookback_weeks).max().shift(1)
    )
    weekly["four_week_low"] = (
        weekly["week_low"].rolling(lookback_weeks).min().shift(1)
    )
    result = result.merge(
        weekly[["four_week_high", "four_week_low"]],
        left_on="week_start",
        right_index=True,
        how="left",
    )
    log_close = np.log(result["close"])
    result["trend_return"] = log_close.diff(240)
    return result


def _classify_event(
    frame: pd.DataFrame,
    position: int,
    event: pd.Series,
    config: FourWeekReversalConfig,
) -> dict:
    row = frame.iloc[position]
    direction = float(event["direction"])
    level = row["four_week_low"] if direction < 0 else row["four_week_high"]
    result = {
        "weekly_level": level,
        "touch": False,
        "sweep": False,
        "reclaimed": False,
        "eligible": False,
    }
    if not np.isfinite(level):
        return result

    aligned_trend_bps = direction * row["trend_return"] * 10_000
    result["aligned_trend_bps"] = aligned_trend_bps
    result["trend_confirmed"] = (
        aligned_trend_bps >= config.minimum_aligned_trend_bps
    )

    if direction < 0:
        distance_bps = 10_000 * (row["low"] - level) / level
        touch = distance_bps <= config.touch_zone_bps
        sweep_bps = max(0.0, -distance_bps)
    else:
        distance_bps = 10_000 * (level - row["high"]) / level
        touch = distance_bps <= config.touch_zone_bps
        sweep_bps = max(0.0, -distance_bps)
    result["distance_to_level_bps"] = distance_bps
    result["sweep_bps"] = sweep_bps
    result["touch"] = bool(touch)
    result["sweep"] = bool(sweep_bps > 0)
    if not touch:
        return result

    if config.entry_mode == "offset_limit":
        target = (
            level * (1 - config.entry_offset_percent / 100)
            if direction < 0
            else level * (1 + config.entry_offset_percent / 100)
        )
        result["limit_price"] = target
        search = frame.iloc[position : position + config.entry_window_minutes + 1]
        for delay, (_, candidate) in enumerate(search.iterrows()):
            filled = (
                candidate["low"] <= target
                if direction < 0
                else candidate["high"] >= target
            )
            if filled:
                result.update(
                    {
                        "entry_timestamp": candidate["timestamp"],
                        "entry_price": target,
                        "entry_delay_minutes": delay,
                        "limit_filled": True,
                        "eligible": bool(result["trend_confirmed"]),
                    }
                )
                entry_position = position + delay
                extreme = (
                    frame.iloc[position : entry_position + 1]["low"].min()
                    if direction < 0
                    else frame.iloc[position : entry_position + 1]["high"].max()
                )
                result["event_extreme"] = extreme
                result["stop_price"] = (
                    extreme * (1 - config.stop_buffer_bps / 10_000)
                    if direction < 0
                    else extreme * (1 + config.stop_buffer_bps / 10_000)
                )
                _attach_returns(
                    result, frame, entry_position, target, direction, config
                )
                break
        return result

    if config.entry_mode != "reclaim":
        raise ValueError(f"Unknown entry mode: {config.entry_mode}")
    if sweep_bps > config.max_sweep_bps:
        return result
    confirmation = frame.iloc[position + 1 : position + config.reclaim_minutes + 1]
    for delay, (_, candidate) in enumerate(confirmation.iterrows(), start=1):
        reclaimed = (
            candidate["close"] > level
            if direction < 0
            else candidate["close"] < level
        )
        if reclaimed:
            result.update(
                {
                    "reclaimed": True,
                    "reclaim_delay_minutes": delay,
                    "entry_timestamp": candidate["timestamp"],
                    "entry_price": candidate["close"],
                    "eligible": bool(result["trend_confirmed"]),
                }
            )
            entry_position = position + delay
            extreme = (
                frame.iloc[position : entry_position + 1]["low"].min()
                if direction < 0
                else frame.iloc[position : entry_position + 1]["high"].max()
            )
            result["event_extreme"] = extreme
            result["stop_price"] = (
                extreme * (1 - config.stop_buffer_bps / 10_000)
                if direction < 0
                else extreme * (1 + config.stop_buffer_bps / 10_000)
            )
            _attach_returns(
                result,
                frame,
                entry_position,
                candidate["close"],
                direction,
                config,
            )
            break
    return result


def _attach_returns(
    result: dict,
    frame: pd.DataFrame,
    entry_position: int,
    entry_price: float,
    direction: float,
    config: FourWeekReversalConfig,
) -> None:
    for horizon in config.horizons:
        future_position = entry_position + horizon
        if future_position < len(frame):
            future = frame.iloc[future_position]["close"]
            gross = -direction * (future / entry_price - 1)
            result[f"gross_return_{horizon}m"] = gross
            result[f"net_return_{horizon}m"] = gross - config.round_trip_cost
        else:
            result[f"gross_return_{horizon}m"] = np.nan
            result[f"net_return_{horizon}m"] = np.nan


def generate_four_week_trades(
    frame: pd.DataFrame,
    events: pd.DataFrame,
    config: FourWeekReversalConfig = FourWeekReversalConfig(),
) -> pd.DataFrame:
    enriched = add_four_week_levels(frame, config.lookback_weeks)
    positions = pd.Series(np.arange(len(enriched)), index=enriched["timestamp"])
    records = []
    for _, event in events.iterrows():
        position = positions.get(event["timestamp"])
        if position is None:
            continue
        record = event.to_dict()
        record.update(_classify_event(enriched, int(position), event, config))
        records.append(record)
    return pd.DataFrame(records)


def _summary(trades: pd.DataFrame, config: FourWeekReversalConfig) -> pd.DataFrame:
    rows = []
    eligible = trades[trades["eligible"].fillna(False)]
    for split in ("research", "validation", "test"):
        split_frame = eligible[eligible["split"] == split]
        if split_frame.empty:
            continue
        for horizon in config.horizons:
            gross_column = f"gross_return_{horizon}m"
            net_column = f"net_return_{horizon}m"
            valid = split_frame.dropna(subset=[gross_column])
            low, high = cluster_bootstrap_ci(valid, gross_column)
            rows.append(
                {
                    "split": split,
                    "horizon_minutes": horizon,
                    "events": len(valid),
                    "clusters": valid["cluster_id"].nunique(),
                    "mean_gross_bps": valid[gross_column].mean() * 10_000,
                    "median_gross_bps": valid[gross_column].median() * 10_000,
                    "mean_net_bps": valid[net_column].mean() * 10_000,
                    "beats_cost_rate": (
                        valid[gross_column] > config.round_trip_cost
                    ).mean(),
                    "ci_low_bps": low * 10_000,
                    "ci_high_bps": high * 10_000,
                }
            )
    return pd.DataFrame(rows)


def run_four_week_strategy(
    raw_dir: Path,
    events_path: Path,
    output_dir: Path,
    *,
    include_test: bool = False,
    config: FourWeekReversalConfig = FourWeekReversalConfig(),
    symbols: list[str] | None = None,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(events_path, parse_dates=["timestamp"])
    if symbols is not None:
        events = events[events["symbol"].isin(symbols)]
    allowed = ["research", "validation"] + (["test"] if include_test else [])
    events = events[events["split"].isin(allowed)]
    start = pd.Timestamp("2025-07-01", tz="UTC")
    end = pd.Timestamp("2026-07-01", tz="UTC")
    frames = []
    for symbol, symbol_events in events.groupby("symbol"):
        frame, _ = load_crypto_symbol(raw_dir, symbol, start, end)
        result = generate_four_week_trades(frame, symbol_events, config)
        frames.append(result)
        print(
            f"{symbol}: {int(result['eligible'].fillna(False).sum())} eligible "
            f"of {len(result)} events",
            flush=True,
        )
    trades = pd.concat(frames, ignore_index=True)
    summary = _summary(trades, config)
    trades.to_csv(output_dir / "events_and_trades.csv", index=False)
    summary.to_csv(output_dir / "summary.csv", index=False)
    metadata = {
        "strategy": "FourWeekLevelReversal",
        "include_test": include_test,
        "config": asdict(config),
        "input_events": len(events),
        "touches": int(trades["touch"].fillna(False).sum()),
        "sweeps": int(trades["sweep"].fillna(False).sum()),
        "reclaims": int(trades["reclaimed"].fillna(False).sum()),
        "limit_fills": int(
            trades.get("limit_filled", pd.Series(False, index=trades.index))
            .fillna(False)
            .sum()
        ),
        "eligible": int(trades["eligible"].fillna(False).sum()),
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata
