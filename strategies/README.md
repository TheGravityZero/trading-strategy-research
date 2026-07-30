# Strategy runners

В этой папке находятся независимые Python launchers торговых стратегий и
результаты запусков различных конфигураций.

```text
strategies/
├── run_crypto_cascade_reversal.py
├── run_crypto_four_week_reversal.py
├── run_crypto_weekly_pivot_limit.py
├── run_stock_weekly_pivot_long.py
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

Текущая crypto-вселенная по умолчанию:
`HYPEUSDT`, `BTCUSDT`, `SOLUSDT`, `ETHUSDT`.

Сводная таблица конфигураций находится в [`reports/README.md`](reports/README.md).
