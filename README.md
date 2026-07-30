# Trading Strategy Research

Исследовательский репозиторий для воспроизводимых event-driven бэктестов на
криптовалютах и американских акциях. Основная тема — отскок после экстремального
пробоя многонедельного уровня или proxy ликвидационного каскада.

Это исследовательский код, а не инвестиционная рекомендация и не готовая
production-система исполнения.

## Реализованные стратегии

| Стратегия | Рынок | Текущий результат | Launcher | Отчёт |
|---|---|---|---|---|
| Cascade reversal | Crypto futures | Gross-эффект стабилен, net отрицательный | `scripts/run_crypto_cascade_reversal.py` | `reports/strategies/crypto-cascade-reversal/` |
| Four-week reversal | Crypto futures | Отклонена: сильное продолжение пробоя | `scripts/run_crypto_four_week_reversal.py` | `reports/strategies/crypto-four-week-reversal/` |
| Confirmed weekly pivot | Crypto futures | +3.68% mean net, только 2 сделки | `scripts/run_crypto_weekly_pivot_limit.py` | `reports/strategies/crypto-weekly-pivot-limit/` |
| Weekly-pivot long | US stocks | +7.98% mean net, только 6 закрытых сделок | `scripts/run_stock_weekly_pivot_long.py` | `reports/strategies/stock-weekly-pivot-long/` |

OI/absorption, aggTrades microstructure и последовательная проверка гипотез
находятся в `src/cascades/`, но не представлены как самостоятельные торговые
стратегии: это фильтры и исследовательские анализы.

## Структура

```text
.
├── scripts/                         # отдельный launcher каждой стратегии
├── src/cascades/
│   ├── strategies/                  # торговая логика и симуляция сделок
│   ├── utils/
│   │   ├── crypto.py                # Binance archives и causal OI merge
│   │   └── stocks.py                # hourly stocks, NY time, weekly pivots
│   ├── data.py                      # низкоуровневые Binance readers/downloaders
│   ├── events.py                    # proxy cascade detector
│   ├── features.py                  # причинные признаки
│   ├── backtest.py                  # event-level continuation/reversal
│   └── cli.py                       # общий CLI для исследований
├── reports/
│   ├── strategies/                  # описание и результаты каждой стратегии
│   └── ...                          # подробные CSV/JSON артефакты прогонов
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

### 1. Crypto cascade reversal

Требует локальных Binance Vision klines и futures metrics в `data/raw`.

```bash
PYTHONPATH=src python scripts/run_crypto_cascade_reversal.py
```

### 2. Crypto four-week reversal

Использует события годового cascade study:

```bash
PYTHONPATH=src python scripts/run_crypto_four_week_reversal.py
```

### 3. Crypto confirmed weekly pivot

Default launcher воспроизводит вариант: entry 5%, заявка 4 часа, TP на pivot,
постоянный SL −25%, удержание до 90 дней.

```bash
PYTHONPATH=src python scripts/run_crypto_weekly_pivot_limit.py
```

### 4. US stocks weekly-pivot long

Default launcher воспроизводит выбранный вариант: только long, entry 5% ниже
pivot, TP +15%, SL −25%, удержание 60 дней. При отсутствии локального CSV
часовые данные загружаются и кешируются.

```bash
PYTHONPATH=src python scripts/run_stock_weekly_pivot_long.py
```

Все launcher-файлы поддерживают `--help` и параметры директорий/стратегии.

## Загрузка криптоданных

Пример загрузки дневных архивов минутных свечей и futures metrics:

```bash
PYTHONPATH=src python -m cascades.cli download \
  --symbols BTCUSDT ETHUSDT SOLUSDT \
  --start 2025-05-01 --end 2025-05-31

PYTHONPATH=src python -m cascades.cli download \
  --dataset metrics \
  --symbols BTCUSDT ETHUSDT SOLUSDT \
  --start 2025-05-01 --end 2025-05-31
```

Источник: [Binance Public Data](https://github.com/binance/binance-public-data).

## Методология

- Недельные уровни формируются только после завершения необходимых свечей.
- Futures metrics получают консервативную задержку публикации в одну минуту.
- Хронологические research, validation и test не перемешиваются.
- Синхронные криптособытия объединяются в market clusters.
- В часовых акциях take-profit запрещён в свече исполнения, поскольку OHLC не
  восстанавливает порядок intrabar extremes; stop в ней остаётся возможным.
- Открытые позиции не включаются в realised performance.
- Комиссии и slippage задаются явно в конфигурации стратегии.

## Отчёты

Краткие карточки стратегий находятся в
[`reports/strategies`](reports/strategies). Подробные `RESEARCH_NOTE.md`
фиксируют конфигурацию, выборку, результаты, решение и ограничения. Большие
CSV/JSON/GZip артефакты генерируются локально и исключены из Git.

## Тесты

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Основные ограничения

- Yahoo chart endpoint не является гарантированным production data feed.
- Часовые OHLC не позволяют точно восстановить очередь и intrabar path.
- Для шортов акций не моделируются borrow availability и borrow fee.
- Для perpetual futures не во всех стратегиях учтён funding.
- Event-level сделки не являются capital-constrained portfolio simulation.
- Лучший вариант акций выбран на короткой годовой выборке и требует
  out-of-sample проверки на более длинной истории.
