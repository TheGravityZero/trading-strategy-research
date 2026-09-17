#!/usr/bin/env python3
"""Build separate hourly crypto/U.S.-equity correlation experiments."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from trading_strategy.analysis.cross_asset_correlation import (
    absolute_return_correlation,
    downside_correlation,
    lag_correlation,
    pearson_correlation,
    rolling_pearson,
    spearman_correlation,
)
from trading_strategy.data import download_daily_kline, read_kline_archive
from trading_strategy.utils.stocks import download_stock_hourly, load_stock_hourly


CRYPTO = ["BTCUSDT", "ETHUSDT", "HYPEUSDT"]
STOCKS = ["SPY", "QQQ", "NVDA", "TSLA", "COIN", "MSTR"]
METHODS = {
    "pearson": "Hourly Pearson",
    "spearman": "Hourly Spearman",
    "rolling-pearson-5d": "Rolling Pearson — 5 trading days",
    "lag-correlation": "Lag correlation — −2 to +2 hours",
    "downside-correlation": "Downside correlation",
    "absolute-return-correlation": "Absolute-return correlation",
}


def crypto_hourly(
    symbol: str, start: date, end: date, raw_dir: Path
) -> pd.Series:
    days = [start + timedelta(days=n) for n in range((end - start).days)]
    with ThreadPoolExecutor(max_workers=8) as executor:
        paths = list(
            executor.map(
                lambda day: download_daily_kline(
                    symbol, "1m", day, raw_dir, timeout=20
                ),
                days,
            )
        )
    frame = pd.concat([read_kline_archive(path, symbol) for path in paths])
    # U.S. bars start at :30 UTC during daylight-saving time. A crypto bin with
    # the same label covers exactly the corresponding equity bar interval.
    return (
        frame.set_index("timestamp")["close"]
        .resample("1h", origin="start_day", offset="30min", label="left")
        .last()
        .rename(symbol)
    )


def stock_hourly(symbol: str, data_dir: Path) -> pd.Series:
    path = download_stock_hourly(symbol, data_dir, range_="1mo")
    frame = load_stock_hourly(path)
    return frame.set_index("timestamp")["close"].rename(symbol)


def synchronized_returns(
    crypto: dict[str, pd.Series], stocks: dict[str, pd.Series], start: date, end: date
) -> tuple[pd.DataFrame, pd.Series]:
    stock_prices = pd.concat(stocks.values(), axis=1, sort=False).sort_index()
    stock_prices = stock_prices[
        (stock_prices.index >= pd.Timestamp(start, tz="UTC"))
        & (stock_prices.index < pd.Timestamp(end, tz="UTC"))
    ]
    # Exclude the first bar of each U.S. session: its stock return contains the
    # overnight gap and is not comparable to a one-hour crypto return.
    local = stock_prices.index.tz_convert("America/New_York")
    dates = pd.Series(local.date, index=stock_prices.index, name="trading_date")
    first_bar = dates.ne(dates.shift())
    stock_returns = np.log(stock_prices / stock_prices.shift(1)).loc[~first_bar]
    crypto_prices = pd.concat(
        crypto.values(), axis=1, sort=False
    ).reindex(stock_prices.index)
    crypto_returns = np.log(crypto_prices / crypto_prices.shift(1)).loc[~first_bar]
    returns = pd.concat([crypto_returns, stock_returns], axis=1).dropna()
    return returns, dates.reindex(returns.index)


def markdown_table(frame: pd.DataFrame) -> list[str]:
    header = "| | " + " | ".join(frame.columns) + " |"
    separator = "|---|" + "---:|" * len(frame.columns)
    rows = [
        f"| {index} | " + " | ".join(f"{value:.3f}" for value in row) + " |"
        for index, row in frame.iterrows()
    ]
    return [header, separator, *rows]


def write_matrix_report(
    root: Path, slug: str, matrix: pd.DataFrame, setup: list[str]
) -> None:
    directory = root / slug
    directory.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(directory / "matrix.csv")
    lines = [f"# {METHODS[slug]}", "", *setup, "", *markdown_table(matrix)]
    (directory / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--end", type=date.fromisoformat, default=date.today())
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--crypto", nargs="+", default=CRYPTO)
    parser.add_argument("--stocks", nargs="+", default=STOCKS)
    parser.add_argument("--data-dir", type=Path, default=Path("data/cross-asset"))
    parser.add_argument("--output-dir", type=Path, default=Path("research/reports/cross-asset-correlation"))
    args = parser.parse_args()
    start = args.end - timedelta(days=args.days)
    crypto_symbols = [value.upper() for value in args.crypto]
    stock_symbols = [value.upper() for value in args.stocks]
    crypto = {
        symbol: crypto_hourly(symbol, start, args.end, args.data_dir / "crypto")
        for symbol in crypto_symbols
    }
    stocks = {
        symbol: stock_hourly(symbol, args.data_dir / "stocks")
        for symbol in stock_symbols
    }
    returns, dates = synchronized_returns(crypto, stocks, start, args.end)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    returns.to_csv(args.output_dir / "synchronized_returns.csv")
    setup = [
        f"Period: `{start}` — `{args.end}` (end exclusive).",
        f"Assets: `{', '.join(crypto_symbols)}` vs `{', '.join(stock_symbols)}`.",
        f"Observations: `{len(returns)}` synchronized intraday hourly returns. "
        "The first U.S. session bar is excluded to remove overnight returns.",
    ]
    matrices = {
        "pearson": pearson_correlation(returns, crypto_symbols, stock_symbols),
        "spearman": spearman_correlation(returns, crypto_symbols, stock_symbols),
        "downside-correlation": downside_correlation(returns, crypto_symbols, stock_symbols),
        "absolute-return-correlation": absolute_return_correlation(returns, crypto_symbols, stock_symbols),
    }
    for slug, matrix in matrices.items():
        write_matrix_report(args.output_dir, slug, matrix, setup)
    rolling = rolling_pearson(returns, crypto_symbols, stock_symbols, window=30)
    rolling_dir = args.output_dir / "rolling-pearson-5d"
    rolling_dir.mkdir(parents=True, exist_ok=True)
    rolling.to_csv(rolling_dir / "series.csv", index=False)
    latest = rolling.sort_values("timestamp").groupby(["crypto", "stock"]).tail(1)
    latest_matrix = latest.pivot(index="crypto", columns="stock", values="correlation")
    (rolling_dir / "README.md").write_text(
        "\n".join([f"# {METHODS['rolling-pearson-5d']}", "", *setup, "",
        "Window: `30` observations, equivalent to five six-hour intraday sessions.", "",
        "Latest available rolling values:", "", *markdown_table(latest_matrix)]) + "\n",
        encoding="utf-8",
    )
    lagged = lag_correlation(returns, dates, crypto_symbols, stock_symbols, range(-2, 3))
    lag_dir = args.output_dir / "lag-correlation"
    lag_dir.mkdir(parents=True, exist_ok=True)
    lagged.to_csv(lag_dir / "lags.csv", index=False)
    lag_lines = [f"# {METHODS['lag-correlation']}", "", *setup, "",
        "Positive lag means crypto leads the stock. Shifts never cross a U.S. session boundary."]
    for lag in range(-2, 3):
        matrix = lagged[lagged.lag_hours == lag].pivot(
            index="crypto", columns="stock", values="correlation"
        )
        lag_lines += ["", f"## Lag {lag:+d}h", "", *markdown_table(matrix)]
    (lag_dir / "README.md").write_text("\n".join(lag_lines) + "\n", encoding="utf-8")
    print(f"{len(returns)} observations written to {args.output_dir}")


if __name__ == "__main__":
    main()
