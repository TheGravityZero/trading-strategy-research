# Strategy configurations

Каждый подкаталог содержит описание конкретной стратегии, а следующий уровень
— отчёт отдельной конфигурации. CSV/JSON-артефакты создаются launcher-файлами
рядом с README и не коммитятся.

Текущая crypto-вселенная для новых запусков: `HYPEUSDT`, `BTCUSDT`,
`SOLUSDT`, `ETHUSDT`. Сохранённые ниже старые результаты с другими активами
помечены как historical и не считаются результатом новой вселенной.

## Crypto cascade reversal

| Configuration | Command | Result |
|---|---|---|
| `baseline-7d` | `python -m cascades.cli research --strategy-mode auto` | Исходный baseline, net отрицательный |
| `oi-reversal-7d` | `python -m cascades.cli research --strategy-mode reversal --oi-drop-threshold -0.002` | Gross reversal, издержки не покрыты |
| `fixed-15m-oi-filter` | `python strategies/run_crypto_cascade_reversal.py` | 4,626 событий, mean net около −11.4 bps |

## Crypto four-week reversal

| Configuration | Command | Result |
|---|---|---|
| `reclaim` | `python strategies/run_crypto_four_week_reversal.py --entry-mode reclaim --output-dir strategies/reports/crypto-four-week-reversal/reclaim` | Слишком мало сделок |
| `offset-4pct` | `python strategies/run_crypto_four_week_reversal.py` | Сильное продолжение пробоя, конфигурация отклонена |

## Crypto confirmed weekly pivot

| Configuration | Command | Result |
|---|---|---|
| `default-7pct-breakeven` | `python -m cascades.cli weekly-pivot-limit --events data/processed/crypto-cascade-events.csv --output-dir strategies/reports/crypto-weekly-pivot-limit/default-7pct-breakeven` | Исходный вариант с breakeven |
| `entry5-breakeven-hold7d` | `python -m cascades.cli weekly-pivot-limit --events data/processed/crypto-cascade-events.csv --entry-offset-percent 5 --maximum-holding-days 7 --output-dir strategies/reports/crypto-weekly-pivot-limit/entry5-breakeven-hold7d` | 2 сделки, mean net −1.43% |
| `entry5-stop25-hold7d` | `python strategies/run_crypto_weekly_pivot_limit.py --maximum-holding-days 7 --output-dir strategies/reports/crypto-weekly-pivot-limit/entry5-stop25-hold7d` | 2 сделки, mean net −2.13% |
| `entry5-stop25-hold90d` | `python strategies/run_crypto_weekly_pivot_limit.py` | 2 сделки, mean net +3.68% |

## US stocks weekly pivot

Новые запуски разделены по секторам:

| Sector | Command | Symbols |
|---|---|---:|
| IT | `python strategies/run_stock_weekly_pivot_long.py --sector it` | 10 |
| Semiconductors | `python strategies/run_stock_weekly_pivot_long.py --sector semiconductors` | 13 |
| Oil | `python strategies/run_stock_weekly_pivot_long.py --sector oil` | 10 |
| Metals | `python strategies/run_stock_weekly_pivot_long.py --sector metals` | 10 |

Старый объединённый IT + semiconductor эксперимент находится в
`stock-weekly-pivot/historical-it-semiconductors/`.

Во всех командах предполагается префикс `PYTHONPATH=src`.
