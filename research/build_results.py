#!/usr/bin/env python3
"""Build Markdown summaries for all strategy experiments."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


REPORTS = Path("research/reports")
SECTORS = ("crypto", "it", "semiconductors", "oil", "metals")


def percent(value: float) -> str:
    return "—" if pd.isna(value) else f"{value * 100:.2f}%"


def decimal(value: float) -> str:
    return "—" if pd.isna(value) else f"{value:.3f}"


def read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def sector_result(sector: str) -> None:
    root = REPORTS / "weekly-pivot-limit" / sector
    market = (
        "Binance Public Data, 15m, 2025-07-01 — 2026-07-01"
        if sector == "crypto"
        else "Yahoo Finance, regular session, 1h, latest available year"
    )
    lines = [
        f"# Weekly pivot limit — {sector}",
        "",
        f"Data: {market}. Shared market logic: long-only, entry 5% below a "
        "confirmed weekly pivot, 25% SL, 4-hour limit order, and a maximum "
        "60-day holding period.",
        "",
        "| Configuration | Setups | Fills | Completed | Mean net | "
        "Median net | Win rate | TP | Stop | Time exit | Open |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    failures: dict[str, str] = {}
    for tp in (10, 15, 20):
        directory = root / f"tp{tp}-hold60d"
        metadata = json.loads((directory / "metadata.json").read_text())
        failures.update(metadata.get("failures", {}))
        trades = read_csv(directory / "trades.csv")
        filled = (
            trades[trades["order_filled"] == True].copy()  # noqa: E712
            if len(trades)
            else pd.DataFrame()
        )
        completed = (
            filled[filled["exit_reason"] != "open"]
            if "exit_reason" in filled
            else pd.DataFrame(columns=["net_return"])
        )
        reasons = (
            filled["exit_reason"].value_counts()
            if "exit_reason" in filled
            else pd.Series(dtype=int)
        )
        lines.append(
            f"| TP {tp}% | {metadata['setups']} | {metadata['fills']} | "
            f"{metadata['completed']} | "
            f"{percent(completed['net_return'].mean())} | "
            f"{percent(completed['net_return'].median())} | "
            f"{percent((completed['net_return'] > 0).mean())} | "
            f"{int(reasons.get('take_profit', 0))} | "
            f"{int(reasons.get('stop', 0))} | "
            f"{int(reasons.get('time_exit', 0))} | "
            f"{int(reasons.get('open', 0))} |"
        )
    if failures:
        lines += [
            "",
            "Unavailable assets: "
            + ", ".join(f"`{symbol}` ({error})" for symbol, error in failures.items())
            + ".",
        ]
    lines += [
        "",
        "Note: the trade sample is small; this is an exploratory backtest, "
        "not statistical confirmation of an edge.",
    ]
    append_marked_trade_summary(root, lines)
    (root / "result.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def short_sector_result(sector: str) -> None:
    root = REPORTS / "ath-short" / sector
    market = (
        "Binance Public Data, 15m, 2025-07-01 — 2026-07-01"
        if sector == "crypto"
        else "Yahoo Finance, regular session, 1h, latest available year"
    )
    lines = [
        f"# ATH short — {sector}",
        "",
        f"Data: {market}. Short-only: after a causal ATH update, a limit entry "
        "is placed 7% above the ATH, with a 15% SL, a 4-hour order lifetime, "
        "and a maximum 60-day holding period.",
        "",
        "| TP | Setups | Fills | Completed | Mean net | Median net | "
        "Win rate | TP hits | Stops | Time exit | Open |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    failures: dict[str, str] = {}
    for tp in (10, 15, 20):
        directory = root / f"tp{tp}-hold60d"
        metadata = json.loads((directory / "metadata.json").read_text())
        failures.update(metadata.get("failures", {}))
        trades = read_csv(directory / "trades.csv")
        filled = (
            trades[trades["order_filled"] == True].copy()  # noqa: E712
            if len(trades)
            else pd.DataFrame()
        )
        completed = (
            filled[filled["exit_reason"] != "open"]
            if "exit_reason" in filled
            else pd.DataFrame(columns=["net_return"])
        )
        reasons = (
            filled["exit_reason"].value_counts()
            if "exit_reason" in filled
            else pd.Series(dtype=int)
        )
        lines.append(
            f"| {tp}% | {metadata['setups']} | {metadata['fills']} | "
            f"{metadata['completed']} | "
            f"{percent(completed['net_return'].mean())} | "
            f"{percent(completed['net_return'].median())} | "
            f"{percent((completed['net_return'] > 0).mean())} | "
            f"{int(reasons.get('take_profit', 0))} | "
            f"{int(reasons.get('stop', 0))} | "
            f"{int(reasons.get('time_exit', 0))} | "
            f"{int(reasons.get('open', 0))} |"
        )
    if failures:
        lines += [
            "",
            "Unavailable assets: "
            + ", ".join(f"`{symbol}` ({error})" for symbol, error in failures.items())
            + ".",
        ]
    lines += [
        "",
        "ATH is calculated causally as the maximum of all candles available "
        "before the current one. For equities, this is the maximum in the "
        "loaded one-year history, not the full historical all-time high.",
    ]
    append_marked_trade_summary(root, lines)
    (root / "result.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def defended_pivot_sector_result(sector: str) -> None:
    root = REPORTS / "defended-pivot-long" / sector
    market = (
        "Binance Public Data, 15m, 2025-07-01 — 2026-07-01"
        if sector == "crypto"
        else "Yahoo Finance, regular session, 1h, latest available year"
    )
    lines = [
        f"# Defended pivot long — {sector}",
        "",
        f"Data: {market}. Pivot volume ≥1.5× the 12-week median; first "
        "defense: a ±0.5 ATR touch and a ≥1.5 ATR bounce within 5 days; the "
        "next break activates a limit 5% below the pivot, 25% SL, 4-hour order.",
        "",
        "| TP | Volume pivots | Defenses | Triggers | Fills | Completed | "
        "Mean net | Win rate |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    failures: dict[str, str] = {}
    for tp in (10, 15, 20):
        directory = root / f"tp{tp}-hold60d"
        metadata = json.loads((directory / "metadata.json").read_text())
        failures.update(metadata.get("failures", {}))
        trades = read_csv(directory / "trades.csv")
        triggers = (
            int(trades["trigger_timestamp"].notna().sum())
            if "trigger_timestamp" in trades
            else 0
        )
        filled = (
            trades[trades["order_filled"] == True].copy()  # noqa: E712
            if len(trades)
            else pd.DataFrame()
        )
        completed = (
            filled[filled["exit_reason"] != "open"]
            if "exit_reason" in filled
            else pd.DataFrame(columns=["net_return"])
        )
        lines.append(
            f"| {tp}% | {metadata['volume_qualified_pivots']} | "
            f"{metadata['confirmed_defenses']} | {triggers} | "
            f"{metadata['fills']} | {metadata['completed']} | "
            f"{percent(completed['net_return'].mean())} | "
            f"{percent((completed['net_return'] > 0).mean())} |"
        )
    if failures:
        lines += [
            "",
            "Unavailable assets: "
            + ", ".join(f"`{symbol}` ({error})" for symbol, error in failures.items())
            + ".",
        ]
    lines += [
        "",
        "Conclusion: the filters find defended levels, but the repeated break "
        "with a limit entry another 5% below the pivot produced no fills. TP "
        "does not affect the result yet; the next experiment should change entry.",
    ]
    append_marked_trade_summary(root, lines)
    (root / "result.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def ath_retest_sector_result(sector: str) -> None:
    root = REPORTS / "ath-retest-volume-short" / sector
    market = (
        "Binance Public Data, 15m, 2025-07-01 — 2026-07-01"
        if sector == "crypto"
        else "Yahoo Finance, regular session, 1h, latest available year"
    )
    lines = [
        f"# ATH retest volume short — {sector}",
        "",
        f"Data: {market}. Correction after ATH ≥15%, failed retest within 3% "
        "below ATH, entry on a retest of the upper high-volume node, 15% SL, "
        "and a maximum 60-day holding period.",
        "",
        "| TP | Setups | Fills | Completed | Mean net | Median net | "
        "Win rate | TP hits | Stops | Time exit |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    failures: dict[str, str] = {}
    for tp in (10, 15, 20):
        directory = root / f"tp{tp}-hold60d"
        metadata = json.loads((directory / "metadata.json").read_text())
        failures.update(metadata.get("failures", {}))
        trades = read_csv(directory / "trades.csv")
        filled = (
            trades[trades["order_filled"] == True].copy()  # noqa: E712
            if len(trades)
            else pd.DataFrame()
        )
        completed = (
            filled[filled["exit_reason"] != "open"]
            if "exit_reason" in filled
            else pd.DataFrame(columns=["net_return"])
        )
        reasons = (
            completed["exit_reason"].value_counts()
            if "exit_reason" in completed
            else pd.Series(dtype=int)
        )
        lines.append(
            f"| {tp}% | {metadata['setups']} | {metadata['fills']} | "
            f"{metadata['completed']} | "
            f"{percent(completed['net_return'].mean())} | "
            f"{percent(completed['net_return'].median())} | "
            f"{percent((completed['net_return'] > 0).mean())} | "
            f"{int(reasons.get('take_profit', 0))} | "
            f"{int(reasons.get('stop', 0))} | "
            f"{int(reasons.get('time_exit', 0))} |"
        )
    if failures:
        lines += [
            "",
            "Unavailable assets: "
            + ", ".join(f"`{symbol}` ({error})" for symbol, error in failures.items())
            + ".",
        ]
    lines += [
        "",
        "ATH and the volume profile use only data available at the time of the "
        "failed retest. Equity ATH is limited to the one-year history.",
    ]
    append_marked_trade_summary(root, lines)
    (root / "result.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def defended_hvn_sector_result(sector: str, slug: str, title: str) -> None:
    root = REPORTS / slug / sector
    market = (
        "Binance Public Data, 15m, 2025-07-01 — 2026-07-01"
        if sector == "crypto"
        else "Yahoo Finance, regular session, 1h, latest available year"
    )
    lines = [
        f"# {title} — {sector}",
        "",
        f"Data: {market}. Volume pivot ≥1.5× baseline, first defense ≥1.5 ATR; "
        "the HVN is built within pivot ±1 ATR using the first defense. "
        "SL is 25% and the maximum holding period is 60 days.",
        "",
        "| TP | Volume pivots | Defenses | Fills | Completed | Mean net | "
        "Median net | Win rate | TP hits | Stops |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    failures: dict[str, str] = {}
    for tp in (10, 15, 20):
        directory = root / f"tp{tp}-hold60d"
        metadata = json.loads((directory / "metadata.json").read_text())
        failures.update(metadata.get("failures", {}))
        trades = read_csv(directory / "trades.csv")
        filled = (
            trades[trades["order_filled"] == True].copy()  # noqa: E712
            if len(trades)
            else pd.DataFrame()
        )
        completed = (
            filled[filled["exit_reason"] != "open"]
            if "exit_reason" in filled
            else pd.DataFrame(columns=["net_return"])
        )
        reasons = (
            completed["exit_reason"].value_counts()
            if "exit_reason" in completed
            else pd.Series(dtype=int)
        )
        lines.append(
            f"| {tp}% | {metadata['volume_qualified_pivots']} | "
            f"{metadata['confirmed_defenses']} | {metadata['fills']} | "
            f"{metadata['completed']} | "
            f"{percent(completed['net_return'].mean())} | "
            f"{percent(completed['net_return'].median())} | "
            f"{percent((completed['net_return'] > 0).mean())} | "
            f"{int(reasons.get('take_profit', 0))} | "
            f"{int(reasons.get('stop', 0))} |"
        )
    if failures:
        lines += [
            "",
            "Unavailable assets: "
            + ", ".join(f"`{symbol}` ({error})" for symbol, error in failures.items())
            + ".",
        ]
    append_marked_trade_summary(root, lines)
    (root / "result.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def weekly_pivot_index() -> None:
    rows = [
        "# Results",
        "",
        "Crypto uses 15m candles and equities use 1h candles; trading logic "
        "and configuration are identical.",
        "",
        "[Strategy description](README.md)",
        "",
        "| crypto | it | semiconductors | oil | metals |",
        "|---|---|---|---|---|",
        "| " + " | ".join(
            f"[result]({sector}/result.md)"
            for sector in SECTORS
        ) + " |",
    ]
    (REPORTS / "weekly-pivot-limit" / "RESULTS.md").write_text(
        "\n".join(rows) + "\n", encoding="utf-8"
    )


def ath_short_index() -> None:
    aggregate_rows = []
    equity_sectors = ("it", "semiconductors", "oil", "metals")
    for tp in (10, 15, 20):
        frames = [
            read_csv(
                REPORTS
                / "ath-short"
                / sector
                / f"tp{tp}-hold60d"
                / "trades.csv"
            )
            for sector in equity_sectors
        ]
        trades = pd.concat(frames, ignore_index=True)
        completed = trades[
            trades["order_filled"].eq(True)  # noqa: E712
            & trades["exit_reason"].ne("open")
        ]
        aggregate_rows.append(
            f"| {tp}% | {len(completed)} | "
            f"{percent(completed['net_return'].mean())} | "
            f"{percent(completed['net_return'].median())} | "
            f"{percent((completed['net_return'] > 0).mean())} | "
            f"{int((completed['exit_reason'] == 'take_profit').sum())} | "
            f"{int((completed['exit_reason'] == 'stop').sum())} |"
        )
    rows = [
        "# ATH Short Results",
        "",
        "Entry 7% above causal ATH, 15% SL, TP 10%/15%/20%. Crypto uses 15m "
        "candles and equities use 1h candles.",
        "",
        "[Strategy description](README.md)",
        "",
        "| crypto | it | semiconductors | oil | metals |",
        "|---|---|---|---|---|",
        "| " + " | ".join(
            f"[result]({sector}/result.md)"
            for sector in SECTORS
        ) + " |",
        "",
        "### Aggregate completed equity trades",
        "",
        "Open positions are excluded here; sector reports below include their last-close marks.",
        "",
        "| TP | Trades | Mean net | Median net | Win rate | TP hits | Stops |",
        "|---:|---:|---:|---:|---:|---:|---:|",
        *aggregate_rows,
    ]
    (REPORTS / "ath-short" / "RESULTS.md").write_text(
        "\n".join(rows) + "\n", encoding="utf-8"
    )


def defended_pivot_index() -> None:
    rows = [
        "# Defended Pivot Long Results",
        "",
        "Volume ratio ≥1.5, defense bounce ≥1.5 ATR within 5 days, entry 5% "
        "below the pivot, 25% SL, TP 10%/15%/20%.",
        "",
        "[Strategy description](README.md)",
        "",
        "| crypto | it | semiconductors | oil | metals |",
        "|---|---|---|---|---|",
        "| " + " | ".join(
            f"[result]({sector}/result.md)"
            for sector in SECTORS
        ) + " |",
    ]
    (REPORTS / "defended-pivot-long" / "RESULTS.md").write_text(
        "\n".join(rows) + "\n", encoding="utf-8"
    )


def ath_retest_index() -> None:
    aggregate_rows = []
    equity_sectors = ("it", "semiconductors", "oil", "metals")
    for tp in (10, 15, 20):
        frames = [
            read_csv(
                REPORTS
                / "ath-retest-volume-short"
                / sector
                / f"tp{tp}-hold60d"
                / "trades.csv"
            )
            for sector in equity_sectors
        ]
        trades = pd.concat(frames, ignore_index=True)
        completed = trades[
            trades["order_filled"].eq(True)  # noqa: E712
            & trades["exit_reason"].ne("open")
        ]
        aggregate_rows.append(
            f"| {tp}% | {len(completed)} | "
            f"{percent(completed['net_return'].mean())} | "
            f"{percent(completed['net_return'].median())} | "
            f"{percent((completed['net_return'] > 0).mean())} | "
            f"{int((completed['exit_reason'] == 'take_profit').sum())} | "
            f"{int((completed['exit_reason'] == 'stop').sum())} |"
        )
    rows = [
        "# ATH Retest Volume Short Results",
        "",
        "Correction ≥15%, return within 3% below ATH, entry on a retest of "
        "the upper high-volume node, 15% SL, TP 10%/15%/20%.",
        "",
        "[Strategy description](README.md)",
        "",
        "[Correction/retest/structural-stop grid](GRID_RESULTS.md)",
        "",
        "| crypto | it | semiconductors | oil | metals |",
        "|---|---|---|---|---|",
        "| " + " | ".join(
            f"[result]({sector}/result.md)"
            for sector in SECTORS
        ) + " |",
        "",
        "### Aggregate completed equity trades",
        "",
        "Open positions are excluded here; sector reports below include their last-close marks.",
        "",
        "| TP | Trades | Mean net | Median net | Win rate | TP hits | Stops |",
        "|---:|---:|---:|---:|---:|---:|---:|",
        *aggregate_rows,
    ]
    (REPORTS / "ath-retest-volume-short" / "RESULTS.md").write_text(
        "\n".join(rows) + "\n", encoding="utf-8"
    )


def defended_hvn_index(slug: str, title: str, entry: str) -> None:
    rows = [
        f"# {title} Results",
        "",
        f"{entry}. Volume ratio ≥1.5, defense ≥1.5 ATR, SL 25%, "
        "TP 10%/15%/20%.",
        "",
        "[Strategy description](README.md)",
        "",
        "| crypto | it | semiconductors | oil | metals |",
        "|---|---|---|---|---|",
        "| " + " | ".join(
            f"[result]({sector}/result.md)" for sector in SECTORS
        ) + " |",
    ]
    (REPORTS / slug / "RESULTS.md").write_text(
        "\n".join(rows) + "\n", encoding="utf-8"
    )


def crypto_stat_arb_index() -> None:
    """Build the stat-arb index from the launcher's latest metadata."""
    root = REPORTS / "crypto-stat-arb"
    latest = root / "latest" / "metadata.json"
    rows = [
        "# Crypto Combined Stat-Arb Results",
        "",
        "[Strategy description](README.md)",
        "",
    ]
    if not latest.exists():
        rows += [
            "No canonical backtest has been generated yet. Run the launcher "
            "shown in the strategy description, then rebuild this file.",
        ]
    else:
        metadata = json.loads(latest.read_text(encoding="utf-8"))
        summary = metadata["summary"]
        config = metadata["config"]
        rows += [
            f"Pair `{metadata['pair']}`, interval `{metadata['interval']}`, "
            f"period `{metadata.get('start') or '—'}` — `{metadata.get('end') or '—'}`.",
            "",
            "| Trades | Total return | Maximum drawdown | Bar Sharpe | Turnover |",
            "|---:|---:|---:|---:|---:|",
            f"| {summary['trades']} | {percent(summary['total_return'])} | "
            f"{percent(summary['maximum_drawdown'])} | "
            f"{decimal(summary['bar_sharpe'])} | {summary['turnover']:.2f} |",
            "",
            "| Regression window | Z-score window | Correlation window | "
            "Minimum correlation | Entry / exit / stop z-score |",
            "|---:|---:|---:|---:|---:|",
            f"| {config['regression_window']} | {config['zscore_window']} | "
            f"{config['correlation_window']} | {config['minimum_correlation']:.2f} | "
            f"{config['entry_zscore']:.2f} / {config['exit_zscore']:.2f} / "
            f"{config['stop_zscore']:.2f} |",
            "",
            "The Sharpe value is per-bar and is not annualized. Results include "
            "configured fees and slippage but exclude funding and market impact.",
        ]
    root.mkdir(parents=True, exist_ok=True)
    (root / "RESULTS.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def simple_pair_index(slug: str, title: str) -> None:
    root = REPORTS / slug
    latest = root / "latest" / "metadata.json"
    rows = [f"# {title} Results", "", "[Strategy description](README.md)", ""]
    if not latest.exists():
        rows.append("No canonical backtest has been generated yet.")
    else:
        metadata = json.loads(latest.read_text(encoding="utf-8"))
        summary = metadata["summary"]
        rows += [
            f"Pair `{metadata['pair']}`, interval `{metadata['interval']}`, "
            f"period `{metadata['start']}` — `{metadata['end']}`.",
            "",
            "| Trades | Total return | Maximum drawdown | Bar Sharpe | Turnover |",
            "|---:|---:|---:|---:|---:|",
            f"| {summary['trades']} | {percent(summary['total_return'])} | "
            f"{percent(summary['maximum_drawdown'])} | "
            f"{decimal(summary['bar_sharpe'])} | {summary['turnover']:.2f} |",
            "",
            "Configuration: " + ", ".join(
                f"`{key}={value}`" for key, value in metadata["config"].items()
            ) + ".",
        ]
    root.mkdir(parents=True, exist_ok=True)
    (root / "RESULTS.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def ath_retest_grid_result() -> None:
    root = REPORTS / "ath-retest-volume-short" / "grid"
    rows = []
    sector_rows = []
    for correction in (7, 10, 12):
        for retest in (3, 5, 7):
            for stop_mode in ("ath", "hvn"):
                for tp in (10, 15, 20):
                    name = (
                        f"corr{correction:02d}-retest{retest:02d}-"
                        f"stop-{stop_mode}-tp{tp:02d}"
                    )
                    frames = [
                        read_csv(root / sector / name / "trades.csv")
                        for sector in SECTORS
                    ]
                    trades = pd.concat(frames, ignore_index=True)
                    completed = trades[
                        trades["order_filled"].eq(True)  # noqa: E712
                        & trades["exit_reason"].ne("open")
                    ]
                    reasons = completed["exit_reason"].value_counts()
                    rows.append(
                        {
                            "correction": correction,
                            "retest": retest,
                            "stop": stop_mode.upper(),
                            "tp": tp,
                            "trades": len(completed),
                            "mean": completed["net_return"].mean(),
                            "median": completed["net_return"].median(),
                            "win_rate": (completed["net_return"] > 0).mean(),
                            "tp_hits": int(reasons.get("take_profit", 0)),
                            "stops": int(reasons.get("stop", 0)),
                        }
                    )
    table = pd.DataFrame(rows)
    eligible = table[table.trades >= 20].sort_values(
        ["mean", "trades"], ascending=[False, False]
    )
    for sector in SECTORS:
        candidates = []
        for row in rows:
            name = (
                f"corr{row['correction']:02d}-retest{row['retest']:02d}-"
                f"stop-{row['stop'].lower()}-tp{row['tp']:02d}"
            )
            trades = read_csv(root / sector / name / "trades.csv")
            completed = trades[
                trades["order_filled"].eq(True)  # noqa: E712
                & trades["exit_reason"].ne("open")
            ]
            if len(completed):
                candidates.append((completed.net_return.mean(), len(completed), row))
        best_mean, count, best = max(
            candidates,
            key=lambda candidate: (candidate[0], candidate[1]),
            default=(float("nan"), 0, {}),
        )
        sector_rows.append(
            f"| {sector} | "
            + (
                f"{best['correction']}% | {best['retest']}% | {best['stop']} | "
                f"{best['tp']}% | {count} | {percent(best_mean)} |"
                if best
                else "— | — | — | — | 0 | — |"
            )
        )
    lines = [
        "# ATH Retest Volume Short — parameter grid",
        "",
        "Grid: correction 7/10/12%, retest distance 3/5/7%, stop at ATH or "
        "the HVN upper boundary, TP 10/15/20%. Crypto uses 15m candles and "
        "equities use 1h candles.",
        "",
        "Conclusion: no robust positive result was found. The nominally best "
        "variant with ≥20 trades (7% / 7% / HVN / TP20) returned only +0.01% "
        "mean with a −0.23% median and 274 stops out of 278 trades. The tight "
        "HVN stop triggers almost every time; ATH-stop variants are also "
        "negative on the aggregate sample.",
        "",
        "## Best variants with at least 20 completed trades",
        "",
        "| Correction | Retest | Stop | TP | Trades | Mean net | Median net | Win rate | TP hits | Stops |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in eligible.head(10).to_dict("records"):
        lines.append(
            f"| {row['correction']}% | {row['retest']}% | {row['stop']} | "
            f"{row['tp']}% | {row['trades']} | {percent(row['mean'])} | "
            f"{percent(row['median'])} | {percent(row['win_rate'])} | "
            f"{row['tp_hits']} | {row['stops']} |"
        )
    lines += [
        "",
        "## Best mean by sector (not adjusted for small samples)",
        "",
        "| Sector | Correction | Retest | Stop | TP | Trades | Mean net |",
        "|---|---:|---:|---|---:|---:|---:|",
        *sector_rows,
        "",
        "## Full grid",
        "",
        "| Correction | Retest | Stop | TP | Trades | Mean net | Median net | Win rate | TP hits | Stops |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['correction']}% | {row['retest']}% | {row['stop']} | "
            f"{row['tp']}% | {row['trades']} | {percent(row['mean'])} | "
            f"{percent(row['median'])} | {percent(row['win_rate'])} | "
            f"{row['tp_hits']} | {row['stops']} |"
        )
    (REPORTS / "ath-retest-volume-short" / "GRID_RESULTS.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def mean_reversion_index(
    slug: str = "mean-reversion", title: str = "Mean Reversion",
    launcher: str = "run_mean_reversion.py",
) -> None:
    """Summarize saved runs without interpreting an empty selection as profit."""
    root = REPORTS / slug
    rows = [f"# {title} Results", "", "[Strategy description](README.md)", ""]
    paths = sorted(root.glob("*/metadata.json"))
    if not paths:
        rows.append(f"No saved backtests found. Run `{launcher}` first. Results are unavailable, not zero.")
    for path in paths:
        metadata = json.loads(path.read_text(encoding="utf-8"))
        symbols = metadata["symbols"]
        summaries = metadata["summaries"]
        candidates = len(symbols) * (len(symbols) - 1) // 2
        rows += [
            f"## {path.parent.name}", "",
            f"Train: `{metadata['start']}` to `{metadata['split']}`. "
            f"Test: `{metadata['split']}` to `{metadata['end']}` (exclusive). "
            f"Interval: `{metadata['interval']}`.", "",
            "Symbols: " + ", ".join(f"`{symbol}`" for symbol in symbols) + ".", "",
            "| Candidate pairs | Selected pairs | Completed trades |",
            "|---:|---:|---:|",
            f"| {candidates} | {len(summaries)} | "
            f"{sum(summary['trades'] for summary in summaries)} |", "",
        ]
        if not summaries:
            rows += [
                "No pairs passed the train-only cointegration selection with Holm "
                "correction. No trades were taken; this does not establish "
                "profitability of the trading rules.", "",
            ]
        else:
            rows += [
                "| Pair | Trades | Win rate | Total return | Maximum drawdown | Costs |",
                "|---|---:|---:|---:|---:|---:|",
            ]
            for summary in summaries:
                rows.append(
                    f"| {summary.get('pair') or summary['y'] + '/' + summary['x']} | {summary['trades']} | "
                    f"{percent(summary.get('win_rate'))} | {percent(summary['total_return'])} | "
                    f"{percent(summary['maximum_drawdown'])} | {decimal(summary['costs'])} |"
                )
            rows += ["", "Each pair is an independent account, not a combined portfolio.", ""]
        rows += [
            "Configuration: " + ", ".join(
                f"`{key}={value}`" for key, value in metadata["config"].items()
            ) + ".", "",
        ]
    rows += [
        "Signals execute at the next open. Fees and slippage are included; "
        "funding, borrowing, market impact and margin liquidation are not modeled.",
        "Raw CSV/JSON artifacts remain local and are excluded from Git.",
    ]
    root.mkdir(parents=True, exist_ok=True)
    (root / "RESULTS.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def research_index() -> None:
    """Link all strategy summaries without comparing incompatible metrics."""
    strategies = [
        ("weekly-pivot-limit", "Weekly pivot limit", "Five sectors; TP 10/15/20%"),
        ("ath-short", "ATH short", "Five sectors; aggregate equity results"),
        ("ath-retest-volume-short", "ATH retest volume short", "Five sectors; correction/retest/stop grid"),
        ("defended-pivot-long", "Defended pivot long", "Five sectors; defended-level entries"),
        ("defended-pivot-hvn-limit", "Defended pivot HVN limit", "Five sectors; HVN limit entries"),
        ("defended-pivot-hvn-reclaim", "Defended pivot HVN reclaim", "Five sectors; HVN reclaim entries"),
        ("correlation-divergence", "Correlation divergence", "Equal-weight relative log-price spread"),
        ("regression-spread", "Rolling regression spread", "Rolling OLS residual"),
        ("crypto-stat-arb", "Combined stat-arb", "Rolling OLS with correlation filter"),
        ("cointegration", "Engle–Granger cointegration", "Train-only selection; independent pair accounts"),
        ("mean-reversion", "Mean Reversion", "Train-only selection with regime and risk controls"),
    ]
    rows = [
        "# Strategy Results", "",
        "Generated by `research/build_results.py` from locally saved experiment artifacts.", "",
        "| Strategy | Scope | Results |", "|---|---|---|",
    ]
    audit = REPORTS / "execution-audit" / "latest" / "metadata.json"
    if audit.exists():
        rows[2:2] = ["[Updated execution, cost and robustness audit](reports/execution-audit/RESULTS.md) "
                     "uses next-open fills and actual-notional costs. The legacy pair numbers below "
                     "are retained for comparison and should not be treated as audited account returns.", ""]
    for slug, title, scope in strategies:
        rows.append(f"| {title} | {scope} | [Report](reports/{slug}/RESULTS.md) |")
    rows += ["", "## Legacy pair baselines (approximate accounting)", "",
             "| Strategy | Pair / interval | Trades | Total return | Maximum drawdown |",
             "|---|---|---:|---:|---:|"]
    for slug, title, _ in strategies[6:9]:
        path = REPORTS / slug / "latest" / "metadata.json"
        if not path.exists():
            rows.append(f"| {title} | No saved backtest | — | — | — |")
            continue
        metadata = json.loads(path.read_text(encoding="utf-8"))
        summary = metadata["summary"]
        rows.append(f"| {title} | {metadata['pair']} / {metadata['interval']} | "
                    f"{summary['trades']} | {percent(summary['total_return'])} | "
                    f"{percent(summary['maximum_drawdown'])} |")
    rows += ["", "## Train-selected pair strategies", "",
             "| Strategy / run | Candidate pairs | Selected pairs | Trades |",
             "|---|---:|---:|---:|"]
    for slug, title, _ in strategies[9:]:
        paths = sorted((REPORTS / slug).glob("*/metadata.json"))
        if not paths:
            rows.append(f"| {title}: no saved backtest | — | — | — |")
        for path in paths:
            metadata = json.loads(path.read_text(encoding="utf-8"))
            count = len(metadata["symbols"])
            summaries = metadata["summaries"]
            rows.append(f"| {title} / {path.parent.name} | {count * (count - 1) // 2} | "
                        f"{len(summaries)} | {sum(s['trades'] for s in summaries)} |")
    rows += ["", "Periods, costs, execution assumptions and sample sizes are detailed in each report. "
             "Trade averages, pair-account returns and sector aggregates are different metrics; "
             "these results do not form a performance ranking. Missing backtests are not zero returns. "
             "No selected pairs means no trades, not evidence of profitable trading rules.", "",
             "## Additional analysis", "",
             "[Crypto/U.S. equity correlations](reports/cross-asset-correlation/README.md) "
             "contains six correlation studies, not trading-strategy backtests.", "",
             "[ATH retest parameter grid](reports/ath-retest-volume-short/GRID_RESULTS.md)."]
    (REPORTS.parent / "RESULTS.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def append_marked_trade_summary(root: Path, lines: list[str]) -> None:
    """Expose end-of-sample inventory instead of dropping open fills."""
    lines += ["", "## All filled trades, including marked open positions", "",
              "| TP | Filled | Closed | Open | Mean gross, all | Mean net, all | Mean modeled costs |",
              "|---:|---:|---:|---:|---:|---:|---:|"]
    for tp in (10, 15, 20):
        trades = read_csv(root / f"tp{tp}-hold60d" / "trades.csv")
        filled = trades.loc[trades.order_filled.eq(True)] if 'order_filled' in trades else pd.DataFrame()
        if filled.empty:
            lines.append(f"| {tp}% | 0 | 0 | 0 | — | — | — |")
            continue
        opened = int((filled.exit_reason == 'open').sum())
        lines.append(f"| {tp}% | {len(filled)} | {len(filled) - opened} | {opened} | "
                     f"{percent(filled.gross_return.mean())} | {percent(filled.net_return.mean())} | "
                     f"{percent((filled.gross_return - filled.net_return).mean())} |")
    lines += ["", "Open trades use their saved last-close mark and modeled round-trip costs "
              "(including a hypothetical exit). These are trade averages, not portfolio returns; "
              "overlapping signals and capital allocation are not resolved by this table."]


def execution_audit_index() -> None:
    root = REPORTS / "execution-audit"
    path = root / "latest" / "metadata.json"
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = ["# Execution and robustness audit", "", "[Methodology and reproduction](README.md)", "",
            f"Data: `{data['start']}` — `{data['end']}` (exclusive), {len(data['symbols'])} crypto assets.", "",
            "## Pair accounting: ETHUSDT/BTCUSDT, 1h", "",
            "A common 360-hour warmup precedes trading. Gross is P&L on the same executed quantities "
            "with paid fees/slippage added back; the 0x row is a separately simulated cost-free account. "
            "1x = 5 bps fee + 2 bps slippage on each traded leg notional. Terminal exits are included.", "",
            "| Strategy | Cost multiplier | Entries | Gross P&L / initial equity | Fees | Slippage | Net return | Max DD | Rebalance turnover |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in data['pairs']:
        rows.append(f"| {r['strategy']} | {r['cost_multiplier']:g}x | {r['trades']} | {percent(r['gross_return'])} | "
                    f"{percent(r['fees'])} | {percent(r['slippage'])} | {percent(r['net_return'])} | "
                    f"{percent(r['maximum_drawdown'])} | {r['rebalance_turnover']:.2f} |")
    rows += ["", "## Quarterly chronological evaluation", "",
             "Each test quarter follows three months of training/warmup; trade state resets to cash. "
             "Rolling features update causally during test. Parameters stay fixed; no best-window selection. "
             "These dates were already inspected in earlier research, so this is not a fresh holdout.", "",
             "| Strategy | Train start | Test start | Test end (exclusive) | Entries | Gross | Fees + slippage | Net | Max DD |",
             "|---|---|---|---|---:|---:|---:|---:|---:|"]
    for r in data['walk_forward']:
        rows.append(f"| {r['strategy']} | {r['train_start'][:10]} | {r['test_start'][:10]} | {r['test_end'][:10]} | "
                    f"{r['trades']} | {percent(r['gross_return'])} | {percent(r['fees'] + r['slippage'])} | "
                    f"{percent(r['net_return'])} | {percent(r['maximum_drawdown'])} |")
    rows += ["", "## Refit cointegration each quarter, 4h", "",
             "Each fold screens all 45 pairs with Holm correction on its own preceding three months. "
             "Selected pairs receive equal, segregated capital shares; an empty selection stays in cash. "
             "This does not net exposures to the same asset across pairs.", "",
             "| Strategy | Train start | Test start | Selected pairs (Holm p) | Selected / candidates | Entries | Gross attribution | Net | Max DD |",
             "|---|---|---|---|---:|---:|---:|---:|---:|"]
    for r in data['selection_folds']:
        selected = ', '.join(f"{p['y']}/{p['x']} ({p['adjusted_pvalue']:.4f})" for p in r['selected_pairs']) or '—'
        rows.append(f"| {r['strategy']} | {r['train_start'][:10]} | {r['test_start'][:10]} | "
                    f"{selected} | {r['selected']} / {r['candidates']} | {r['trades']} | {percent(r['gross_return'])} | "
                    f"{percent(r['net_return'])} | {percent(r['maximum_drawdown'])} |")
    rows += ["", "## Expanded crypto sample: ten assets, 15min", "",
             "Fixed existing parameters for TP 10/15/20%; this is universe expansion on the same historical year. "
             "All-marked trade means include open positions at their last stored close. "
             "The portfolio uses equal initial cash sleeves per symbol, reinvests within each sleeve, "
             "skips overlapping signals for occupied symbols and charges actual-notional costs. "
             "Positions still open at the boundary are liquidated at their last close.", "",
             "| Strategy | TP | Fills | Closed | Open | Mean net, closed | Mean net, all marked | Portfolio entries | Overlaps skipped | Portfolio net | Portfolio max DD |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in data['expanded']:
        p = r['portfolio']
        rows.append(f"| {r['strategy']} | {r['tp']:g}% | {r['fills']} | {r['closed']} | {r['open']} | "
                    f"{percent(r['closed_mean'])} | {percent(r['all_marked_mean'])} | {p['accepted']} | "
                    f"{p['skipped_overlap']} | {percent(p['net_return'])} | {percent(p['maximum_drawdown'])} |")
    rows += ["", "## Previously omitted open positions in saved sector reports", "",
             "Only configurations with open trades are listed here; every sector report now includes all-marked means.", "",
             "| Strategy | Sector | Configuration | Closed / open | Mean net, closed | Mean net, all marked |",
             "|---|---|---|---:|---:|---:|"]
    for r in data['existing_trades']:
        if r['open']:
            rows.append(f"| {r['strategy']} | {r['sector']} | {r['configuration']} | {r['closed']} / {r['open']} | "
                        f"{percent(r['closed_mean'])} | {percent(r['all_marked_mean'])} |")
    rows += ["", "Funding, borrowing, liquidity, margin calls and market impact beyond the stated slippage "
             "are excluded. Expanded long portfolios inherit the original OHLC fill/stop assumptions; "
             "they do not validate actual order-book execution. Correlated trades and repeated TP variants "
             "are not independent observations. No confidence claim or live-trading recommendation follows."]
    root.mkdir(parents=True, exist_ok=True)
    (root / 'RESULTS.md').write_text('\n'.join(rows) + '\n', encoding='utf-8')


def main() -> None:
    for sector in SECTORS:
        sector_result(sector)
        short_sector_result(sector)
        defended_pivot_sector_result(sector)
        ath_retest_sector_result(sector)
        defended_hvn_sector_result(
            sector, "defended-pivot-hvn-limit", "Defended Pivot HVN Limit"
        )
        defended_hvn_sector_result(
            sector, "defended-pivot-hvn-reclaim", "Defended Pivot HVN Reclaim"
        )
    weekly_pivot_index()
    ath_short_index()
    defended_pivot_index()
    ath_retest_index()
    ath_retest_grid_result()
    defended_hvn_index(
        "defended-pivot-hvn-limit",
        "Defended Pivot HVN Limit",
        "Limit-order entry at the HVN center",
    )
    defended_hvn_index(
        "defended-pivot-hvn-reclaim",
        "Defended Pivot HVN Reclaim",
        "Entry after a sweep below the HVN and a close back above its lower boundary",
    )
    crypto_stat_arb_index()
    mean_reversion_index()
    mean_reversion_index("cointegration", "Engle–Granger Cointegration", "run_cointegration.py")
    simple_pair_index("correlation-divergence", "Crypto Correlation Divergence")
    simple_pair_index("regression-spread", "Crypto Rolling Regression Spread")
    execution_audit_index()
    research_index()


if __name__ == "__main__":
    main()
