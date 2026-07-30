# Strategy runners

В этой папке находятся независимые Python launchers торговых стратегий и
результаты запусков различных конфигураций.

```text
strategies/
├── run_weekly_pivot_limit.py
├── build_results.py
└── reports/
    └── <strategy>/
        └── <sector>/
            ├── result.md              # сводка конфигураций, committed
            └── <configuration>/
                ├── metadata.json      # генерируется локально, ignored
                └── trades/summary.csv # генерируется локально, ignored
```

Запуск производится из корня репозитория с `PYTHONPATH=src`. Все параметры
можно посмотреть через `--help`.

Сектора: `crypto`, `it`, `semiconductors`, `oil`, `metals`. Текущая
вселенная сектора `crypto`: `HYPEUSDT`, `BTCUSDT`, `SOLUSDT`, `ETHUSDT`.

После backtest-запусков Markdown-отчёты обновляются командой:

```bash
PYTHONPATH=src python3 strategies/build_results.py
```

Сводная матрица находится в [`reports/README.md`](reports/README.md).
