from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

COST = 14 / 10_000
HORIZONS = (5, 15, 30)


def cluster_bootstrap_ci(
    frame: pd.DataFrame,
    column: str,
    *,
    iterations: int = 2_000,
    seed: int = 17,
) -> tuple[float, float]:
    grouped = [
        group[column].dropna().to_numpy()
        for _, group in frame.groupby("cluster_id")
    ]
    grouped = [values for values in grouped if len(values)]
    if not grouped:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    estimates = np.empty(iterations)
    for index in range(iterations):
        sample = rng.integers(0, len(grouped), len(grouped))
        values = np.concatenate([grouped[position] for position in sample])
        estimates[index] = values.mean()
    low, high = np.quantile(estimates, [0.025, 0.975])
    return float(low), float(high)


def summarize_group(
    frame: pd.DataFrame, name: str, split: str
) -> list[dict]:
    rows = []
    for horizon in HORIZONS:
        column = f"reversal_{horizon}m"
        valid = frame.dropna(subset=[column])
        low, high = cluster_bootstrap_ci(valid, column)
        gross = valid[column]
        rows.append(
            {
                "variant": name,
                "split": split,
                "horizon_minutes": horizon,
                "events": len(valid),
                "clusters": valid["cluster_id"].nunique(),
                "mean_gross_bps": gross.mean() * 10_000,
                "median_gross_bps": gross.median() * 10_000,
                "ci_low_bps": low * 10_000,
                "ci_high_bps": high * 10_000,
                "mean_net_bps": (gross.mean() - COST) * 10_000,
                "beats_cost_rate": (gross > COST).mean(),
            }
        )
    return rows


def run_hypothesis_analysis(events_path: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(events_path, parse_dates=["timestamp"])
    research = events[events["split"] == "research"].copy()

    oi_edges = research["oi_change_15m"].quantile([0.25, 0.5, 0.75])
    oi_threshold = float(oi_edges.loc[0.25])
    edges = [-np.inf, *oi_edges.tolist(), np.inf]
    labels = ["Q1_deepest", "Q2", "Q3", "Q4_shallowest"]
    events["oi_bucket"] = pd.cut(
        events["oi_change_15m"], bins=edges, labels=labels, include_lowest=True
    )
    events["h1_strong_oi"] = events["oi_change_15m"] <= oi_threshold

    h1_research = events[
        (events["split"] == "research") & events["h1_strong_oi"]
    ]
    absorption_threshold = float(
        h1_research["efficiency_ratio"].quantile(0.25)
    )
    events["h2_absorption"] = (
        events["h1_strong_oi"]
        & (events["efficiency_ratio"] <= absorption_threshold)
    )

    bucket_rows = []
    for split in ("research", "validation"):
        split_frame = events[events["split"] == split]
        for bucket in labels:
            bucket_frame = split_frame[split_frame["oi_bucket"] == bucket]
            bucket_rows.extend(summarize_group(bucket_frame, bucket, split))
    bucket_table = pd.DataFrame(bucket_rows)

    comparison_rows = []
    for split in ("research", "validation"):
        split_frame = events[events["split"] == split]
        comparison_rows.extend(summarize_group(split_frame, "baseline", split))
        comparison_rows.extend(
            summarize_group(
                split_frame[split_frame["h1_strong_oi"]],
                "h1_strong_oi",
                split,
            )
        )
        comparison_rows.extend(
            summarize_group(
                split_frame[split_frame["h2_absorption"]],
                "h1_plus_h2_absorption",
                split,
            )
        )
    comparison = pd.DataFrame(comparison_rows)

    thresholds = {
        "cost_bps": 14.0,
        "oi_threshold_research_q25": oi_threshold,
        "absorption_efficiency_research_q25": absorption_threshold,
        "test_used_for_thresholds": False,
    }
    bucket_table.to_csv(output_dir / "hypothesis_1_oi_buckets.csv", index=False)
    comparison.to_csv(output_dir / "hypothesis_comparison.csv", index=False)
    events[
        [
            "timestamp",
            "symbol",
            "split",
            "cluster_id",
            "oi_change_15m",
            "efficiency_ratio",
            "oi_bucket",
            "h1_strong_oi",
            "h2_absorption",
        ]
    ].to_csv(output_dir / "event_labels.csv", index=False)
    (output_dir / "thresholds.json").write_text(
        json.dumps(thresholds, indent=2), encoding="utf-8"
    )
    return {
        "thresholds": thresholds,
        "oi_buckets": bucket_table,
        "comparison": comparison,
    }

