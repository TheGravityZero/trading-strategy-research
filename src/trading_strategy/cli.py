from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

from .data import download_monthly_archive
from .utils.crypto import DEFAULT_CRYPTO_SYMBOLS


INTERVALS = ("15m", "30m", "1h", "4h", "1d")


def parse_day(value: str) -> date:
    return date.fromisoformat(value)


def month_range(start: date, end: date):
    current = start.replace(day=1)
    final = end.replace(day=1)
    while current <= final:
        yield current
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)


def download_command(args: argparse.Namespace) -> None:
    jobs = [
        (symbol.upper(), month)
        for symbol in args.symbols
        for month in month_range(args.start, args.end)
    ]
    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                download_monthly_archive,
                symbol,
                args.interval,
                month,
                "klines",
                args.raw_dir,
            ): (symbol, month)
            for symbol, month in jobs
        }
        for number, future in enumerate(as_completed(futures), start=1):
            job = futures[future]
            try:
                print(f"[{number}/{len(jobs)}] {future.result()}", flush=True)
            except Exception as exc:
                failures.append((job, exc))
                print(f"[{number}/{len(jobs)}] FAILED {job}: {exc}", flush=True)
    if failures:
        raise SystemExit(f"{len(failures)} of {len(jobs)} downloads failed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trading_strategy")
    subparsers = parser.add_subparsers(dest="command", required=True)
    download = subparsers.add_parser(
        "download", help="Download Binance OHLC archives at 15m or higher"
    )
    download.add_argument(
        "--symbols", nargs="+", default=DEFAULT_CRYPTO_SYMBOLS
    )
    download.add_argument("--interval", choices=INTERVALS, default="15m")
    download.add_argument("--workers", type=int, default=4)
    download.add_argument("--start", type=parse_day, required=True)
    download.add_argument("--end", type=parse_day, required=True)
    download.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    download.set_defaults(func=download_command)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
