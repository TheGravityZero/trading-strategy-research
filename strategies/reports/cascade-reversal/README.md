# Cascade reversal

## Идея

Стратегия ищет экстремальные минутные движения Binance USD-M Futures,
сопровождаемые аномальным объёмом, диапазоном свечи, taker imbalance и
15-минутным снижением open interest не менее 0.2%. После события открывается
контртрендовая позиция с фиксированным горизонтом 15 минут.

## Запуск

```bash
PYTHONPATH=src python strategies/run_cascade_reversal.py
```

## Бэктест

- Период: 2025-07-01 — 2026-06-30.
- Инструменты: BTC, ETH, SOL, XRP, BNB, DOGE, ADA, LINK, AVAX и LTC perpetual.
- Данные: 5,256,000 минутных свечей и 1,051,151 futures-metrics строк.
- События: 4,626, объединённые в 2,404 временных кластера.
- Издержки: 14 bps round trip.

| Split | Mean gross | Mean net | Net-positive |
|---|---:|---:|---:|
| Research | +2.62 bps | -11.38 bps | 43.86% |
| Validation | +2.36 bps | -11.64 bps | 44.19% |
| Test | +2.68 bps | -11.32 bps | 40.50% |

Вывод: обнаружен устойчивый небольшой gross reversal, но он не покрывает
издержки. Стратегия в текущем виде — **No-Go**.

Конфигурации:

- [`crypto/`](crypto/) — криптовалютный сектор.
