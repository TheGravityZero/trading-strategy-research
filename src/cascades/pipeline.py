from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .backtest import BacktestConfig, run_event_backtest, summarize
from .events import DetectorConfig, attach_forward_returns, detect_events
from .features import build_features


def run_pipeline(
    klines: pd.DataFrame,
    output_dir: Path,
    detector: DetectorConfig = DetectorConfig(),
    backtest: BacktestConfig = BacktestConfig(),
) -> dict[str, float | int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    feature_frames = []
    event_frames = []
    for _, symbol_frame in klines.groupby("symbol", sort=False):
        features = build_features(symbol_frame)
        events = detect_events(features, detector)
        events = attach_forward_returns(features, events)
        feature_frames.append(features)
        event_frames.append(events)
    all_features = pd.concat(feature_frames, ignore_index=True)
    all_events = pd.concat(event_frames, ignore_index=True)
    all_events = all_events.sort_values("timestamp").reset_index(drop=True)
    all_events["event_id"] = range(len(all_events))
    trades = run_event_backtest(all_events, backtest)
    metrics = summarize(trades)

    all_features.to_csv(output_dir / "features.csv.gz", index=False)
    trades.to_csv(output_dir / "events_and_trades.csv", index=False)
    (output_dir / "summary.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    return metrics

