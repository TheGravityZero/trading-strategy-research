"""Reusable US-equity data acquisition and calendar-aware pivot utilities."""

from __future__ import annotations

import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd


STOCK_UNIVERSES = {
    "it": [
        "MSFT", "AAPL", "GOOGL", "META", "AMZN",
        "ORCL", "CRM", "NOW", "ADBE", "PLTR",
    ],
    "semiconductors": [
        "NVDA", "AMD", "AVGO", "QCOM", "INTC", "MU", "AMAT",
        "LRCX", "KLAC", "TSM", "SNDK", "NBIS", "CRWV",
    ],
    "oil": [
        "XOM", "CVX", "COP", "OXY", "EOG",
        "SLB", "HAL", "MPC", "VLO", "FANG",
    ],
    "metals": [
        "NEM", "GOLD", "AEM", "FCX", "SCCO",
        "AA", "CLF", "NUE", "STLD", "MP",
    ],
}

DEFAULT_STOCK_SYMBOLS = [
    symbol
    for sector in ("it", "semiconductors", "oil", "metals")
    for symbol in STOCK_UNIVERSES[sector]
]


def stock_symbols(
    sector: str, symbols: list[str] | None = None
) -> list[str]:
    """Resolve an explicit symbol override or one named sector universe."""
    if symbols:
        return [symbol.upper() for symbol in symbols]
    if sector == "all":
        return DEFAULT_STOCK_SYMBOLS.copy()
    try:
        return STOCK_UNIVERSES[sector].copy()
    except KeyError as exc:
        raise ValueError(f"Unknown stock sector: {sector}") from exc


def download_stock_hourly(
    symbol: str,
    output_dir: Path,
    range_: str = "1y",
    retries: int = 5,
) -> Path:
    """Download regular-session hourly OHLCV from Yahoo's chart endpoint."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{symbol}.csv"
    if path.exists() and path.stat().st_size > 1_000:
        return path
    params = urlencode(
        {
            "range": range_,
            "interval": "1h",
            "includePrePost": "false",
            "events": "div,splits",
        }
    )
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?{params}"
    error: Exception | None = None
    for attempt in range(retries):
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=45) as response:
                payload = json.load(response)
            result = payload["chart"]["result"][0]
            quote = result["indicators"]["quote"][0]
            frame = pd.DataFrame(
                {
                    "timestamp": pd.to_datetime(
                        result["timestamp"], unit="s", utc=True
                    ),
                    "open": quote["open"],
                    "high": quote["high"],
                    "low": quote["low"],
                    "close": quote["close"],
                    "volume": quote["volume"],
                }
            ).dropna(subset=["open", "high", "low", "close"])
            frame["symbol"] = symbol
            frame.to_csv(path, index=False)
            return path
        except Exception as exc:
            error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to download {symbol}: {error}")


def load_stock_hourly(path: Path) -> pd.DataFrame:
    """Read a cached hourly equity file in canonical timestamp order."""
    return (
        pd.read_csv(path, parse_dates=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )


def confirmed_stock_weekly_pivots(frame: pd.DataFrame) -> pd.DataFrame:
    """Build causal 2-left/2-right weekly pivots in New York market time."""
    work = frame.copy()
    local = work["timestamp"].dt.tz_convert("America/New_York")
    work["week_start"] = (
        local.dt.normalize() - pd.to_timedelta(local.dt.dayofweek, unit="D")
    )
    weekly = work.groupby("week_start").agg(high=("high", "max"), low=("low", "min"))
    rows: list[dict] = []
    for position in range(2, len(weekly) - 2):
        window = weekly.iloc[position - 2 : position + 3]
        current = weekly.iloc[position]
        week = weekly.index[position]
        available = weekly.index[position + 2] + pd.Timedelta(days=7)
        if current.low == window.low.min():
            rows.append(
                {
                    "kind": "low",
                    "level": current.low,
                    "pivot_week": week,
                    "available_at": available,
                }
            )
        if current.high == window.high.max():
            rows.append(
                {
                    "kind": "high",
                    "level": current.high,
                    "pivot_week": week,
                    "available_at": available,
                }
            )
    return pd.DataFrame(rows)


# Compatibility aliases used by earlier notebooks and scripts.
DEFAULT_SYMBOLS = DEFAULT_STOCK_SYMBOLS
download_yahoo_hourly = download_stock_hourly
confirmed_weekly_pivots = confirmed_stock_weekly_pivots
