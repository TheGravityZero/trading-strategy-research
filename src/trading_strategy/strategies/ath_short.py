"""Causal all-time-high breakout short strategy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import pandas as pd

from ..utils.stocks import download_stock_hourly, load_stock_hourly


@dataclass(frozen=True)
class AthShortConfig:
    entry_offset_percent: float = 7.0
    take_profit_percent: float = 10.0
    stop_loss_percent: float = 15.0
    order_lifetime_hours: int = 4
    maximum_holding_days: int = 60
    fee_bps_per_side: float = 1.0
    slippage_bps_per_side: float = 3.0

    @property
    def round_trip_cost(self) -> float:
        return 2 * (self.fee_bps_per_side + self.slippage_bps_per_side) / 10_000


def _close_short(
    frame: pd.DataFrame,
    fill: int,
    entry: float,
    config: AthShortConfig,
) -> dict:
    deadline = frame.iloc[fill].timestamp + pd.Timedelta(
        days=config.maximum_holding_days
    )
    stop = entry * (1 + config.stop_loss_percent / 100)
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


def backtest_ath_short(
    frame: pd.DataFrame, config: AthShortConfig
) -> pd.DataFrame:
    """Short above the maximum high available before the current candle."""
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    prior_ath = frame["high"].cummax().shift(1)
    records: list[dict] = []
    unavailable_until: pd.Timestamp | None = None
    for position in range(1, len(frame)):
        candle = frame.iloc[position]
        if unavailable_until is not None and candle.timestamp <= unavailable_until:
            continue
        ath = prior_ath.iloc[position]
        previous_close = frame.iloc[position - 1].close
        if not pd.notna(ath) or not (
            previous_close <= ath and candle.high > ath
        ):
            continue
        entry = ath * (1 + config.entry_offset_percent / 100)
        order_end = candle.timestamp + pd.Timedelta(
            hours=config.order_lifetime_hours
        )
        order_bars = frame.iloc[position:]
        order_bars = order_bars[order_bars.timestamp <= order_end]
        fill = next(
            (
                int(index)
                for index, candidate in order_bars.iterrows()
                if candidate.high >= entry
            ),
            None,
        )
        record = {
            "symbol": frame.iloc[0].symbol,
            "side": "short",
            "ath_level": ath,
            "trigger_timestamp": candle.timestamp,
            "entry_price": entry,
            "take_profit_price": entry
            * (1 - config.take_profit_percent / 100),
            "order_filled": fill is not None,
        }
        if fill is not None:
            record["entry_timestamp"] = frame.iloc[fill].timestamp
            record.update(_close_short(frame, fill, entry, config))
            unavailable_until = record["exit_timestamp"]
        else:
            unavailable_until = order_end
        records.append(record)
    return pd.DataFrame(records)


def _write_results(
    frames: dict[str, pd.DataFrame],
    output_dir: Path,
    config: AthShortConfig,
    *,
    source: str,
    interval: str,
    range_: str,
    failures: dict[str, str],
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_trades = []
    for symbol, frame in frames.items():
        trades = backtest_ath_short(frame, config)
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
        "strategy": "AthBreakoutShort",
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


def run_ath_short_frames(
    frames: dict[str, pd.DataFrame],
    output_dir: Path,
    config: AthShortConfig,
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


def run_ath_short_equities(
    data_dir: Path,
    output_dir: Path,
    symbols: list[str],
    config: AthShortConfig,
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
