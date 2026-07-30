# Crypto confirmed weekly-pivot limit

## Идея

Недельный pivot подтверждается двумя свечами слева и двумя справа, поэтому
уровень доступен причинно. При последующем пробое ставится лимит на 5% дальше
pivot сроком на четыре часа. Take-profit находится на pivot, stop-loss — 25%
от входа, максимальное удержание — 90 дней. Breakeven отключён.

## Запуск

```bash
PYTHONPATH=src python scripts/run_crypto_weekly_pivot_limit.py
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

Исходные артефакты:
[`../../weekly-pivot-limit-5pct-stop25-hold90d/`](../../weekly-pivot-limit-5pct-stop25-hold90d/).
