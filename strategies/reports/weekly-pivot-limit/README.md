# Weekly Pivot Limit

Единая long-only стратегия возврата к подтверждённому недельному минимуму для
криптовалют и американских акций. Торговая логика одинакова для всех секторов;
различаются только источник данных, таймфрейм, торговый календарь и издержки.

## Идея

После пробоя значимого недельного минимума цена может сначала продолжить
движение вниз, а затем отскочить. Стратегия не покупает непосредственно на
уровне: после пробоя она размещает лимитный ордер ещё ниже pivot и тем самым
пытается войти ближе к локальной капитуляции.

## Формирование pivot

Свечи агрегируются по неделям в календаре соответствующего рынка:

- crypto: UTC, основной таймфрейм `15m`;
- акции: `America/New_York`, таймфрейм `1h`.

Недельный минимум считается pivot low, если он минимален в симметричном окне
из пяти недель: две недели слева, текущая неделя и две недели справа. Уровень
становится доступен стратегии только после завершения двух правых недель.
Таким образом, в расчёте нет look-ahead: pivot нельзя использовать до момента
его подтверждения.

## Вход

Для каждого подтверждённого pivot используется только первый последующий
пробой:

1. Закрытие предыдущей свечи находится не ниже pivot.
2. Минимум текущей свечи проходит ниже pivot — это trigger.
3. Выставляется лимитный buy:

   `entry = pivot × (1 − entry_offset_percent / 100)`.

4. Ордер действует `order_lifetime_hours`. Если цена не касается entry за это
   время, setup остаётся незаполненным.

Стандартная конфигурация использует offset `5%` и срок ордера `4 часа`.

## Выход

- Take-profit задаётся как процент от entry. В текущей сетке проверяются
  `+10%`, `+15%` и `+20%`.
- Stop-loss по умолчанию расположен на `−25%` от entry.
- Если TP или SL не достигнут, позиция закрывается по последней доступной цене
  после `maximum_holding_days`; стандартно — `60 дней`.
- Если история заканчивается раньше срока удержания, позиция получает статус
  `open` и не включается в realised performance.

На свече исполнения разрешён консервативный stop, но запрещён take-profit:
OHLC не позволяет восстановить, произошло ли достижение TP до или после
касания лимитного ордера. Если в последующей свече одновременно достигнуты
stop и TP, приоритет получает stop.

## Издержки

Net return рассчитывается после round-trip комиссии и slippage:

`net_return = gross_return − 2 × (fee_bps_per_side + slippage_bps_per_side)`.

Текущие допущения:

| Рынок | Fee на сторону | Slippage на сторону | Round trip |
|---|---:|---:|---:|
| Crypto | 5 bps | 2 bps | 14 bps |
| Акции | 1 bp | 3 bps | 8 bps |

Funding perpetual futures, влияние размера ордера, очередь лимитных заявок и
borrow для short не моделируются. Launcher запускает только long-сценарий.

## Запуск

Из корня репозитория:

```bash
PYTHONPATH=src python3 strategies/run_weekly_pivot_limit.py --sector crypto
PYTHONPATH=src python3 strategies/run_weekly_pivot_limit.py --sector it
PYTHONPATH=src python3 strategies/run_weekly_pivot_limit.py --sector semiconductors
PYTHONPATH=src python3 strategies/run_weekly_pivot_limit.py --sector oil
PYTHONPATH=src python3 strategies/run_weekly_pivot_limit.py --sector metals
```

Пример отдельной конфигурации:

```bash
PYTHONPATH=src python3 strategies/run_weekly_pivot_limit.py \
  --sector crypto \
  --crypto-interval 30min \
  --entry-offset-percent 5 \
  --take-profit-percent 10 \
  --stop-loss-percent 25 \
  --order-lifetime-hours 4 \
  --maximum-holding-days 60
```

## Результаты

Сводные отчёты по конфигурациям находятся в каталогах секторов:

- [crypto](crypto/result.md)
- [IT](it/result.md)
- [semiconductors](semiconductors/result.md)
- [oil](oil/result.md)
- [metals](metals/result.md)

Количество сделок в текущей годовой выборке невелико, поэтому результаты
следует считать exploratory и перепроверять на более длинной out-of-sample
истории.
