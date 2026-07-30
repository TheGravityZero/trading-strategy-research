# Strategy runners

В этой папке находятся независимые Python launchers торговых стратегий и
результаты запусков различных конфигураций.

```text
strategies/
├── run_cascade_reversal.py
├── run_four_week_reversal.py
├── run_weekly_pivot_limit.py
└── reports/
    └── <strategy>/
        ├── README.md
        └── <configuration>/
            ├── README.md
            ├── metadata.json          # генерируется локально, ignored
            └── trades/summary.csv     # генерируется локально, ignored
```

Запуск производится из корня репозитория с `PYTHONPATH=src`. Все параметры
можно посмотреть через `--help`.

Сектора: `crypto`, `it`, `semiconductors`, `oil`, `metals`. Текущая
вселенная сектора `crypto`: `HYPEUSDT`, `BTCUSDT`, `SOLUSDT`, `ETHUSDT`.

Сводная таблица конфигураций находится в [`reports/README.md`](reports/README.md).
