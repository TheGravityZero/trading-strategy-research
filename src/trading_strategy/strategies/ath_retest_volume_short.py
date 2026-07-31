"""Short a failed ATH retest at an upper high-volume node."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..utils.stocks import download_stock_hourly, load_stock_hourly


@dataclass(frozen=True)
class AthRetestVolumeConfig:
    minimum_correction_percent: float = 15.0
    ath_retest_distance_percent: float = 3.0
    profile_bins: int = 30
    upper_profile_fraction: float = 0.5
    entry_lifetime_days: int = 5
    take_profit_percent: float = 10.0
    stop_mode: str = "percent"
    stop_loss_percent: float = 15.0
    maximum_holding_days: int = 60
    fee_bps_per_side: float = 1.0
    slippage_bps_per_side: float = 3.0

    @property
    def round_trip_cost(self) -> float:
        return 2 * (self.fee_bps_per_side + self.slippage_bps_per_side) / 10_000


def _upper_high_volume_node(
    window: pd.DataFrame,
    correction_low: float,
    ath: float,
    config: AthRetestVolumeConfig,
) -> tuple[float, float]:
    edges = np.linspace(correction_low, ath, config.profile_bins + 1)
    typical_price = (window["high"] + window["low"] + window["close"]) / 3
    weights = window["close"] * window["volume"]
    profile, _ = np.histogram(typical_price, bins=edges, weights=weights)
    first_upper_bin = int(
        config.profile_bins * (1 - config.upper_profile_fraction)
    )
    upper_profile = profile[first_upper_bin:]
    best = first_upper_bin + int(np.argmax(upper_profile))
    center = (edges[best] + edges[best + 1]) / 2
    total = profile.sum()
    share = float(profile[best] / total) if total else 0.0
    return float(center), share


def _close_short(
    frame: pd.DataFrame,
    fill: int,
    entry: float,
    config: AthRetestVolumeConfig,
    stop_price: float | None = None,
) -> dict:
    deadline = frame.iloc[fill].timestamp + pd.Timedelta(
        days=config.maximum_holding_days
    )
    stop = (
        stop_price
        if stop_price is not None
        else entry * (1 + config.stop_loss_percent / 100)
    )
    take_profit = entry * (1 - config.take_profit_percent / 100)
    candidates = frame.iloc[fill:]
    candidates = candidates[candidates.timestamp <= deadline]
    for elapsed, (_, candle) in enumerate(candidates.iterrows()):
        stop_hit = candle.high >= stop
        take_profit_hit = elapsed > 0 and candle.low <= take_profit
        if stop_hit:
            exit_price, reason = stop, "stop"
        elif take_profit_hit:
            exit_price, reason = take_profit, "take_profit"
        else:
            continue
        gross = -(exit_price / entry - 1)
        return {
            "exit_timestamp": candle.timestamp,
            "exit_price": exit_price,
            "exit_reason": reason,
            "gross_return": gross,
            "net_return": gross - config.round_trip_cost,
        }
    candle = candidates.iloc[-1] if len(candidates) else frame.iloc[fill]
    gross = -(candle.close / entry - 1)
    return {
        "exit_timestamp": candle.timestamp,
        "exit_price": candle.close,
        "exit_reason": (
            "time_exit" if frame.iloc[-1].timestamp >= deadline else "open"
        ),
        "gross_return": gross,
        "net_return": gross - config.round_trip_cost,
    }


def backtest_ath_retest_volume(
    frame: pd.DataFrame, config: AthRetestVolumeConfig
) -> pd.DataFrame:
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    records = []
    ath = float(frame.iloc[0].high)
    ath_index = 0
    correction_index: int | None = None
    unavailable_until: pd.Timestamp | None = None
    position = 1
    while position < len(frame):
        candle = frame.iloc[position]
        if unavailable_until is not None and candle.timestamp <= unavailable_until:
            position += 1
            continue
        if candle.high >= ath:
            ath = float(candle.high)
            ath_index = position
            correction_index = None
            position += 1
            continue
        drawdown = 100 * (1 - candle.low / ath)
        if (
            correction_index is None
            and drawdown >= config.minimum_correction_percent
        ):
            correction_index = position
        if correction_index is None:
            position += 1
            continue
        retest_floor = ath * (1 - config.ath_retest_distance_percent / 100)
        if not (retest_floor <= candle.high < ath):
            position += 1
            continue
        profile_window = frame.iloc[ath_index : position + 1]
        correction_low = float(
            frame.iloc[correction_index : position + 1]["low"].min()
        )
        node, node_share = _upper_high_volume_node(
            profile_window, correction_low, ath, config
        )
        node_half_width = (ath - correction_low) / config.profile_bins / 2
        node_upper = node + node_half_width
        below = frame.iloc[position:]
        breaks = below[below.close < node]
        record = {
            "symbol": frame.iloc[0].symbol,
            "side": "short",
            "ath_level": ath,
            "ath_timestamp": frame.iloc[ath_index].timestamp,
            "correction_timestamp": frame.iloc[correction_index].timestamp,
            "correction_percent": 100 * (1 - correction_low / ath),
            "ath_retest_timestamp": candle.timestamp,
            "ath_retest_high": candle.high,
            "volume_node": node,
            "volume_node_upper": node_upper,
            "volume_node_share": node_share,
            "order_filled": False,
        }
        if breaks.empty:
            records.append(record)
            break
        break_index = int(breaks.index[0])
        entry_end = frame.iloc[break_index].timestamp + pd.Timedelta(
            days=config.entry_lifetime_days
        )
        entry_bars = frame.iloc[break_index + 1 :]
        entry_bars = entry_bars[entry_bars.timestamp <= entry_end]
        fill = next(
            (
                int(index)
                for index, candidate in entry_bars.iterrows()
                if candidate.high >= node
            ),
            None,
        )
        record["node_break_timestamp"] = frame.iloc[break_index].timestamp
        record["entry_price"] = node
        record["take_profit_price"] = node * (
            1 - config.take_profit_percent / 100
        )
        if config.stop_mode == "ath":
            stop_price = ath
        elif config.stop_mode == "hvn":
            stop_price = node_upper
        elif config.stop_mode == "percent":
            stop_price = node * (1 + config.stop_loss_percent / 100)
        else:
            raise ValueError(f"Unknown stop mode: {config.stop_mode}")
        record["stop_price"] = stop_price
        record["order_filled"] = fill is not None
        if fill is not None:
            record["entry_timestamp"] = frame.iloc[fill].timestamp
            record.update(
                _close_short(frame, fill, node, config, stop_price=stop_price)
            )
            unavailable_until = record["exit_timestamp"]
            position = fill + 1
        else:
            unavailable_until = entry_end
            position = break_index + 1
        records.append(record)
        ath = float(frame.iloc[: position + 1]["high"].max())
        ath_index = int(frame.iloc[: position + 1]["high"].idxmax())
        correction_index = None
    return pd.DataFrame(records)


def _write_results(
    frames: dict[str, pd.DataFrame],
    output_dir: Path,
    config: AthRetestVolumeConfig,
    *,
    source: str,
    interval: str,
    range_: str,
    failures: dict[str, str],
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_trades = []
    for symbol, frame in frames.items():
        trades = backtest_ath_retest_volume(frame, config)
        all_trades.append(trades)
        fills = int(trades.order_filled.sum()) if len(trades) else 0
        print(f"{symbol}: {len(frame)} bars, {len(trades)} setups, {fills} fills")
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
        "strategy": "AthRetestVolumeShort",
        "source": source,
        "interval": interval,
        "range": range_,
        "symbols": list(frames),
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


def run_ath_retest_frames(
    frames: dict[str, pd.DataFrame],
    output_dir: Path,
    config: AthRetestVolumeConfig,
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


def run_ath_retest_equities(
    data_dir: Path,
    output_dir: Path,
    symbols: list[str],
    config: AthRetestVolumeConfig,
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
