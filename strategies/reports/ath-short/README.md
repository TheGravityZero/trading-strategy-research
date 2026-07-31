# ATH Short

Отдельная short-only стратегия для криптовалют и американских акций.

## Идея и сигнал

Перед каждой свечой рассчитывается causal ATH — максимальный high всей истории,
доступной строго до этой свечи. Когда текущая свеча обновляет максимум,
стратегия размещает лимитный short ещё на `7%` выше прежнего ATH:

`entry = prior_ath × 1.07`.

Ордер действует `4 часа`. Одновременно на символ разрешён только один активный
ордер или short. Для акций ATH ограничен доступной годовой историей Yahoo; это
не полный биржевой all-time high.

## Выход

- Stop-loss: `15%` выше цены входа.
- Take-profit: проверяются варианты `10%`, `15%` и `20%` ниже входа.
- Максимальное удержание: `60 дней`.
- На свече исполнения TP запрещён из-за неизвестного intrabar path, stop
  разрешён консервативно.
- Если TP и stop достигнуты в одной последующей свече, приоритет имеет stop.

Crypto работает на `15m`, акции — на `1h`. Из результата вычитаются round-trip
fee и slippage: `14 bps` для crypto и `8 bps` для акций. Funding, borrow fee,
очередь лимитных заявок и market impact не моделируются.

## Запуск

```bash
PYTHONPATH=src python3 strategies/run_ath_short.py \
  --sector semiconductors \
  --entry-offset-percent 7 \
  --take-profit-percent 10 \
  --stop-loss-percent 15 \
  --order-lifetime-hours 4 \
  --maximum-holding-days 60
```

Сектора: `crypto`, `it`, `semiconductors`, `oil`, `metals`.

## Результаты

[Общая таблица результатов](RESULTS.md)

- [crypto](crypto/result.md)
- [IT](it/result.md)
- [semiconductors](semiconductors/result.md)
- [oil](oil/result.md)
- [metals](metals/result.md)
