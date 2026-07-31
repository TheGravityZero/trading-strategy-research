# Strategy runners

В этой папке находятся независимые Python launchers торговых стратегий и
результаты запусков различных конфигураций.

```text
strategies/
├── run_ath_short.py
├── run_ath_retest_volume_short.py
├── run_defended_pivot_hvn_limit.py
├── run_defended_pivot_hvn_reclaim.py
├── run_defended_pivot_long.py
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

Сводные матрицы:

- [`reports/weekly-pivot-limit/RESULTS.md`](reports/weekly-pivot-limit/RESULTS.md)
- [`reports/ath-short/RESULTS.md`](reports/ath-short/RESULTS.md)
- [`reports/ath-retest-volume-short/RESULTS.md`](reports/ath-retest-volume-short/RESULTS.md)
- [`reports/defended-pivot-long/RESULTS.md`](reports/defended-pivot-long/RESULTS.md)
- [`reports/defended-pivot-hvn-limit/RESULTS.md`](reports/defended-pivot-hvn-limit/RESULTS.md)
- [`reports/defended-pivot-hvn-reclaim/RESULTS.md`](reports/defended-pivot-hvn-reclaim/RESULTS.md)
