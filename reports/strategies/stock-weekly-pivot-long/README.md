# US stocks weekly-pivot long

## Идея

Стратегия работает только в long. После пробоя подтверждённого недельного
pivot low ставится лимит на 5% ниже уровня сроком на четыре часа. Take-profit —
15% от входа, stop-loss — 25%, максимальное удержание — 60 календарных дней.

## Запуск

```bash
PYTHONPATH=src python scripts/run_stock_weekly_pivot_long.py
```

## Бэктест

- Период: 2025-07-30 — 2026-07-30.
- Вселенная: 23 IT/semiconductor акции.
- Данные: regular-session hourly OHLCV.

| Metric | Result |
|---|---:|
| Потенциальные setup | 88 |
| Исполненные заявки | 7 |
| Завершённые сделки | 6 |
| Открытые сделки | 1 |
| Mean net, completed | +7.98% |
| Median net, completed | +7.18% |
| Win rate | 100% |
| Mean holding | 42.0 дня |
| Take-profit / time-exit / stop | 2 / 4 / 0 |

Вывод: результат положительный, но основан только на шести завершённых сделках
и выбран после просмотра той же годовой выборки. Два сигнала AMZN являются
одновременными траншами.

Исходные артефакты:
[`../../us-equities-1y-long-tp15-hold60d/`](../../us-equities-1y-long-tp15-hold60d/).
