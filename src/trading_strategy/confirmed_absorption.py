from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data import read_kline_archive
from .features import build_features
from .hypotheses import summarize_group


def _monthly_klines(raw_dir: Path, symbol: str) -> pd.DataFrame:
    paths = sorted((raw_dir / symbol / "1m" / "monthly").glob("*.zip"))
    frame = pd.concat(
        [read_kline_archive(path, symbol) for path in paths],
        ignore_index=True,
    )
    return frame.sort_values("timestamp").drop_duplicates("timestamp")


def _evaluate_event(
    frame: pd.DataFrame,
    position: int,
    direction: float,
    *,
    confirmation_minutes: int = 3,
    impact_ratio: float = 0.5,
    flow_weakening: float = 0.15,
) -> dict:
    event = frame.iloc[position]
    candidates = frame.iloc[position + 1 : position + confirmation_minutes + 1]
    result = {
        "no_new_extreme": False,
        "impact_decayed": False,
        "flow_weakened": False,
        "midpoint_reentered": False,
        "confirmed": False,
        "confirmation_timestamp": pd.NaT,
        "confirmation_delay_minutes": np.nan,
    }
    if len(candidates) < confirmation_minutes:
        return result

    midpoint = (event["high"] + event["low"]) / 2
    event_flow = direction * event["taker_imbalance"]
    event_efficiency = event["impulse_efficiency"]
    no_extreme_so_far = True

    for delay, (_, candidate) in enumerate(candidates.iterrows(), start=1):
        if direction < 0:
            no_extreme_so_far &= candidate["low"] >= event["low"]
        else:
            no_extreme_so_far &= candidate["high"] <= event["high"]
        impact_decayed = (
            np.isfinite(event_efficiency)
            and event_efficiency > 0
            and candidate["impulse_efficiency"] / event_efficiency <= impact_ratio
        )
        aligned_flow = direction * candidate["taker_imbalance"]
        flow_weakened = aligned_flow <= event_flow - flow_weakening
        midpoint_reentered = -direction * (candidate["close"] - midpoint) >= 0

        result["no_new_extreme"] |= bool(no_extreme_so_far)
        result["impact_decayed"] |= bool(impact_decayed)
        result["flow_weakened"] |= bool(flow_weakened)
        result["midpoint_reentered"] |= bool(midpoint_reentered)

        if (
            no_extreme_so_far
            and impact_decayed
            and flow_weakened
            and midpoint_reentered
        ):
            result["confirmed"] = True
            result["confirmation_timestamp"] = candidate["timestamp"]
            result["confirmation_delay_minutes"] = delay
            result["entry_price"] = candidate["close"]
            confirmation_position = position + delay
            for horizon in (5, 15, 30):
                future_position = confirmation_position + horizon
                if future_position < len(frame):
                    future_close = frame.iloc[future_position]["close"]
                    raw_return = future_close / candidate["close"] - 1
                    result[f"reversal_{horizon}m"] = -direction * raw_return
                else:
                    result[f"reversal_{horizon}m"] = np.nan
            break
    return result


def run_confirmed_absorption(
    events_path: Path,
    raw_dir: Path,
    thresholds_path: Path,
    output_dir: Path,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(events_path, parse_dates=["timestamp"])
    thresholds = json.loads(thresholds_path.read_text(encoding="utf-8"))
    oi_threshold = thresholds["oi_threshold_research_q25"]
    selected = events[
        events["split"].isin(["research", "validation"])
        & (events["oi_change_15m"] <= oi_threshold)
    ].copy()
    records = []
    for symbol, symbol_events in selected.groupby("symbol"):
        features = build_features(_monthly_klines(raw_dir, symbol))
        positions = pd.Series(
            np.arange(len(features)), index=features["timestamp"]
        )
        for _, event in symbol_events.iterrows():
            position = positions.get(event["timestamp"])
            base = event.to_dict()
            if position is None:
                base["confirmed"] = False
            else:
                base.update(
                    _evaluate_event(features, int(position), event["direction"])
                )
            records.append(base)
        print(f"{symbol}: {len(symbol_events)} strong-OI events", flush=True)
    evaluated = pd.DataFrame(records)

    gates = []
    for split in ("research", "validation"):
        split_frame = evaluated[evaluated["split"] == split]
        progressive = pd.Series(True, index=split_frame.index)
        for gate in (
            "no_new_extreme",
            "impact_decayed",
            "flow_weakened",
            "midpoint_reentered",
        ):
            progressive &= split_frame[gate].fillna(False)
            gates.append(
                {
                    "split": split,
                    "gate": gate,
                    "standalone_pass_rate": split_frame[gate].mean(),
                    "progressive_pass_rate": progressive.mean(),
                    "progressive_events": int(progressive.sum()),
                }
            )

    confirmed = evaluated[evaluated["confirmed"].fillna(False)].copy()
    comparison_rows = []
    for split in ("research", "validation"):
        comparison_rows.extend(
            summarize_group(
                confirmed[confirmed["split"] == split],
                "confirmed_absorption",
                split,
            )
        )
    comparison = pd.DataFrame(comparison_rows)
    gates_frame = pd.DataFrame(gates)
    evaluated.to_csv(output_dir / "evaluated_events.csv", index=False)
    gates_frame.to_csv(output_dir / "gate_funnel.csv", index=False)
    comparison.to_csv(output_dir / "confirmed_results.csv", index=False)
    config = {
        "oi_threshold": oi_threshold,
        "confirmation_minutes": 3,
        "maximum_impact_ratio": 0.5,
        "minimum_flow_weakening": 0.15,
        "requires_no_new_extreme": True,
        "requires_midpoint_reentry": True,
        "entry": "confirmation minute close",
        "test_used": False,
    }
    (output_dir / "config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )
    return {"gates": gates_frame, "results": comparison, "config": config}

