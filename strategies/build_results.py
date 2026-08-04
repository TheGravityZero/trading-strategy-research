#!/usr/bin/env python3
"""Build Markdown summaries for all strategy experiments."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


REPORTS = Path("strategies/reports")
SECTORS = ("crypto", "it", "semiconductors", "oil", "metals")


def percent(value: float) -> str:
    return "—" if pd.isna(value) else f"{value * 100:.2f}%"


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
        "### Aggregate equity result",
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
        "### Aggregate equity result",
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


if __name__ == "__main__":
    main()
