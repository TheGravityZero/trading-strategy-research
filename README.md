# Trading Strategy Research

Исследовательский репозиторий для воспроизводимых бэктестов единой
weekly-pivot стратегии на криптовалютах и американских акциях.

Это исследовательский код, а не инвестиционная рекомендация и не готовая
production-система исполнения.

## Реализованные стратегии

| Стратегия | Секторы | Текущий результат | Launcher | Отчёт |
|---|---|---|---|---|
| Weekly-pivot limit | crypto, it, semiconductors, oil, metals | Зависит от сектора | `strategies/run_weekly_pivot_limit.py` | `strategies/reports/weekly-pivot-limit/` |

## Структура

```text
.
├── strategies/
│   ├── run_weekly_pivot_limit.py    # общий launcher всех рынков
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

Для всех рынков используется одна логика: только long, entry 5% ниже
подтверждённого weekly pivot, TP +15%, SL −25%, заявка 4 часа и удержание
до 60 дней. Crypto агрегируется в 15-минутные свечи, акции работают на 1h.

```bash
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector crypto
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector it
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector semiconductors
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector oil
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector metals
```

Все launcher-файлы поддерживают `--help` и параметры директорий/стратегии.

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
