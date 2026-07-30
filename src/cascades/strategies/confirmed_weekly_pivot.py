from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..hypotheses import cluster_bootstrap_ci
from ..utils.crypto import load_crypto_symbol


@dataclass(frozen=True)
class WeeklyPivotLimitConfig:
    pivot_left_weeks: int = 2
    pivot_right_weeks: int = 2
    entry_offset_percent: float = 7.0
    order_lifetime_minutes: int = 240
    initial_stop_loss_percent: float = 25.0
    breakeven_after_minutes: int | None = 5
    maximum_holding_minutes: int = 7 * 24 * 60
    fee_bps_per_side: float = 5.0
    slippage_bps_per_side: float = 2.0

    @property
    def cost(self) -> float:
        return 2 * (self.fee_bps_per_side + self.slippage_bps_per_side) / 10_000


def confirmed_weekly_pivots(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["week_start"] = (
        work.timestamp.dt.normalize()
        - pd.to_timedelta(work.timestamp.dt.dayofweek, unit="D")
    )
    weekly = work.groupby("week_start").agg(high=("high", "max"), low=("low", "min"))
    low_window = weekly.low.rolling(5, center=True)
    high_window = weekly.high.rolling(5, center=True)
    low_mask = weekly.low.eq(low_window.min())
    high_mask = weekly.high.eq(high_window.max())
    rows = []
    for week_start, row in weekly[low_mask].iterrows():
        rows.append(
            {
                "kind": "low",
                "level": row.low,
                "pivot_week": week_start,
                "available_at": week_start + pd.Timedelta(weeks=3),
            }
        )
    for week_start, row in weekly[high_mask].iterrows():
        rows.append(
            {
                "kind": "high",
                "level": row.high,
                "pivot_week": week_start,
                "available_at": week_start + pd.Timedelta(weeks=3),
            }
        )
    return pd.DataFrame(rows).sort_values("available_at").reset_index(drop=True)


def _simulate(
    frame: pd.DataFrame,
    fill_position: int,
    entry: float,
    take_profit: float,
    direction: float,
    config: WeeklyPivotLimitConfig,
) -> dict:
    initial_stop = (
        entry * (1 - config.initial_stop_loss_percent / 100)
        if direction < 0
        else entry * (1 + config.initial_stop_loss_percent / 100)
    )
    end = min(len(frame), fill_position + config.maximum_holding_minutes + 1)
    for elapsed, (_, candle) in enumerate(
        frame.iloc[fill_position:end].iterrows()
    ):
        breakeven_active = (
            config.breakeven_after_minutes is not None
            and elapsed >= config.breakeven_after_minutes
        )
        stop = entry if breakeven_active else initial_stop
        activation_behind_market = (
            config.breakeven_after_minutes is not None
            and elapsed == config.breakeven_after_minutes
            and (
                (direction < 0 and candle.open < entry)
                or (direction > 0 and candle.open > entry)
            )
        )
        if activation_behind_market:
            exit_price = candle.open
            gross = -direction * (exit_price / entry - 1)
            return {
                "exit_timestamp": candle.timestamp,
                "exit_price": exit_price,
                "exit_reason": "breakeven_activation",
                "holding_minutes": elapsed,
                "gross_return": gross,
                "net_return": gross - config.cost,
            }
        stop_hit = candle.low <= stop if direction < 0 else candle.high >= stop
        tp_hit = (
            candle.high >= take_profit
            if direction < 0
            else candle.low <= take_profit
        )
        if stop_hit:  # Conservative when stop and TP are both inside the candle.
            exit_price, reason = stop, (
                "breakeven" if breakeven_active else "stop"
            )
        elif tp_hit:
            exit_price, reason = take_profit, "take_profit"
        else:
            continue
        gross = -direction * (exit_price / entry - 1)
        return {
            "exit_timestamp": candle.timestamp,
            "exit_price": exit_price,
            "exit_reason": reason,
            "holding_minutes": elapsed,
            "gross_return": gross,
            "net_return": gross - config.cost,
        }
    candle = frame.iloc[end - 1]
    gross = -direction * (candle.close / entry - 1)
    return {
        "exit_timestamp": candle.timestamp,
        "exit_price": candle.close,
        "exit_reason": "time_exit",
        "holding_minutes": end - fill_position - 1,
        "gross_return": gross,
        "net_return": gross - config.cost,
    }


def generate_pivot_trades(
    frame: pd.DataFrame,
    events: pd.DataFrame,
    config: WeeklyPivotLimitConfig = WeeklyPivotLimitConfig(),
) -> pd.DataFrame:
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    positions = pd.Series(np.arange(len(frame)), index=frame.timestamp)
    pivots = confirmed_weekly_pivots(frame)
    used: set[tuple[str, pd.Timestamp]] = set()
    records = []
    for _, event in events.sort_values("timestamp").iterrows():
        position = positions.get(event.timestamp)
        if position is None or position == 0:
            continue
        direction = float(event.direction)
        kind = "low" if direction < 0 else "high"
        previous_close = frame.iloc[int(position) - 1].close
        candle = frame.iloc[int(position)]
        available = pivots[
            (pivots.kind == kind) & (pivots.available_at <= event.timestamp)
        ].copy()
        if direction < 0:
            available = available[
                (available.level <= previous_close) & (available.level >= candle.low)
            ]
            available = available.sort_values("level", ascending=False)
        else:
            available = available[
                (available.level >= previous_close) & (available.level <= candle.high)
            ]
            available = available.sort_values("level")
        if available.empty:
            continue
        pivot = available.iloc[0]
        key = (kind, pivot.pivot_week)
        if key in used:
            continue
        used.add(key)
        entry = (
            pivot.level * (1 - config.entry_offset_percent / 100)
            if direction < 0
            else pivot.level * (1 + config.entry_offset_percent / 100)
        )
        search = frame.iloc[
            int(position) : int(position) + config.order_lifetime_minutes + 1
        ]
        fill_position = None
        for offset, (_, candidate) in enumerate(search.iterrows()):
            filled = candidate.low <= entry if direction < 0 else candidate.high >= entry
            if filled:
                fill_position = int(position) + offset
                break
        record = event.to_dict()
        record.update(
            {
                "pivot_kind": kind,
                "pivot_week": pivot.pivot_week,
                "pivot_level": pivot.level,
                "pivot_available_at": pivot.available_at,
                "entry_price": entry,
                "order_filled": fill_position is not None,
            }
        )
        if fill_position is not None:
            record["entry_timestamp"] = frame.iloc[fill_position].timestamp
            record["fill_delay_minutes"] = fill_position - int(position)
            record.update(
                _simulate(
                    frame, fill_position, entry, pivot.level, direction, config
                )
            )
        records.append(record)
    return pd.DataFrame(records)


def run_weekly_pivot_strategy(
    raw_dir: Path,
    events_path: Path,
    output_dir: Path,
    include_test: bool = False,
    config: WeeklyPivotLimitConfig | None = None,
) -> dict:
    config = config or WeeklyPivotLimitConfig()
    output_dir.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(events_path, parse_dates=["timestamp"])
    allowed = ["research", "validation"] + (["test"] if include_test else [])
    events = events[events.split.isin(allowed)]
    start, end = pd.Timestamp("2025-07-01", tz="UTC"), pd.Timestamp("2026-07-01", tz="UTC")
    results = []
    for symbol, group in events.groupby("symbol"):
        frame, _ = load_crypto_symbol(raw_dir, symbol, start, end)
        trades = generate_pivot_trades(frame, group, config)
        if len(trades):
            trades["symbol"] = symbol
            results.append(trades)
        print(f"{symbol}: {int(trades.order_filled.sum()) if len(trades) else 0} fills", flush=True)
    trades = pd.concat(results, ignore_index=True) if results else pd.DataFrame()
    rows = []
    filled = trades[trades.order_filled.fillna(False)] if len(trades) else trades
    for split, group in filled.groupby("split"):
        low, high = cluster_bootstrap_ci(group, "net_return")
        rows.append(
            {
                "split": split,
                "trades": len(group),
                "clusters": group.cluster_id.nunique(),
                "mean_net_return": group.net_return.mean(),
                "median_net_return": group.net_return.median(),
                "win_rate": (group.net_return > 0).mean(),
                "take_profit_rate": (group.exit_reason == "take_profit").mean(),
                "breakeven_rate": (group.exit_reason == "breakeven").mean(),
                "stop_rate": (group.exit_reason == "stop").mean(),
                "ci_low": low,
                "ci_high": high,
            }
        )
    summary = pd.DataFrame(rows)
    trades.to_csv(output_dir / "events_and_trades.csv", index=False)
    summary.to_csv(output_dir / "summary.csv", index=False)
    metadata = {
        "strategy": "ConfirmedWeeklyPivotLimit",
        "include_test": include_test,
        "config": asdict(config),
        "setups": len(trades),
        "fills": len(filled),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
