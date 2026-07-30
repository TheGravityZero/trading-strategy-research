from __future__ import annotations

import gzip
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

BASE = "https://fapi.binance.com/fapi/v1/aggTrades"


def fetch_window(
    symbol: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    cache_path: Path,
    *,
    request_pause: float = 0.55,
) -> pd.DataFrame:
    if cache_path.exists():
        return pd.read_csv(cache_path, parse_dates=["timestamp"])
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    cursor = start_ms
    rows = []
    while cursor <= end_ms:
        query = urllib.parse.urlencode(
            {
                "symbol": symbol,
                "startTime": cursor,
                "endTime": end_ms,
                "limit": 1000,
            }
        )
        request = urllib.request.Request(
            f"{BASE}?{query}",
            headers={"User-Agent": "liquidation-trading_strategy-research/0.1"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read())
        if not payload:
            break
        rows.extend(payload)
        next_cursor = int(payload[-1]["T"]) + 1
        if next_cursor <= cursor or len(payload) < 1000:
            break
        cursor = next_cursor
        time.sleep(request_pause)
    frame = pd.DataFrame(rows)
    if frame.empty:
        frame = pd.DataFrame(
            columns=["agg_id", "price", "quantity", "timestamp", "buyer_maker"]
        )
    else:
        frame = frame.rename(
            columns={
                "a": "agg_id",
                "p": "price",
                "q": "quantity",
                "T": "time",
                "m": "buyer_maker",
            }
        )
        frame["price"] = pd.to_numeric(frame["price"])
        frame["quantity"] = pd.to_numeric(frame["quantity"])
        frame["timestamp"] = pd.to_datetime(frame["time"], unit="ms", utc=True)
        frame = frame[
            ["agg_id", "price", "quantity", "timestamp", "buyer_maker"]
        ].drop_duplicates("agg_id")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(cache_path, "wt", encoding="utf-8") as target:
        frame.to_csv(target, index=False)
    return frame


def deterministic_sample(events: pd.DataFrame, per_group: int = 5) -> pd.DataFrame:
    selected = []
    for _, group in events.groupby(["split", "symbol"], sort=True):
        group = group.sort_values("timestamp")
        if len(group) <= per_group:
            selected.append(group)
        elif per_group == 1:
            selected.append(group.iloc[[0]])
        else:
            positions = [
                round(index * (len(group) - 1) / (per_group - 1))
                for index in range(per_group)
            ]
            selected.append(group.iloc[positions])
    return pd.concat(selected).drop_duplicates(["symbol", "timestamp"])
