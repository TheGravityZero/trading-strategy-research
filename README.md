# Trading Strategy Research

Исследовательский репозиторий для воспроизводимых бэктестов единой
weekly-pivot стратегии на криптовалютах и американских акциях.

Это исследовательский код, а не инвестиционная рекомендация и не готовая
production-система исполнения.

## Реализованные стратегии

| Стратегия | Секторы | Текущий результат | Launcher | Отчёт |
|---|---|---|---|---|
| Weekly-pivot limit | crypto, it, semiconductors, oil, metals | Зависит от сектора | `strategies/run_weekly_pivot_limit.py` | `strategies/reports/weekly-pivot-limit/` |
| ATH short | crypto, it, semiconductors, oil, metals | Общий результат отрицательный | `strategies/run_ath_short.py` | `strategies/reports/ath-short/` |
| ATH retest volume short | crypto, it, semiconductors, oil, metals | Failed retest + volume profile | `strategies/run_ath_retest_volume_short.py` | `strategies/reports/ath-retest-volume-short/` |
| Defended pivot long | crypto, it, semiconductors, oil, metals | Защиты найдены, fills отсутствуют | `strategies/run_defended_pivot_long.py` | `strategies/reports/defended-pivot-long/` |
| Defended pivot HVN limit | crypto, it, semiconductors, oil, metals | Вход в центре объёмной зоны | `strategies/run_defended_pivot_hvn_limit.py` | `strategies/reports/defended-pivot-hvn-limit/` |
| Defended pivot HVN reclaim | crypto, it, semiconductors, oil, metals | Вход после возврата в объёмную зону | `strategies/run_defended_pivot_hvn_reclaim.py` | `strategies/reports/defended-pivot-hvn-reclaim/` |

## Структура

```text
.
├── strategies/
│   ├── run_weekly_pivot_limit.py    # weekly pivot long
│   ├── run_ath_short.py             # causal ATH short
│   ├── run_ath_retest_volume_short.py # failed ATH retest + HVN
│   ├── run_defended_pivot_long.py   # volume + prior defense
│   ├── run_defended_pivot_hvn_limit.py # limit в центре HVN
│   ├── run_defended_pivot_hvn_reclaim.py # sweep + reclaim HVN
│   └── reports/                     # strategy/sector/result.md + artifacts
├── src/trading_strategy/
│   ├── strategies/                  # торговая логика и симуляция сделок
│   ├── utils/
│   │   ├── crypto.py                # Binance archives и 15m+ OHLC
│   │   └── stocks.py                # hourly stocks, NY time, weekly pivots
│   ├── data.py                      # низкоуровневые Binance readers/downloaders
│   └── cli.py                       # общий CLI для исследований
└── tests/
```

## Установка

Требуется Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Без editable-install команды можно запускать с `PYTHONPATH=src`, как в
примерах ниже.

## Запуск стратегий

### Weekly-pivot limit

Long-стратегия входит на 5% ниже подтверждённого weekly pivot low. Заявка
живёт 4 часа, позиция удерживается до 60 дней.

```bash
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector crypto
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector it
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector semiconductors
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector oil
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector metals
```

Все launcher-файлы поддерживают `--help` и параметры директорий/стратегии.

### ATH short

После обновления causal ATH выставляется лимитный short на 7% выше уровня.
SL — 15%; проверяются TP 10%, 15% и 20%.

```bash
PYTHONPATH=src python strategies/run_ath_short.py --sector crypto
PYTHONPATH=src python strategies/run_ath_short.py --sector semiconductors
PYTHONPATH=src python strategies/run_ath_short.py --sector metals
```

### Defended pivot long

Торгует только weekly pivot low с объёмом минимум 1.5× медианы предыдущих
12 недель и уже подтверждённым отскоком 1.5 ATR после касания.

```bash
PYTHONPATH=src python strategies/run_defended_pivot_long.py --sector crypto
PYTHONPATH=src python strategies/run_defended_pivot_long.py --sector it
```

### Defended pivot HVN

Обе стратегии строят профиль относительного dollar volume во время первой
защиты pivot. Вариант `limit` покупает в центре HVN; вариант `reclaim` ждёт
sweep ниже зоны и закрытие свечи обратно выше её нижней границы.

```bash
PYTHONPATH=src python strategies/run_defended_pivot_hvn_limit.py --sector crypto
PYTHONPATH=src python strategies/run_defended_pivot_hvn_reclaim.py --sector crypto
```

### ATH retest volume short

После коррекции минимум на 15% стратегия ждёт возврат к ATH без его обновления,
строит volume profile и входит в short на retest верхнего high-volume node.

```bash
PYTHONPATH=src python strategies/run_ath_retest_volume_short.py --sector crypto
PYTHONPATH=src python strategies/run_ath_retest_volume_short.py --sector semiconductors
```

## Загрузка криптоданных

Пример загрузки архивов свечей. Стратегия агрегирует их до 15m и не принимает
таймфреймы ниже 15 минут:

```bash
PYTHONPATH=src python -m trading_strategy.cli download \
  --symbols HYPEUSDT BTCUSDT SOLUSDT ETHUSDT \
  --start 2025-05-01 --end 2025-05-31
```

Источник: [Binance Public Data](https://github.com/binance/binance-public-data).

## Методология

- Недельные уровни формируются только после завершения необходимых свечей.
- Take-profit запрещён в свече исполнения, поскольку OHLC не
  восстанавливает порядок intrabar extremes; stop в ней остаётся возможным.
- Открытые позиции не включаются в realised performance.
- Комиссии и slippage задаются явно в конфигурации стратегии.

## Отчёты

Сводные результаты разных конфигураций находятся в sector-level `result.md`
в [`strategies/reports`](strategies/reports). CSV/JSON-артефакты генерируются
локально и исключены из Git.

## Тесты

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Основные ограничения

- Yahoo chart endpoint не является гарантированным production data feed.
- Часовые OHLC не позволяют точно восстановить очередь и intrabar path.
- Для шортов акций не моделируются borrow availability и borrow fee.
- Для perpetual futures не учтён funding.
- Сделки не объединены в capital-constrained portfolio simulation.
- Лучший вариант акций выбран на короткой годовой выборке и требует
  out-of-sample проверки на более длинной истории.
