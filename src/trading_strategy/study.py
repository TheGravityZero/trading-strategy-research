from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .backtest import BacktestConfig, run_event_backtest
from .events import DetectorConfig, attach_forward_returns, detect_events
from .features import build_features
from .utils.crypto import load_crypto_symbol


# Public compatibility alias. New code should import from trading_strategy.utils.crypto.
load_symbol = load_crypto_symbol


def add_splits(events: pd.DataFrame) -> pd.DataFrame:
    result = events.copy()
    result["split"] = pd.cut(
        result["timestamp"],
        bins=[
            pd.Timestamp("2025-07-01", tz="UTC"),
            pd.Timestamp("2026-01-01", tz="UTC"),
            pd.Timestamp("2026-04-01", tz="UTC"),
            pd.Timestamp("2026-07-01", tz="UTC"),
        ],
        labels=["research", "validation", "test"],
        right=False,
    )
    return result


def add_market_clusters(events: pd.DataFrame, minutes: int = 10) -> pd.DataFrame:
    result = events.sort_values("timestamp").reset_index(drop=True).copy()
    if result.empty:
        result["cluster_id"] = pd.Series(dtype=int)
        return result
    new_cluster = result["timestamp"].diff().gt(pd.Timedelta(minutes=minutes))
    new_cluster.iloc[0] = True
    result["cluster_id"] = new_cluster.cumsum().astype(int) - 1
    breadth = result.groupby("cluster_id")["symbol"].transform("nunique")
    result["cluster_breadth"] = breadth
    result["event_scope"] = breadth.gt(1).map(
        {True: "market-wide", False: "local"}
    )
    return result


def event_study(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (split, scope), group in events.groupby(
        ["split", "event_scope"], observed=True
    ):
        for horizon in (1, 5, 15, 30):
            series = group[f"reversal_{horizon}m"].dropna()
            rows.append(
                {
                    "split": str(split),
                    "event_scope": scope,
                    "horizon_minutes": horizon,
                    "events": len(series),
                    "clusters": group.loc[series.index, "cluster_id"].nunique(),
                    "mean_reversal": series.mean(),
                    "median_reversal": series.median(),
                    "positive_rate": (series > 0).mean(),
                }
            )
    return pd.DataFrame(rows)


def run_large_study(
    raw_dir: Path,
    output_dir: Path,
    symbols: list[str],
    oi_drop_threshold: float = -0.002,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    start = pd.Timestamp("2025-07-01", tz="UTC")
    end = pd.Timestamp("2026-07-01", tz="UTC")
    manifests = []
    event_frames = []
    detector = DetectorConfig(oi_drop_threshold=oi_drop_threshold)
    for symbol in symbols:
        frame, manifest = load_crypto_symbol(raw_dir, symbol, start, end)
        manifests.append(manifest)
        features = build_features(frame)
        events = attach_forward_returns(
            features, detect_events(features, detector)
        )
        event_frames.append(events)
        print(
            f"{symbol}: {len(frame):,} rows, {len(events):,} events, "
            f"OI {manifest['oi_coverage']:.2%}",
            flush=True,
        )
    events = pd.concat(event_frames, ignore_index=True)
    events = add_splits(add_market_clusters(events))
    trades = run_event_backtest(
        events, BacktestConfig(strategy_mode="reversal")
    )
    study = event_study(trades)
    split_summary = (
        trades.dropna(subset=["net_return"])
        .groupby("split", observed=True)
        .agg(
            events=("event_id", "size"),
            clusters=("cluster_id", "nunique"),
            mean_gross=("gross_return", "mean"),
            mean_net=("net_return", "mean"),
            hit_rate=("net_return", lambda value: (value > 0).mean()),
        )
        .reset_index()
    )
    manifest = {
        "period_start": str(start),
        "period_end_exclusive": str(end),
        "symbols": symbols,
        "total_kline_rows": sum(item["kline_rows"] for item in manifests),
        "total_metric_rows": sum(item["metric_rows"] for item in manifests),
        "total_events": len(events),
        "total_clusters": int(events["cluster_id"].nunique()),
        "per_symbol": manifests,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    trades.to_csv(output_dir / "events_and_trades.csv", index=False)
    study.to_csv(output_dir / "event_study.csv", index=False)
    split_summary.to_csv(output_dir / "split_summary.csv", index=False)
    return manifest
