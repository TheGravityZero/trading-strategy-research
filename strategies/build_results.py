#!/usr/bin/env python3
"""Build Markdown summaries for the unified weekly-pivot strategy."""

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


def index_result() -> None:
    rows = [
        "# Backtest results",
        "",
        "В репозитории оставлена одна объединённая стратегия. Crypto использует "
        "15m, акции — 1h; торговая логика и конфигурация одинаковы.",
        "",
        "| crypto | it | semiconductors | oil | metals |",
        "|---|---|---|---|---|",
        "| " + " | ".join(
            f"[result](weekly-pivot-limit/{sector}/result.md)"
            for sector in SECTORS
        ) + " |",
    ]
    (REPORTS / "README.md").write_text(
        "\n".join(rows) + "\n", encoding="utf-8"
    )


def main() -> None:
    for sector in SECTORS:
        sector_result(sector)
    index_result()


if __name__ == "__main__":
    main()
