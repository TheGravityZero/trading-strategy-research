#!/usr/bin/env python3
"""Build committed Markdown summaries from ignored backtest artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


REPORTS = Path("strategies/reports")


def percent(value: float) -> str:
    return "—" if pd.isna(value) else f"{value * 100:.2f}%"


def bps(value: float) -> str:
    return "—" if pd.isna(value) else f"{value * 10_000:.2f}"


def write(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def cascade_result() -> None:
    root = REPORTS / "cascade-reversal" / "crypto"
    labels = {
        "oi-0.1pct": "OI drop ≤ −0.1%",
        "oi-0.2pct": "OI drop ≤ −0.2%",
        "oi-0.5pct": "OI drop ≤ −0.5%",
    }
    lines = [
        "# Cascade reversal — crypto",
        "",
        "Период: 2025-07-01 — 2026-07-01. Таймфрейм: 1 минута. "
        "Активы: BTCUSDT, ETHUSDT, SOLUSDT. HYPEUSDT исключён: "
        "локальный архив за период отсутствует.",
        "",
        "Сделка: reversal на горизонте 15 минут; round-trip cost 14 bps.",
        "",
        "| Конфигурация | Split | События | Кластеры | Gross, bps | "
        "Net, bps | Win rate |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for directory, label in labels.items():
        summary = read_csv(root / directory / "split_summary.csv")
        for _, row in summary.iterrows():
            lines.append(
                f"| {label} | {row['split']} | {int(row['events'])} | "
                f"{int(row['clusters'])} | {bps(row['mean_gross'])} | "
                f"{bps(row['mean_net'])} | {percent(row['hit_rate'])} |"
            )
    lines += [
        "",
        "Вывод: gross-отскок положителен на research/validation, но ни одна "
        "конфигурация не покрывает 14 bps издержек. Усиление OI-фильтра "
        "сокращает выборку и не создаёт устойчивого положительного net edge.",
    ]
    write(root / "result.md", lines)


def four_week_result() -> None:
    root = REPORTS / "four-week-reversal" / "crypto"
    labels = {
        "offset-4pct": "Limit 4% ниже/выше уровня",
        "offset-5pct": "Limit 5% ниже/выше уровня",
        "reclaim-5m": "Reclaim за 5 минут",
    }
    lines = [
        "# Four-week reversal — crypto",
        "",
        "Период: 2025-07-01 — 2026-07-01. Таймфрейм: 1 минута. "
        "Активы: BTCUSDT, ETHUSDT, SOLUSDT. HYPEUSDT исключён из-за "
        "отсутствия локального архива.",
        "",
        "| Конфигурация | Split | Горизонт | Сделки | Кластеры | "
        "Gross, bps | Net, bps | Beats cost |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for directory, label in labels.items():
        metadata = json.loads((root / directory / "metadata.json").read_text())
        summary = read_csv(root / directory / "summary.csv")
        if summary.empty:
            lines.append(
                f"| {label} | — | — | {metadata['eligible']} | — | — | — | — |"
            )
            continue
        for _, row in summary.iterrows():
            lines.append(
                f"| {label} | {row['split']} | "
                f"{int(row['horizon_minutes'])}m | {int(row['events'])} | "
                f"{int(row['clusters'])} | {row['mean_gross_bps']:.2f} | "
                f"{row['mean_net_bps']:.2f} | "
                f"{percent(row['beats_cost_rate'])} |"
            )
    lines += [
        "",
        "Вывод: offset-limit создаёт больше наблюдений, но результаты сильно "
        "меняются между split и горизонтами. Reclaim дал только 3 eligible "
        "события — статистики недостаточно для оценки стратегии.",
    ]
    write(root / "result.md", lines)


def weekly_crypto_result() -> None:
    root = REPORTS / "weekly-pivot-limit" / "crypto"
    labels = {
        "entry5-hold7d": "Entry 5%, hold 7d",
        "entry5-hold90d": "Entry 5%, hold 90d",
        "entry7-hold90d": "Entry 7%, hold 90d",
    }
    lines = [
        "# Weekly pivot limit — crypto",
        "",
        "Период: 2025-07-01 — 2026-07-01. Активы: BTCUSDT, ETHUSDT, "
        "SOLUSDT. HYPEUSDT исключён из-за отсутствия локального архива. "
        "SL 25%, срок лимитного ордера 4 часа, TP на pivot, без breakeven.",
        "",
        "| Конфигурация | Split | Сделки | Кластеры | Mean net | "
        "Median net | Win rate | TP rate | Stop rate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for directory, label in labels.items():
        summary = read_csv(root / directory / "summary.csv")
        if summary.empty:
            lines.append(f"| {label} | — | 0 | 0 | — | — | — | — | — |")
            continue
        for _, row in summary.iterrows():
            lines.append(
                f"| {label} | {row['split']} | {int(row['trades'])} | "
                f"{int(row['clusters'])} | {percent(row['mean_net_return'])} | "
                f"{percent(row['median_net_return'])} | "
                f"{percent(row['win_rate'])} | "
                f"{percent(row['take_profit_rate'])} | "
                f"{percent(row['stop_rate'])} |"
            )
    lines += [
        "",
        "Вывод: при offset 5% получена только одна сделка, при 7% — ни одной. "
        "Текущая связка «cascade event + confirmed weekly pivot + limit» "
        "слишком селективна для надёжного вывода.",
    ]
    write(root / "result.md", lines)


def weekly_equity_result(sector: str) -> None:
    root = REPORTS / "weekly-pivot-limit" / sector
    lines = [
        f"# Weekly pivot limit — {sector}",
        "",
        "Данные: Yahoo Finance, regular session, 1h, последний доступный год. "
        "Long-only; entry 5% ниже подтверждённого weekly pivot; SL 25%; "
        "лимитный ордер 4 часа; удержание до 60 дней.",
        "",
        "| Конфигурация | Setups | Fills | Completed | Mean net | "
        "Median net | Win rate | TP | Stop | Time exit | Open |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for tp in (10, 15, 20):
        directory = root / f"tp{tp}-hold60d"
        metadata = json.loads((directory / "metadata.json").read_text())
        trades = read_csv(directory / "trades.csv")
        filled = trades[trades["order_filled"] == True].copy()  # noqa: E712
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
    lines += [
        "",
        "Важно: число сделок мало; результаты являются exploratory backtest, "
        "а не статистическим подтверждением edge.",
    ]
    write(root / "result.md", lines)


def index_result() -> None:
    lines = [
        "# Backtest results",
        "",
        "Каждый `result.md` объединяет результаты разных конфигураций одной "
        "стратегии для одного сектора. CSV/JSON с полными сделками создаются "
        "локально и исключены из Git.",
        "",
        "| Стратегия | crypto | it | semiconductors | oil | metals |",
        "|---|---|---|---|---|---|",
        "| Cascade reversal | [result](cascade-reversal/crypto/result.md) | "
        "N/A | N/A | N/A | N/A |",
        "| Four-week reversal | [result](four-week-reversal/crypto/result.md) | "
        "N/A | N/A | N/A | N/A |",
        "| Weekly pivot limit | "
        "[result](weekly-pivot-limit/crypto/result.md) | "
        "[result](weekly-pivot-limit/it/result.md) | "
        "[result](weekly-pivot-limit/semiconductors/result.md) | "
        "[result](weekly-pivot-limit/oil/result.md) | "
        "[result](weekly-pivot-limit/metals/result.md) |",
        "",
        "`N/A` означает, что стратегия требует liquidation-cascade событий и "
        "minute futures metrics, которых нет для equity-секторов.",
    ]
    write(REPORTS / "README.md", lines)


def main() -> None:
    cascade_result()
    four_week_result()
    weekly_crypto_result()
    for sector in ("it", "semiconductors", "oil", "metals"):
        weekly_equity_result(sector)
    index_result()


if __name__ == "__main__":
    main()
