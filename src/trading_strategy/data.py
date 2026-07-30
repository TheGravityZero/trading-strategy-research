from __future__ import annotations

import io
import time
import urllib.error
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd

KLINE_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "trades",
    "taker_buy_volume",
    "taker_buy_quote_volume",
    "ignore",
]
NUMERIC_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trades",
    "taker_buy_volume",
    "taker_buy_quote_volume",
]
BASE_URL = "https://data.binance.vision/data/futures/um/daily"


def _download(request: urllib.request.Request, timeout: int, attempts: int = 4) -> bytes:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
    assert last_error is not None
    raise last_error


def archive_url(symbol: str, interval: str, day: date) -> str:
    stamp = day.isoformat()
    filename = f"{symbol}-{interval}-{stamp}.zip"
    return f"{BASE_URL}/klines/{symbol}/{interval}/{filename}"


def metrics_archive_url(symbol: str, day: date) -> str:
    stamp = day.isoformat()
    filename = f"{symbol}-metrics-{stamp}.zip"
    return f"{BASE_URL}/metrics/{symbol}/{filename}"


def monthly_archive_url(
    symbol: str, interval: str, month: date, dataset: str
) -> str:
    stamp = month.strftime("%Y-%m")
    if dataset == "klines":
        filename = f"{symbol}-{interval}-{stamp}.zip"
        return (
            "https://data.binance.vision/data/futures/um/monthly/"
            f"klines/{symbol}/{interval}/{filename}"
        )
    if dataset == "metrics":
        filename = f"{symbol}-metrics-{stamp}.zip"
        return (
            "https://data.binance.vision/data/futures/um/monthly/"
            f"metrics/{symbol}/{filename}"
        )
    raise ValueError(f"Unsupported dataset: {dataset}")


def download_daily_kline(
    symbol: str,
    interval: str,
    day: date,
    raw_dir: Path,
    timeout: int = 30,
) -> Path:
    symbol = symbol.upper()
    destination = raw_dir / symbol / interval / f"{symbol}-{interval}-{day}.zip"
    if destination.exists() and destination.stat().st_size > 0:
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        archive_url(symbol, interval, day),
        headers={"User-Agent": "liquidation-trading_strategy-research/0.1"},
    )
    try:
        payload = _download(request, timeout)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise FileNotFoundError(
                f"Binance archive is unavailable for {symbol} {interval} {day}"
            ) from exc
        raise

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        bad_file = archive.testzip()
        if bad_file:
            raise ValueError(f"Corrupt file in archive: {bad_file}")
    destination.write_bytes(payload)
    return destination


def download_daily_metrics(
    symbol: str,
    day: date,
    raw_dir: Path,
    timeout: int = 30,
) -> Path:
    symbol = symbol.upper()
    destination = raw_dir / symbol / "metrics" / f"{symbol}-metrics-{day}.zip"
    if destination.exists() and destination.stat().st_size > 0:
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        metrics_archive_url(symbol, day),
        headers={"User-Agent": "liquidation-trading_strategy-research/0.1"},
    )
    try:
        payload = _download(request, timeout)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise FileNotFoundError(
                f"Binance metrics archive is unavailable for {symbol} {day}"
            ) from exc
        raise
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        bad_file = archive.testzip()
        if bad_file:
            raise ValueError(f"Corrupt file in archive: {bad_file}")
    destination.write_bytes(payload)
    return destination


def download_daily_aggtrades(
    symbol: str, day: date, raw_dir: Path, timeout: int = 60
) -> Path:
    symbol = symbol.upper()
    filename = f"{symbol}-aggTrades-{day}.zip"
    destination = raw_dir / symbol / "aggTrades" / filename
    if destination.exists() and destination.stat().st_size > 0:
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    url = (
        "https://data.binance.vision/data/futures/um/daily/"
        f"aggTrades/{symbol}/{filename}"
    )
    request = urllib.request.Request(
        url, headers={"User-Agent": "liquidation-trading_strategy-research/0.1"}
    )
    payload = _download(request, timeout)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        bad_file = archive.testzip()
        if bad_file:
            raise ValueError(f"Corrupt file in archive: {bad_file}")
    destination.write_bytes(payload)
    return destination


def read_aggtrades_archive(path: Path) -> pd.DataFrame:
    columns = [
        "agg_id", "price", "quantity", "first_id", "last_id",
        "time", "buyer_maker",
    ]
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".csv")]
        with archive.open(names[0]) as source:
            frame = pd.read_csv(source, header=None, names=columns)
    frame = frame[pd.to_numeric(frame["agg_id"], errors="coerce").notna()].copy()
    frame["agg_id"] = pd.to_numeric(frame["agg_id"]).astype("int64")
    frame["price"] = pd.to_numeric(frame["price"])
    frame["quantity"] = pd.to_numeric(frame["quantity"])
    frame["time"] = pd.to_numeric(frame["time"]).astype("int64")
    frame["timestamp"] = pd.to_datetime(frame["time"], unit="ms", utc=True)
    frame["buyer_maker"] = frame["buyer_maker"].astype(str).str.lower().eq("true")
    return frame[["agg_id", "price", "quantity", "timestamp", "buyer_maker"]]


def download_monthly_archive(
    symbol: str,
    interval: str,
    month: date,
    dataset: str,
    raw_dir: Path,
    timeout: int = 60,
) -> Path:
    symbol = symbol.upper()
    stamp = month.strftime("%Y-%m")
    if dataset == "klines":
        filename = f"{symbol}-{interval}-{stamp}.zip"
        destination = raw_dir / symbol / interval / "monthly" / filename
    elif dataset == "metrics":
        filename = f"{symbol}-metrics-{stamp}.zip"
        destination = raw_dir / symbol / "metrics" / "monthly" / filename
    else:
        raise ValueError(f"Unsupported dataset: {dataset}")
    if destination.exists() and destination.stat().st_size > 0:
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        monthly_archive_url(symbol, interval, month, dataset),
        headers={"User-Agent": "liquidation-trading_strategy-research/0.1"},
    )
    try:
        payload = _download(request, timeout)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise FileNotFoundError(
                f"Monthly archive unavailable: {dataset} {symbol} {stamp}"
            ) from exc
        raise
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        bad_file = archive.testzip()
        if bad_file:
            raise ValueError(f"Corrupt file in archive: {bad_file}")
    destination.write_bytes(payload)
    return destination


def read_metrics_archive(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError(f"Expected one CSV in {path}, found {len(csv_names)}")
        with archive.open(csv_names[0]) as source:
            frame = pd.read_csv(source)
    required = {"create_time", "symbol", "sum_open_interest"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing metrics columns in {path}: {sorted(missing)}")
    frame["timestamp"] = pd.to_datetime(frame["create_time"], utc=True)
    numeric = [
        column
        for column in frame.columns
        if column not in {"create_time", "symbol", "timestamp"}
    ]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["symbol"] = frame["symbol"].str.upper()
    return frame.drop(columns=["create_time"]).sort_values("timestamp").reset_index(drop=True)


def read_kline_archive(path: Path, symbol: str | None = None) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError(f"Expected one CSV in {path}, found {len(csv_names)}")
        with archive.open(csv_names[0]) as source:
            frame = pd.read_csv(source, header=None, names=KLINE_COLUMNS)

    # Some newer archives contain a header, while older ones do not.
    frame = frame[pd.to_numeric(frame["open_time"], errors="coerce").notna()].copy()
    frame["open_time"] = pd.to_numeric(frame["open_time"]).astype("int64")
    frame["timestamp"] = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["symbol"] = (symbol or path.name.split("-")[0]).upper()
    frame = frame.sort_values("timestamp").drop_duplicates("timestamp")
    return frame[
        [
            "timestamp",
            "symbol",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_volume",
            "trades",
            "taker_buy_volume",
            "taker_buy_quote_volume",
        ]
    ].reset_index(drop=True)


def validate_klines(frame: pd.DataFrame, interval_minutes: int = 1) -> list[str]:
    problems: list[str] = []
    if frame.empty:
        return ["dataset is empty"]
    if frame["timestamp"].duplicated().any():
        problems.append("duplicate timestamps")
    if not frame["timestamp"].is_monotonic_increasing:
        problems.append("timestamps are not sorted")
    if frame[["open", "high", "low", "close", "volume"]].isna().any().any():
        problems.append("missing required numeric values")
    if (frame["volume"] < 0).any():
        problems.append("negative volume")
    invalid_ohlc = (
        (frame["high"] < frame[["open", "close", "low"]].max(axis=1))
        | (frame["low"] > frame[["open", "close", "high"]].min(axis=1))
    )
    if invalid_ohlc.any():
        problems.append("invalid OHLC relation")
    gaps = frame["timestamp"].diff().dropna()
    expected = pd.Timedelta(minutes=interval_minutes)
    if (gaps != expected).any():
        problems.append(f"{int((gaps != expected).sum())} timestamp gaps")
    return problems
