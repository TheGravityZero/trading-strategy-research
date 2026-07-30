from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from .data import (
    download_daily_kline,
    download_daily_metrics,
    download_monthly_archive,
    read_kline_archive,
    read_metrics_archive,
    validate_klines,
)
from .events import DetectorConfig
from .backtest import BacktestConfig
from .pipeline import run_pipeline
from .synthetic import make_synthetic_klines
from .study import run_large_study
from .hypotheses import run_hypothesis_analysis
from .confirmed_absorption import run_confirmed_absorption
from .microstructure import collect_microstructure
from .strategies.four_week_reversal import run_four_week_strategy
from .strategies.confirmed_weekly_pivot import (
    WeeklyPivotLimitConfig,
    run_weekly_pivot_strategy,
)
from .strategies.us_equity_weekly_pivot import (
    EquityPivotConfig,
    run_equity_study,
)
from .utils.stocks import DEFAULT_STOCK_SYMBOLS


def parse_day(value: str) -> date:
    return date.fromisoformat(value)


def date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


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
    raw_dir = Path(args.raw_dir)
    jobs = []
    for symbol in args.symbols:
        periods = (
            month_range(args.start, args.end)
            if args.frequency == "monthly"
            else date_range(args.start, args.end)
        )
        for period in periods:
            jobs.append((symbol, period))

    def fetch(job):
        symbol, period = job
        if args.frequency == "monthly":
            return download_monthly_archive(
                symbol, args.interval, period, args.dataset, raw_dir
            )
        if args.dataset == "metrics":
            return download_daily_metrics(symbol, period, raw_dir)
        return download_daily_kline(symbol, args.interval, period, raw_dir)

    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(fetch, job): job for job in jobs}
        for number, future in enumerate(as_completed(futures), start=1):
            job = futures[future]
            try:
                path = future.result()
                print(f"[{number}/{len(jobs)}] {path}", flush=True)
            except Exception as exc:
                failures.append((job, exc))
                print(f"[{number}/{len(jobs)}] FAILED {job}: {exc}", flush=True)
    if failures:
        raise SystemExit(f"{len(failures)} of {len(jobs)} downloads failed")


def download_event_days_command(args: argparse.Namespace) -> None:
    events = pd.read_csv(args.events, parse_dates=["timestamp"])
    selected = events[
        events["split"].isin(args.splits)
        & (events["oi_change_15m"] <= args.oi_threshold)
    ].copy()
    selected["day"] = selected["timestamp"].dt.date
    jobs = list(
        selected[["symbol", "day"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )
    raw_dir = Path(args.raw_dir)

    def fetch(job):
        symbol, day = job
        return download_daily_kline(symbol, "1s", day, raw_dir)

    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(fetch, job): job for job in jobs}
        for number, future in enumerate(as_completed(futures), start=1):
            job = futures[future]
            try:
                print(
                    f"[{number}/{len(jobs)}] {future.result()}",
                    flush=True,
                )
            except Exception as exc:
                failures.append((job, exc))
                print(f"[{number}/{len(jobs)}] FAILED {job}: {exc}", flush=True)
    if failures:
        raise SystemExit(f"{len(failures)} of {len(jobs)} downloads failed")


def research_command(args: argparse.Namespace) -> None:
    if args.synthetic:
        klines = make_synthetic_klines(rows=args.synthetic_rows)
    else:
        paths = sorted(Path(args.raw_dir).glob("*/*m/*.zip"))
        if not paths:
            raise SystemExit("No archives found. Run `cascades download` first.")
        frames = []
        for path in paths:
            frame = read_kline_archive(path)
            problems = validate_klines(frame)
            serious = [problem for problem in problems if "timestamp gaps" not in problem]
            if serious:
                raise SystemExit(f"Invalid data in {path}: {serious}")
            if problems:
                print(f"warning: {path}: {', '.join(problems)}")
            frames.append(frame)
        klines = pd.concat(frames, ignore_index=True)
        metric_paths = sorted(Path(args.raw_dir).glob("*/metrics/*.zip"))
        if metric_paths:
            metrics = pd.concat(
                [read_metrics_archive(path) for path in metric_paths],
                ignore_index=True,
            )
            # A metric stamped at t is conservatively treated as available at t+1m.
            metrics["timestamp"] += pd.Timedelta(minutes=1)
            klines = pd.merge_asof(
                klines.sort_values("timestamp"),
                metrics.sort_values("timestamp"),
                on="timestamp",
                by="symbol",
                direction="backward",
                tolerance=pd.Timedelta(minutes=5),
            )
    detector = DetectorConfig(oi_drop_threshold=args.oi_drop_threshold)
    backtest = BacktestConfig(strategy_mode=args.strategy_mode)
    metrics = run_pipeline(
        klines, Path(args.output_dir), detector=detector, backtest=backtest
    )
    for key, value in metrics.items():
        print(f"{key}: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cascades")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser("download", help="Download Binance Vision data")
    download.add_argument("--symbols", nargs="+", default=["BTCUSDT"])
    download.add_argument("--interval", default="1m")
    download.add_argument("--dataset", choices=["klines", "metrics"], default="klines")
    download.add_argument(
        "--frequency", choices=["daily", "monthly"], default="daily"
    )
    download.add_argument("--workers", type=int, default=1)
    download.add_argument("--start", type=parse_day, required=True)
    download.add_argument("--end", type=parse_day, required=True)
    download.add_argument("--raw-dir", default="data/raw")
    download.set_defaults(func=download_command)

    event_days = subparsers.add_parser(
        "download-event-days",
        help="Download 1-second klines only for selected event days",
    )
    event_days.add_argument("--events", type=Path, required=True)
    event_days.add_argument("--raw-dir", default="data/raw")
    event_days.add_argument(
        "--splits", nargs="+", default=["research", "validation"]
    )
    event_days.add_argument("--oi-threshold", type=float, required=True)
    event_days.add_argument("--workers", type=int, default=8)
    event_days.set_defaults(func=download_event_days_command)

    research = subparsers.add_parser("research", help="Run event study and backtest")
    research.add_argument("--raw-dir", default="data/raw")
    research.add_argument(
        "--output-dir", default="strategies/reports/research/latest"
    )
    research.add_argument("--synthetic", action="store_true")
    research.add_argument("--synthetic-rows", type=int, default=10_000)
    research.add_argument(
        "--oi-drop-threshold",
        type=float,
        default=None,
        help="Require 15-minute OI change at or below this value, e.g. -0.002",
    )
    research.add_argument(
        "--strategy-mode",
        choices=["auto", "continuation", "reversal"],
        default="auto",
    )
    research.set_defaults(func=research_command)

    study = subparsers.add_parser(
        "study", help="Run memory-bounded 12-month multi-symbol study"
    )
    study.add_argument("--raw-dir", default="data/raw")
    study.add_argument(
        "--output-dir",
        default="strategies/reports/crypto-cascade-reversal/study-12m",
    )
    study.add_argument("--symbols", nargs="+", required=True)
    study.add_argument("--oi-drop-threshold", type=float, default=-0.002)
    study.set_defaults(
        func=lambda args: run_large_study(
            Path(args.raw_dir),
            Path(args.output_dir),
            [symbol.upper() for symbol in args.symbols],
            args.oi_drop_threshold,
        )
    )

    hypotheses = subparsers.add_parser(
        "hypotheses", help="Evaluate sequential OI and absorption hypotheses"
    )
    hypotheses.add_argument("--events", type=Path, required=True)
    hypotheses.add_argument(
        "--output-dir",
        type=Path,
        default=Path("strategies/reports/research/hypotheses"),
    )
    hypotheses.set_defaults(
        func=lambda args: run_hypothesis_analysis(args.events, args.output_dir)
    )

    confirmation = subparsers.add_parser(
        "confirmed-absorption",
        help="Evaluate post-event causal absorption confirmation",
    )
    confirmation.add_argument("--events", type=Path, required=True)
    confirmation.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    confirmation.add_argument("--thresholds", type=Path, required=True)
    confirmation.add_argument(
        "--output-dir",
        type=Path,
        default=Path("strategies/reports/research/confirmed-absorption"),
    )
    confirmation.set_defaults(
        func=lambda args: run_confirmed_absorption(
            args.events, args.raw_dir, args.thresholds, args.output_dir
        )
    )

    micro = subparsers.add_parser(
        "microstructure", help="Collect exact aggTrades event windows"
    )
    micro.add_argument("--events", type=Path, required=True)
    micro.add_argument("--thresholds", type=Path, required=True)
    micro.add_argument("--cache-dir", type=Path, default=Path("data/aggtrades"))
    micro.add_argument("--output", type=Path, required=True)
    micro.add_argument("--per-group", type=int, default=5)
    micro.set_defaults(
        func=lambda args: collect_microstructure(
            args.events,
            args.thresholds,
            args.cache_dir,
            args.output,
            args.per_group,
        )
    )

    four_week = subparsers.add_parser(
        "four-week-reversal",
        help="Run standalone four-week extreme sweep/reclaim strategy",
    )
    four_week.add_argument("--events", type=Path, required=True)
    four_week.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    four_week.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "strategies/reports/crypto-four-week-reversal/latest"
        ),
    )
    four_week.add_argument("--include-test", action="store_true")
    four_week.set_defaults(
        func=lambda args: run_four_week_strategy(
            args.raw_dir,
            args.events,
            args.output_dir,
            include_test=args.include_test,
        )
    )

    pivot = subparsers.add_parser(
        "weekly-pivot-limit", help="Run confirmed weekly pivot limit strategy"
    )
    pivot.add_argument("--events", type=Path, required=True)
    pivot.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    pivot.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "strategies/reports/crypto-weekly-pivot-limit/latest"
        ),
    )
    pivot.add_argument("--include-test", action="store_true")
    pivot.add_argument("--entry-offset-percent", type=float, default=7.0)
    pivot.add_argument("--initial-stop-loss-percent", type=float, default=25.0)
    pivot.add_argument("--maximum-holding-days", type=int, default=7)
    pivot.add_argument(
        "--disable-breakeven",
        action="store_true",
        help="Keep the initial stop for the entire trade",
    )
    pivot.set_defaults(
        func=lambda args: run_weekly_pivot_strategy(
            args.raw_dir,
            args.events,
            args.output_dir,
            args.include_test,
            WeeklyPivotLimitConfig(
                entry_offset_percent=args.entry_offset_percent,
                initial_stop_loss_percent=args.initial_stop_loss_percent,
                breakeven_after_minutes=(
                    None if args.disable_breakeven else 5
                ),
                maximum_holding_minutes=args.maximum_holding_days * 24 * 60,
            ),
        )
    )

    equities = subparsers.add_parser(
        "us-equities",
        help="Download and backtest the weekly-pivot strategy on US stocks",
    )
    equities.add_argument("--symbols", nargs="+", default=DEFAULT_STOCK_SYMBOLS)
    equities.add_argument(
        "--data-dir", type=Path, default=Path("data/us-equities/hourly-1y")
    )
    equities.add_argument(
        "--output-dir",
        type=Path,
        default=Path("strategies/reports/stock-weekly-pivot/latest"),
    )
    equities.add_argument("--entry-offset-percent", type=float, default=5.0)
    equities.add_argument(
        "--take-profit-percent",
        type=float,
        default=None,
        help="Target return from entry; default takes profit at the pivot",
    )
    equities.add_argument("--stop-loss-percent", type=float, default=25.0)
    equities.add_argument("--order-lifetime-hours", type=int, default=4)
    equities.add_argument("--maximum-holding-days", type=int, default=90)
    equities.add_argument(
        "--long-only",
        action="store_true",
        help="Trade only breakdowns of confirmed pivot lows",
    )
    equities.set_defaults(
        func=lambda args: run_equity_study(
            args.data_dir,
            args.output_dir,
            [symbol.upper() for symbol in args.symbols],
            EquityPivotConfig(
                entry_offset_percent=args.entry_offset_percent,
                take_profit_percent=args.take_profit_percent,
                long_only=args.long_only,
                stop_loss_percent=args.stop_loss_percent,
                order_lifetime_hours=args.order_lifetime_hours,
                maximum_holding_days=args.maximum_holding_days,
            ),
        )
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
