# Crypto confirmed weekly-pivot limit

## Идея

Недельный pivot подтверждается двумя свечами слева и двумя справа, поэтому
уровень доступен причинно. При последующем пробое ставится лимит на 5% дальше
pivot сроком на четыре часа. Take-profit находится на pivot, stop-loss — 25%
от входа, максимальное удержание — 90 дней. Breakeven отключён.

## Запуск

```bash
PYTHONPATH=src python strategies/run_crypto_weekly_pivot_limit.py
```

## Бэктест

| Symbol | Exit | Holding | Net |
|---|---|---:|---:|
| AVAXUSDT | Take-profit | 96 минут | +5.12% |
| BTCUSDT | Time-exit | 90 дней | +2.24% |

Средний net-return: **+3.68%**, но исполнено только две сделки.

Вывод: сценарий интересен, но статистических оснований для edge нет. BTC-сделка
пересекает границу номинального test-периода; funding и стоимость занятого
капитала не учтены.

Конфигурации:

- [`default-7pct-breakeven/`](default-7pct-breakeven/) — исходный вариант.
- [`entry5-breakeven-hold7d/`](entry5-breakeven-hold7d/) — вход 5% и
  breakeven через пять минут.
- [`entry5-stop25-hold7d/`](entry5-stop25-hold7d/) — постоянный stop и
  удержание семь дней.
- [`entry5-stop25-hold90d/`](entry5-stop25-hold90d/) — постоянный stop и
  удержание до 90 дней.
