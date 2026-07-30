# Strategy configurations

Каждый подкаталог содержит описание конкретной стратегии, а следующий уровень
— отчёт отдельной конфигурации. CSV/JSON-артефакты создаются launcher-файлами
рядом с README и не коммитятся.

Текущая crypto-вселенная для новых запусков: `HYPEUSDT`, `BTCUSDT`,
`SOLUSDT`, `ETHUSDT`. Сохранённые ниже старые результаты с другими активами
помечены как historical и не считаются результатом новой вселенной.

## Cascade reversal / crypto

| Configuration | Command | Result |
|---|---|---|
| `baseline-7d` | `python -m cascades.cli research --strategy-mode auto` | Исходный baseline, net отрицательный |
| `oi-reversal-7d` | `python -m cascades.cli research --strategy-mode reversal --oi-drop-threshold -0.002` | Gross reversal, издержки не покрыты |
| `fixed-15m-oi-filter` | `python strategies/run_cascade_reversal.py` | 4,626 событий, mean net около −11.4 bps |

## Four-week reversal / crypto

| Configuration | Command | Result |
|---|---|---|
| `reclaim` | `python strategies/run_four_week_reversal.py --entry-mode reclaim --output-dir strategies/reports/four-week-reversal/crypto/reclaim` | Слишком мало сделок |
| `offset-4pct` | `python strategies/run_four_week_reversal.py` | Сильное продолжение пробоя, конфигурация отклонена |

## Weekly-pivot limit / crypto

| Configuration | Command | Result |
|---|---|---|
| `default-7pct-breakeven` | `python -m cascades.cli weekly-pivot-limit --events data/processed/crypto-cascade-events.csv --output-dir strategies/reports/weekly-pivot-limit/crypto/default-7pct-breakeven` | Исходный вариант с breakeven |
| `entry5-breakeven-hold7d` | `python -m cascades.cli weekly-pivot-limit --events data/processed/crypto-cascade-events.csv --entry-offset-percent 5 --maximum-holding-days 7 --output-dir strategies/reports/weekly-pivot-limit/crypto/entry5-breakeven-hold7d` | 2 сделки, mean net −1.43% |
| `entry5-stop25-hold7d` | `python strategies/run_weekly_pivot_limit.py --sector crypto --maximum-holding-days 7 --output-dir strategies/reports/weekly-pivot-limit/crypto/entry5-stop25-hold7d` | 2 сделки, mean net −2.13% |
| `entry5-stop25-hold90d` | `python strategies/run_weekly_pivot_limit.py --sector crypto` | 2 сделки, mean net +3.68% |

## Weekly-pivot limit / equity sectors

Новые запуски разделены по секторам:

| Sector | Command | Symbols |
|---|---|---:|
| IT | `python strategies/run_weekly_pivot_limit.py --sector it` | 10 |
| Semiconductors | `python strategies/run_weekly_pivot_limit.py --sector semiconductors` | 13 |
| Oil | `python strategies/run_weekly_pivot_limit.py --sector oil` | 10 |
| Metals | `python strategies/run_weekly_pivot_limit.py --sector metals` | 10 |

Старый объединённый IT + semiconductor эксперимент находится в
`weekly-pivot-limit/historical-it-semiconductors/`.

Во всех командах предполагается префикс `PYTHONPATH=src`.
