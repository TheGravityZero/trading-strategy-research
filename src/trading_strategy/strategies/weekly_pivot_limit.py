"""Market-neutral confirmed weekly-pivot limit strategy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

import pandas as pd

from ..utils.stocks import (
    confirmed_stock_weekly_pivots,
    download_stock_hourly,
    load_stock_hourly,
)


@dataclass(frozen=True)
class WeeklyPivotConfig:
    entry_offset_percent: float = 5.0
    take_profit_percent: float | None = None
    long_only: bool = False
    order_lifetime_hours: int = 4
    stop_loss_percent: float = 25.0
    maximum_holding_days: int = 90
    fee_bps_per_side: float = 1.0
    slippage_bps_per_side: float = 3.0
    market_timezone: str = "America/New_York"

    @property
    def round_trip_cost(self) -> float:
        return 2 * (self.fee_bps_per_side + self.slippage_bps_per_side) / 10_000


def _close_trade(
    frame: pd.DataFrame,
    fill: int,
    entry: float,
    take_profit: float,
    side: str,
    config: WeeklyPivotConfig,
) -> dict:
    deadline = frame.iloc[fill].timestamp + pd.Timedelta(
        days=config.maximum_holding_days
    )
    stop = (
        entry * (1 - config.stop_loss_percent / 100)
        if side == "long"
        else entry * (1 + config.stop_loss_percent / 100)
    )
    candidates = frame.iloc[fill:]
    candidates = candidates[candidates.timestamp <= deadline]
    for elapsed, (_, candle) in enumerate(candidates.iterrows()):
        stop_hit = candle.low <= stop if side == "long" else candle.high >= stop
        # Hourly OHLC does not reveal whether the extreme happened before the
        # limit fill. Ignore a fill-bar TP, while retaining the conservative stop.
        tp_hit = elapsed > 0 and (
            candle.high >= take_profit
            if side == "long"
            else candle.low <= take_profit
        )
        if stop_hit:
            exit_price, reason = stop, "stop"
        elif tp_hit:
            exit_price, reason = take_profit, "take_profit"
        else:
            continue
        gross = (
            exit_price / entry - 1
            if side == "long"
            else -(exit_price / entry - 1)
        )
        return {
            "exit_timestamp": candle.timestamp,
            "exit_price": exit_price,
            "exit_reason": reason,
            "gross_return": gross,
            "net_return": gross - config.round_trip_cost,
        }
    candle = candidates.iloc[-1] if len(candidates) else frame.iloc[fill]
    gross = (
        candle.close / entry - 1
        if side == "long"
        else -(candle.close / entry - 1)
    )
    return {
        "exit_timestamp": candle.timestamp,
        "exit_price": candle.close,
        "exit_reason": (
            "time_exit" if frame.iloc[-1].timestamp >= deadline else "open"
        ),
        "gross_return": gross,
        "net_return": gross - config.round_trip_cost,
    }


def backtest_weekly_pivot(
    frame: pd.DataFrame, config: WeeklyPivotConfig
) -> pd.DataFrame:
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    pivots = confirmed_stock_weekly_pivots(
        frame, timezone=config.market_timezone
    )
    if config.long_only and len(pivots):
        pivots = pivots[pivots.kind == "low"]
    records: list[dict] = []
    previous_close = frame.close.shift(1)
    for _, pivot in pivots.iterrows():
        eligible = frame[frame.timestamp >= pivot.available_at]
        if eligible.empty:
            continue
        if pivot.kind == "low":
            crossed = eligible[
                (previous_close.loc[eligible.index] >= pivot.level)
                & (eligible.low < pivot.level)
            ]
            side = "long"
            entry = pivot.level * (1 - config.entry_offset_percent / 100)
        else:
            crossed = eligible[
                (previous_close.loc[eligible.index] <= pivot.level)
                & (eligible.high > pivot.level)
            ]
            side = "short"
            entry = pivot.level * (1 + config.entry_offset_percent / 100)
        if crossed.empty:
            continue
        trigger = int(crossed.index[0])
        order_end = frame.iloc[trigger].timestamp + pd.Timedelta(
            hours=config.order_lifetime_hours
        )
        order_bars = frame.iloc[trigger:]
        order_bars = order_bars[order_bars.timestamp <= order_end]
        fill = None
        for index, candle in order_bars.iterrows():
            if (side == "long" and candle.low <= entry) or (
                side == "short" and candle.high >= entry
            ):
                fill = int(index)
                break
        take_profit = (
            entry * (1 + config.take_profit_percent / 100)
            if side == "long" and config.take_profit_percent is not None
            else entry * (1 - config.take_profit_percent / 100)
            if side == "short" and config.take_profit_percent is not None
            else pivot.level
        )
        record = {
            "symbol": frame.iloc[0].symbol,
            "side": side,
            "pivot_week": pivot.pivot_week,
            "pivot_level": pivot.level,
            "pivot_available_at": pivot.available_at,
            "trigger_timestamp": frame.iloc[trigger].timestamp,
            "entry_price": entry,
            "take_profit_price": take_profit,
            "order_filled": fill is not None,
        }
        if fill is not None:
            record["entry_timestamp"] = frame.iloc[fill].timestamp
            record.update(
                _close_trade(frame, fill, entry, take_profit, side, config)
            )
        records.append(record)
    return pd.DataFrame(records)


def run_weekly_pivot_study(
    data_dir: Path,
    output_dir: Path,
    symbols: list[str],
    config: WeeklyPivotConfig | None = None,
) -> dict:
    config = config or WeeklyPivotConfig()
    output_dir.mkdir(parents=True, exist_ok=True)
    all_trades = []
    failures = {}
    for symbol in symbols:
        try:
            path = download_stock_hourly(symbol, data_dir)
            frame = load_stock_hourly(path)
            trades = backtest_weekly_pivot(frame, config)
            all_trades.append(trades)
            fills = int(trades.order_filled.sum()) if len(trades) else 0
            print(f"{symbol}: {len(frame)} bars, {fills} fills", flush=True)
        except Exception as exc:
            failures[symbol] = str(exc)
            print(f"{symbol}: FAILED: {exc}", flush=True)
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
    completed = filled[filled.exit_reason != "open"] if len(filled) else filled
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
        "strategy": "ConfirmedWeeklyPivotLimit",
        "source": "Yahoo Finance chart API",
        "interval": "1h",
        "range": "1y",
        "symbols": symbols,
        "config": asdict(config),
        "setups": len(trades),
        "fills": len(filled),
        "completed": len(completed),
        "failures": failures,
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def run_frames_study(
    frames: dict[str, pd.DataFrame],
    output_dir: Path,
    config: WeeklyPivotConfig,
    *,
    source: str,
    interval: str,
    range_: str,
    failures: dict[str, str] | None = None,
) -> dict:
    """Backtest the same strategy on already loaded crypto or equity frames."""
    output_dir.mkdir(parents=True, exist_ok=True)
    all_trades = []
    for symbol, frame in frames.items():
        trades = backtest_weekly_pivot(frame, config)
        all_trades.append(trades)
        fills = int(trades.order_filled.sum()) if len(trades) else 0
        print(f"{symbol}: {len(frame)} bars, {fills} fills", flush=True)
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
        "strategy": "ConfirmedWeeklyPivotLimit",
        "source": source,
        "interval": interval,
        "range": range_,
        "symbols": list(frames),
        "config": asdict(config),
        "setups": len(trades),
        "fills": len(filled),
        "completed": len(completed),
        "failures": failures or {},
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata
