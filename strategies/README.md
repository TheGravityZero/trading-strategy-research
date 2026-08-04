# Strategy runners

This directory contains independent Python strategy launchers and results for
their tested configurations.

```text
strategies/
├── run_ath_short.py
├── run_ath_retest_volume_short.py
├── run_ath_retest_volume_grid.py
├── run_defended_pivot_hvn_limit.py
├── run_defended_pivot_hvn_reclaim.py
├── run_defended_pivot_long.py
├── run_weekly_pivot_limit.py
├── build_results.py
└── reports/
    └── <strategy>/
        └── <sector>/
            ├── result.md              # committed configuration summary
            └── <configuration>/
                ├── metadata.json      # generated locally, ignored
                └── trades/summary.csv # generated locally, ignored
```

Run launchers from the repository root with `PYTHONPATH=src`. Use `--help` to
view all available parameters.

Sectors: `crypto`, `it`, `semiconductors`, `oil`, and `metals`. The current
crypto universe is `HYPEUSDT`, `BTCUSDT`, `SOLUSDT`, and `ETHUSDT`.

After running backtests, rebuild the Markdown reports with:

```bash
PYTHONPATH=src python3 strategies/build_results.py
```

Result matrices:

- [`reports/weekly-pivot-limit/RESULTS.md`](reports/weekly-pivot-limit/RESULTS.md)
- [`reports/ath-short/RESULTS.md`](reports/ath-short/RESULTS.md)
- [`reports/ath-retest-volume-short/RESULTS.md`](reports/ath-retest-volume-short/RESULTS.md)
- [`reports/defended-pivot-long/RESULTS.md`](reports/defended-pivot-long/RESULTS.md)
- [`reports/defended-pivot-hvn-limit/RESULTS.md`](reports/defended-pivot-hvn-limit/RESULTS.md)
- [`reports/defended-pivot-hvn-reclaim/RESULTS.md`](reports/defended-pivot-hvn-reclaim/RESULTS.md)
