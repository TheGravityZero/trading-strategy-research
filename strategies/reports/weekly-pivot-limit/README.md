# Weekly-pivot limit

## Идея

Стратегия ищет возврат после пробоя подтверждённого недельного pivot. Рынок
задаётся сектором, а не названием стратегии.

## Запуск

```bash
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector crypto
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector it
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector semiconductors
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector oil
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector metals
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

Секторы:

- [`crypto/`](crypto/)
- [`it/`](it/)
- [`semiconductors/`](semiconductors/)
- [`oil/`](oil/)
- [`metals/`](metals/)

Старые смешанные результаты IT + semiconductors сохранены отдельно в
[`historical-it-semiconductors/`](historical-it-semiconductors/) и не являются
результатами новых секторных прогонов.
