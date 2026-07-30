"""Reusable data-loading utilities for Binance USD-M futures research."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..data import read_kline_archive, read_metrics_archive


def crypto_archive_paths(
    raw_dir: Path, symbol: str, dataset: str
) -> list[Path]:
    """Return locally cached archive paths for one crypto symbol."""
    if dataset == "klines":
        return sorted((raw_dir / symbol / "1m" / "monthly").glob("*.zip"))
    if dataset == "metrics":
        return sorted(
            path
            for path in (raw_dir / symbol / "metrics").glob("**/*.zip")
            if "monthly" not in path.parts
        )
    raise ValueError(f"Unsupported crypto dataset: {dataset}")


def load_crypto_symbol(
    raw_dir: Path, symbol: str, start: pd.Timestamp, end: pd.Timestamp
) -> tuple[pd.DataFrame, dict]:
    """Load and causally merge minute klines with delayed futures metrics."""
    kline_paths = crypto_archive_paths(raw_dir, symbol, "klines")
    metric_paths = crypto_archive_paths(raw_dir, symbol, "metrics")
    if not kline_paths:
        raise FileNotFoundError(f"No minute kline archives for {symbol}")
    if not metric_paths:
        raise FileNotFoundError(f"No futures metric archives for {symbol}")

    klines = pd.concat(
        [read_kline_archive(path, symbol) for path in kline_paths],
        ignore_index=True,
    ).sort_values("timestamp")
    metrics = pd.concat(
        [read_metrics_archive(path) for path in metric_paths],
        ignore_index=True,
    ).sort_values("timestamp")
    klines = klines[
        (klines["timestamp"] >= start) & (klines["timestamp"] < end)
    ].drop_duplicates("timestamp")
    metrics = metrics[
        (metrics["timestamp"] >= start) & (metrics["timestamp"] < end)
    ].drop_duplicates("timestamp")

    # A metric stamped at t is conservatively available to a strategy at t+1m.
    metrics["timestamp"] += pd.Timedelta(minutes=1)
    merged = pd.merge_asof(
        klines,
        metrics,
        on="timestamp",
        by="symbol",
        direction="backward",
        tolerance=pd.Timedelta(minutes=5),
    )
    manifest = {
        "symbol": symbol,
        "kline_archives": len(kline_paths),
        "metric_archives": len(metric_paths),
        "kline_rows": len(klines),
        "metric_rows": len(metrics),
        "minute_gaps": int(
            (klines["timestamp"].diff().dropna() != pd.Timedelta(minutes=1)).sum()
        ),
        "metric_gaps": int(
            (metrics["timestamp"].diff().dropna() != pd.Timedelta(minutes=5)).sum()
        ),
        "oi_coverage": float(merged["sum_open_interest"].notna().mean()),
        "first_timestamp": str(klines["timestamp"].min()),
        "last_timestamp": str(klines["timestamp"].max()),
    }
    return merged, manifest


# Backwards-friendly name for strategy modules written before the utils split.
load_symbol = load_crypto_symbol
