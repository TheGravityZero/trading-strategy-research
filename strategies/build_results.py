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
        else "Yahoo Finance, regular session, 1h, последний доступный год"
    )
    lines = [
        f"# Weekly pivot limit — {sector}",
        "",
        f"Данные: {market}. Общая логика для всех рынков: long-only, entry 5% "
        "ниже подтверждённого weekly pivot, SL 25%, лимитный ордер 4 часа, "
        "удержание до 60 дней.",
        "",
        "| Конфигурация | Setups | Fills | Completed | Mean net | "
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
            "Недоступные активы: "
            + ", ".join(f"`{symbol}` ({error})" for symbol, error in failures.items())
            + ".",
        ]
    lines += [
        "",
        "Важно: выборка сделок мала; это exploratory backtest, а не "
        "статистическое подтверждение edge.",
    ]
    (root / "result.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def short_sector_result(sector: str) -> None:
    root = REPORTS / "ath-short" / sector
    market = (
        "Binance Public Data, 15m, 2025-07-01 — 2026-07-01"
        if sector == "crypto"
        else "Yahoo Finance, regular session, 1h, последний доступный год"
    )
    lines = [
        f"# ATH short — {sector}",
        "",
        f"Данные: {market}. Short-only: после обновления causal ATH лимитный "
        "вход ставится на 7% выше ATH, SL 15%, ордер живёт 4 часа, "
        "удержание до 60 дней.",
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
            "Недоступные активы: "
            + ", ".join(f"`{symbol}` ({error})" for symbol, error in failures.items())
            + ".",
        ]
    lines += [
        "",
        "ATH определяется причинно как максимум всех доступных свечей до "
        "текущей. Для акций это максимум в загруженной годовой истории, а не "
        "полный исторический all-time high.",
    ]
    (root / "result.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def defended_pivot_sector_result(sector: str) -> None:
    root = REPORTS / "defended-pivot-long" / sector
    market = (
        "Binance Public Data, 15m, 2025-07-01 — 2026-07-01"
        if sector == "crypto"
        else "Yahoo Finance, regular session, 1h, последний доступный год"
    )
    lines = [
        f"# Defended pivot long — {sector}",
        "",
        f"Данные: {market}. Pivot volume ≥1.5× медианы 12 недель; первая "
        "защита: касание ±0.5 ATR и отскок ≥1.5 ATR за 5 дней; следующий "
        "пробой активирует limit 5% ниже pivot, SL 25%, ордер 4 часа.",
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
            "Недоступные активы: "
            + ", ".join(f"`{symbol}` ({error})" for symbol, error in failures.items())
            + ".",
        ]
    lines += [
        "",
        "Вывод: фильтры находят защищённые уровни, но повторный пробой с "
        "лимитным входом ещё на 5% ниже pivot не дал fills. TP пока не влияет "
        "на результат; следующим экспериментом следует менять вход.",
    ]
    (root / "result.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def ath_retest_sector_result(sector: str) -> None:
    root = REPORTS / "ath-retest-volume-short" / sector
    market = (
        "Binance Public Data, 15m, 2025-07-01 — 2026-07-01"
        if sector == "crypto"
        else "Yahoo Finance, regular session, 1h, последний доступный год"
    )
    lines = [
        f"# ATH retest volume short — {sector}",
        "",
        f"Данные: {market}. Коррекция после ATH ≥15%, failed retest в пределах "
        "3% ниже ATH, entry на retest верхнего high-volume node, SL 15%, "
        "удержание до 60 дней.",
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
            "Недоступные активы: "
            + ", ".join(f"`{symbol}` ({error})" for symbol, error in failures.items())
            + ".",
        ]
    lines += [
        "",
        "ATH и volume profile рассчитываются только по данным, доступным к "
        "моменту failed retest. Для акций ATH ограничен годовой историей.",
    ]
    (root / "result.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def defended_hvn_sector_result(sector: str, slug: str, title: str) -> None:
    root = REPORTS / slug / sector
    market = (
        "Binance Public Data, 15m, 2025-07-01 — 2026-07-01"
        if sector == "crypto"
        else "Yahoo Finance, regular session, 1h, последний доступный год"
    )
    lines = [
        f"# {title} — {sector}",
        "",
        f"Данные: {market}. Volume pivot ≥1.5× baseline, первая защита "
        "≥1.5 ATR; HVN строится в зоне pivot ±1 ATR по первой защите. "
        "SL 25%, удержание до 60 дней.",
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
            "Недоступные активы: "
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
        "Crypto использует 15m, акции — 1h; торговая логика и конфигурация "
        "одинаковы.",
        "",
        "[Описание стратегии](README.md)",
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
        "Entry 7% выше causal ATH, SL 15%, TP 10%/15%/20%. Crypto использует "
        "15m, акции — 1h.",
        "",
        "[Описание стратегии](README.md)",
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
        "Volume ratio ≥1.5, defense bounce ≥1.5 ATR за 5 дней, entry 5% "
        "ниже pivot, SL 25%, TP 10%/15%/20%.",
        "",
        "[Описание стратегии](README.md)",
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
        "Коррекция ≥15%, возврат в пределах 3% ниже ATH, entry на retest "
        "верхнего high-volume node, SL 15%, TP 10%/15%/20%.",
        "",
        "[Описание стратегии](README.md)",
        "",
        "[Сетка correction/retest/structural stop](GRID_RESULTS.md)",
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
        "[Описание стратегии](README.md)",
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
        "Сетка: correction 7/10/12%, retest distance 3/5/7%, stop на ATH "
        "или верхней границе HVN, TP 10/15/20%. Crypto — 15m, акции — 1h.",
        "",
        "Вывод: устойчивого положительного результата нет. Формально лучший "
        "вариант при ≥20 сделках (7% / 7% / HVN / TP20) дал только +0.01% "
        "mean при медиане −0.23% и 274 stop из 278 сделок. Узкий HVN-stop "
        "почти всегда срабатывает; варианты со stop на ATH также отрицательны "
        "на общей выборке.",
        "",
        "## Лучшие варианты при минимум 20 завершённых сделках",
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
        "## Лучший mean по сектору (без поправки на малую выборку)",
        "",
        "| Sector | Correction | Retest | Stop | TP | Trades | Mean net |",
        "|---|---:|---:|---|---:|---:|---:|",
        *sector_rows,
        "",
        "## Полная сетка",
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
        "Вход лимитным ордером в центре HVN",
    )
    defended_hvn_index(
        "defended-pivot-hvn-reclaim",
        "Defended Pivot HVN Reclaim",
        "Вход после sweep ниже HVN и закрытия обратно выше нижней границы",
    )


if __name__ == "__main__":
    main()
