# Defended Pivot Long

Отдельная long-only стратегия, которая торгует только недельные уровни с
повышенным относительным объёмом и подтверждённой предыдущей защитой.

## Относительный объём

Для каждой недели считается dollar volume:

`weekly_dollar_volume = Σ(close × volume)`.

Baseline — медиана предыдущих 12 завершённых недель, не включая pivot-неделю.
Pivot допускается к дальнейшему анализу при:

`pivot_volume / baseline_volume ≥ 1.5`.

Сравнение выполняется отдельно внутри каждого актива.

## Первая защита уровня

После causal-подтверждения pivot low стратегия ждёт:

1. Касание зоны `pivot ± 0.5 daily ATR(14)`.
2. Рост до `pivot + 1.5 ATR` не позднее пяти дней после касания.

ATR использует только завершённые предыдущие дни. Вход при первой защите не
выполняется: она только переводит уровень в состояние `defended`.

## Торговый вход

После подтверждённой защиты ожидается следующий пробой pivot сверху вниз.
Выставляется лимитный buy:

`entry = pivot × 0.95`.

Ордер действует 4 часа. Stop-loss находится на 25% ниже entry, максимальное
удержание — 60 дней. Проверяются TP 10%, 15% и 20%.

## Запуск

```bash
PYTHONPATH=src python3 strategies/run_defended_pivot_long.py \
  --sector crypto \
  --minimum-volume-ratio 1.5 \
  --touch-zone-atr 0.5 \
  --minimum-bounce-atr 1.5 \
  --bounce-window-days 5 \
  --entry-offset-percent 5 \
  --take-profit-percent 10
```

Сектора: `crypto`, `it`, `semiconductors`, `oil`, `metals`.

## Результаты

[Общая таблица результатов](RESULTS.md)

- [crypto](crypto/result.md)
- [IT](it/result.md)
- [semiconductors](semiconductors/result.md)
- [oil](oil/result.md)
- [metals](metals/result.md)

В первой конфигурации защищённые уровни найдены, но fills отсутствуют: после
повторного пробоя цена не достигала лимита ещё на 5% ниже pivot за четыре часа.
