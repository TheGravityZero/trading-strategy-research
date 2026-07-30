# Strategy configurations

Каждый подкаталог содержит описание конкретной стратегии, а следующий уровень
— отчёт отдельной конфигурации. CSV/JSON-артефакты создаются launcher-файлами
рядом с README и не коммитятся.

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

| Configuration | Command | Result |
|---|---|---|
| `symmetric-pivot-hold90d` | `python -m cascades.cli us-equities --maximum-holding-days 90 --output-dir strategies/reports/stock-weekly-pivot/symmetric-pivot-hold90d` | 21 сделка, mean net −3.27% |
| `take-profit-grid` | Последовательные запуски `us-equities --take-profit-percent 7.5…30` | Лучший общий target в сетке — 20% |
| `long-tp15-hold60d` | `python strategies/run_stock_weekly_pivot_long.py` | 6 закрытых сделок, mean net +7.98% |

Во всех командах предполагается префикс `PYTHONPATH=src`.
