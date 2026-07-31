"""Long strategy for volume-backed weekly pivots with a prior defense."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils.stocks import (
    confirmed_stock_weekly_pivots,
    download_stock_hourly,
    load_stock_hourly,
)


@dataclass(frozen=True)
class DefendedPivotConfig:
    volume_lookback_weeks: int = 12
    minimum_volume_ratio: float = 1.5
    atr_days: int = 14
    touch_zone_atr: float = 0.5
    minimum_bounce_atr: float = 1.5
    bounce_window_days: int = 5
    entry_offset_percent: float = 5.0
    take_profit_percent: float = 10.0
    stop_loss_percent: float = 25.0
    order_lifetime_hours: int = 4
    entry_mode: str = "offset_limit"
    profile_bins: int = 30
    profile_range_atr: float = 1.0
    volume_entry_window_days: int = 5
    maximum_holding_days: int = 60
    fee_bps_per_side: float = 1.0
    slippage_bps_per_side: float = 3.0
    market_timezone: str = "America/New_York"

    @property
    def round_trip_cost(self) -> float:
        return 2 * (self.fee_bps_per_side + self.slippage_bps_per_side) / 10_000


def _add_causal_atr(
    frame: pd.DataFrame, config: DefendedPivotConfig
) -> pd.DataFrame:
    result = frame.copy()
    local = result["timestamp"].dt.tz_convert(config.market_timezone)
    result["_day"] = local.dt.normalize()
    daily = result.groupby("_day").agg(
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
    )
    previous_close = daily["close"].shift(1)
    true_range = pd.concat(
        [
            daily["high"] - daily["low"],
            (daily["high"] - previous_close).abs(),
            (daily["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    # Shift one full day: today's intraday decisions never see today's range.
    daily["atr"] = (
        true_range.rolling(config.atr_days, min_periods=config.atr_days)
        .mean()
        .shift(1)
    )
    result["daily_atr"] = result["_day"].map(daily["atr"])
    return result.drop(columns="_day")


def _pivot_volume_ratio(
    frame: pd.DataFrame, config: DefendedPivotConfig
) -> pd.Series:
    work = frame.copy()
    local = work["timestamp"].dt.tz_convert(config.market_timezone)
    work["_week"] = (
        local.dt.normalize() - pd.to_timedelta(local.dt.dayofweek, unit="D")
    )
    work["_dollar_volume"] = work["close"] * work["volume"]
    weekly = work.groupby("_week")["_dollar_volume"].sum()
    baseline = (
        weekly.rolling(
            config.volume_lookback_weeks,
            min_periods=config.volume_lookback_weeks,
        )
        .median()
        .shift(1)
    )
    return weekly / baseline


def _defense_high_volume_zone(
    window: pd.DataFrame,
    pivot: float,
    atr: float,
    config: DefendedPivotConfig,
) -> tuple[float, float, float, float]:
    lower = pivot - config.profile_range_atr * atr
    upper = pivot + config.profile_range_atr * atr
    edges = np.linspace(lower, upper, config.profile_bins + 1)
    typical_price = (window["high"] + window["low"] + window["close"]) / 3
    typical_price = typical_price.clip(
        lower=lower + np.finfo(float).eps,
        upper=upper - np.finfo(float).eps,
    )
    dollar_volume = window["close"] * window["volume"]
    profile, _ = np.histogram(typical_price, bins=edges, weights=dollar_volume)
    best = int(np.argmax(profile))
    total = profile.sum()
    share = float(profile[best] / total) if total else 0.0
    return (
        float(edges[best]),
        float((edges[best] + edges[best + 1]) / 2),
        float(edges[best + 1]),
        share,
    )


def _close_long(
    frame: pd.DataFrame,
    fill: int,
    entry: float,
    config: DefendedPivotConfig,
) -> dict:
    deadline = frame.iloc[fill].timestamp + pd.Timedelta(
        days=config.maximum_holding_days
    )
    stop = entry * (1 - config.stop_loss_percent / 100)
    take_profit = entry * (1 + config.take_profit_percent / 100)
    candidates = frame.iloc[fill:]
    candidates = candidates[candidates.timestamp <= deadline]
    for elapsed, (_, candle) in enumerate(candidates.iterrows()):
        stop_hit = candle.low <= stop
        take_profit_hit = elapsed > 0 and candle.high >= take_profit
        if stop_hit:
            exit_price, reason = stop, "stop"
        elif take_profit_hit:
            exit_price, reason = take_profit, "take_profit"
        else:
            continue
        gross = exit_price / entry - 1
        return {
            "exit_timestamp": candle.timestamp,
            "exit_price": exit_price,
            "exit_reason": reason,
            "gross_return": gross,
            "net_return": gross - config.round_trip_cost,
        }
    candle = candidates.iloc[-1] if len(candidates) else frame.iloc[fill]
    gross = candle.close / entry - 1
    return {
        "exit_timestamp": candle.timestamp,
        "exit_price": candle.close,
        "exit_reason": (
            "time_exit" if frame.iloc[-1].timestamp >= deadline else "open"
        ),
        "gross_return": gross,
        "net_return": gross - config.round_trip_cost,
    }


def backtest_defended_pivot(
    frame: pd.DataFrame, config: DefendedPivotConfig
) -> pd.DataFrame:
    frame = _add_causal_atr(
        frame.sort_values("timestamp").reset_index(drop=True), config
    )
    pivots = confirmed_stock_weekly_pivots(
        frame, timezone=config.market_timezone
    )
    if pivots.empty:
        return pd.DataFrame()
    pivots = pivots[pivots.kind == "low"].copy()
    volume_ratio = _pivot_volume_ratio(frame, config)
    pivots["volume_ratio"] = pivots["pivot_week"].map(volume_ratio)
    pivots = pivots[
        pivots["volume_ratio"] >= config.minimum_volume_ratio
    ]
    previous_close = frame["close"].shift(1)
    records = []
    for _, pivot in pivots.iterrows():
        record = {
            "symbol": frame.iloc[0].symbol,
            "side": "long",
            "pivot_week": pivot.pivot_week,
            "pivot_level": pivot.level,
            "pivot_available_at": pivot.available_at,
            "volume_ratio": pivot.volume_ratio,
            "defense_confirmed": False,
            "order_filled": False,
        }
        eligible = frame[
            (frame.timestamp >= pivot.available_at)
            & frame.daily_atr.notna()
        ]
        touches = eligible[
            (eligible.low >= pivot.level - config.touch_zone_atr * eligible.daily_atr)
            & (eligible.low <= pivot.level + config.touch_zone_atr * eligible.daily_atr)
        ]
        if touches.empty:
            records.append(record)
            continue
        touch_index = int(touches.index[0])
        touch = frame.iloc[touch_index]
        bounce_end = touch.timestamp + pd.Timedelta(
            days=config.bounce_window_days
        )
        bounce_bars = frame.iloc[touch_index:]
        bounce_bars = bounce_bars[bounce_bars.timestamp <= bounce_end]
        target = pivot.level + config.minimum_bounce_atr * touch.daily_atr
        confirmations = bounce_bars[bounce_bars.high >= target]
        if confirmations.empty:
            records.append(record)
            continue
        confirmation_index = int(confirmations.index[0])
        confirmation = frame.iloc[confirmation_index]
        zone_low, zone_center, zone_high, zone_share = _defense_high_volume_zone(
            frame.iloc[touch_index : confirmation_index + 1],
            pivot.level,
            touch.daily_atr,
            config,
        )
        record.update(
            {
                "defense_touch_timestamp": touch.timestamp,
                "defense_atr": touch.daily_atr,
                "defense_confirmed": True,
                "defense_confirmed_at": confirmation.timestamp,
                "hvn_low": zone_low,
                "hvn_center": zone_center,
                "hvn_high": zone_high,
                "hvn_volume_share": zone_share,
            }
        )
        after_defense = frame.iloc[confirmation_index + 1 :]
        triggers = after_defense[
            (previous_close.loc[after_defense.index] >= pivot.level)
            & (after_defense.low < pivot.level)
        ]
        if triggers.empty:
            records.append(record)
            continue
        trigger_index = int(triggers.index[0])
        trigger = frame.iloc[trigger_index]
        if config.entry_mode == "offset_limit":
            entry = pivot.level * (1 - config.entry_offset_percent / 100)
            order_end = trigger.timestamp + pd.Timedelta(
                hours=config.order_lifetime_hours
            )
            order_bars = frame.iloc[trigger_index:]
            order_bars = order_bars[order_bars.timestamp <= order_end]
            fill = next(
                (
                    int(index)
                    for index, candle in order_bars.iterrows()
                    if candle.low <= entry
                ),
                None,
            )
        elif config.entry_mode == "hvn_limit_center":
            entry = zone_center
            order_end = trigger.timestamp + pd.Timedelta(
                days=config.volume_entry_window_days
            )
            order_bars = frame.iloc[trigger_index:]
            order_bars = order_bars[order_bars.timestamp <= order_end]
            fill = next(
                (
                    int(index)
                    for index, candle in order_bars.iterrows()
                    if candle.low <= entry
                ),
                None,
            )
        elif config.entry_mode == "hvn_reclaim_low":
            entry_end = trigger.timestamp + pd.Timedelta(
                days=config.volume_entry_window_days
            )
            candidates = frame.iloc[trigger_index:]
            candidates = candidates[candidates.timestamp <= entry_end]
            fill = next(
                (
                    int(index)
                    for index, candle in candidates.iterrows()
                    if candle.low < zone_low and candle.close > zone_low
                ),
                None,
            )
            entry = float(frame.iloc[fill].close) if fill is not None else zone_low
        else:
            raise ValueError(f"Unknown entry mode: {config.entry_mode}")
        record.update(
            {
                "trigger_timestamp": trigger.timestamp,
                "entry_price": entry,
                "take_profit_price": entry
                * (1 + config.take_profit_percent / 100),
                "order_filled": fill is not None,
            }
        )
        if fill is not None:
            record["entry_timestamp"] = frame.iloc[fill].timestamp
            record.update(_close_long(frame, fill, entry, config))
        records.append(record)
    return pd.DataFrame(records)


def _write_results(
    frames: dict[str, pd.DataFrame],
    output_dir: Path,
    config: DefendedPivotConfig,
    *,
    source: str,
    interval: str,
    range_: str,
    failures: dict[str, str],
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_trades = []
    for symbol, frame in frames.items():
        trades = backtest_defended_pivot(frame, config)
        all_trades.append(trades)
        defenses = (
            int(trades.defense_confirmed.sum()) if len(trades) else 0
        )
        fills = int(trades.order_filled.sum()) if len(trades) else 0
        print(
            f"{symbol}: {len(frame)} bars, {defenses} defenses, {fills} fills",
            flush=True,
        )
    trades = (
        pd.concat(all_trades, ignore_index=True)
        if all_trades
        else pd.DataFrame()
    )
    filled = (
        trades[trades.order_filled.fillna(False)].copy()
        if len(trades)
        else trades
    )
    completed = (
        filled[filled.exit_reason != "open"]
        if len(filled) and "exit_reason" in filled
        else pd.DataFrame()
    )
    summary = (
        completed.groupby("symbol")
        .agg(
            trades=("net_return", "size"),
            mean_net_return=("net_return", "mean"),
            median_net_return=("net_return", "median"),
            win_rate=("net_return", lambda x: (x > 0).mean()),
        )
        .reset_index()
        if len(completed)
        else pd.DataFrame()
    )
    trades.to_csv(output_dir / "trades.csv", index=False)
    summary.to_csv(output_dir / "summary_by_symbol.csv", index=False)
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strategy": {
            "offset_limit": "DefendedPivotLong",
            "hvn_limit_center": "DefendedPivotHvnLimit",
            "hvn_reclaim_low": "DefendedPivotHvnReclaim",
        }[config.entry_mode],
        "source": source,
        "interval": interval,
        "range": range_,
        "symbols": list(frames),
        "config": asdict(config),
        "volume_qualified_pivots": len(trades),
        "confirmed_defenses": (
            int(trades.defense_confirmed.sum()) if len(trades) else 0
        ),
        "fills": len(filled),
        "completed": len(completed),
        "failures": failures,
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def run_defended_pivot_frames(
    frames: dict[str, pd.DataFrame],
    output_dir: Path,
    config: DefendedPivotConfig,
    *,
    source: str,
    interval: str,
    range_: str,
    failures: dict[str, str] | None = None,
) -> dict:
    return _write_results(
        frames,
        output_dir,
        config,
        source=source,
        interval=interval,
        range_=range_,
        failures=failures or {},
    )


def run_defended_pivot_equities(
    data_dir: Path,
    output_dir: Path,
    symbols: list[str],
    config: DefendedPivotConfig,
) -> dict:
    frames = {}
    failures = {}
    for symbol in symbols:
        try:
            frames[symbol] = load_stock_hourly(
                download_stock_hourly(symbol, data_dir)
            )
        except Exception as exc:
            failures[symbol] = str(exc)
            print(f"{symbol}: FAILED: {exc}", flush=True)
    return _write_results(
        frames,
        output_dir,
        config,
        source="Yahoo Finance chart API",
        interval="1h",
        range_="1y",
        failures=failures,
    )
