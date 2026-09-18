# Strategy research

This directory contains experiment launchers and results. Importable strategy
logic lives separately under `src/trading_strategy/strategies`.

Start with [the consolidated results](RESULTS.md): it links all 11 strategies,
summarizes saved pair experiments, and lists correlation studies separately.

```text
research/
├── runners/
│   ├── run_ath_short.py
│   ├── run_ath_retest_volume_short.py
│   ├── run_ath_retest_volume_grid.py
│   ├── run_defended_pivot_hvn_limit.py
│   ├── run_defended_pivot_hvn_reclaim.py
│   ├── run_defended_pivot_long.py
│   ├── run_weekly_pivot_limit.py
│   ├── run_mean_reversion.py
│   ├── run_cointegration.py
│   ├── run_correlation_divergence.py
│   ├── run_regression_spread.py
│   ├── run_cross_asset_correlations.py
│   └── run_combined_stat_arb.py
├── build_results.py                   # rebuild Markdown from saved artifacts
├── RESULTS.md                         # consolidated strategy summary
└── reports/
    └── <strategy>/
        ├── README.md                  # methodology and commands
        ├── RESULTS.md                 # generated strategy summary
        ├── <sector>/                  # sector-based strategies
        │   ├── result.md
        │   └── <configuration>/       # local CSV/JSON artifacts
        └── <run>/                     # pair runs: latest, all-crypto, etc.
            ├── metadata.json          # configuration and metrics; ignored
            └── *.csv                  # selection, bars or trades; ignored
```

Run launchers in `research/runners` from the repository root with
`PYTHONPATH=src`. Use `--help` to view all available parameters.

## Data and experiment scope

Sector-based strategies cover `crypto`, `it`, `semiconductors`, `oil`, and
`metals`. The crypto universe depends on the launcher and experiment; there
is no single shared universe for all reports.

The saved Mean Reversion and Engle–Granger runs use ten cached Binance assets:
`ADAUSDT`, `AVAXUSDT`, `BNBUSDT`, `BTCUSDT`, `DOGEUSDT`, `ETHUSDT`, `LINKUSDT`,
`LTCUSDT`, `SOLUSDT`, and `XRPUSDT`. Both use 4h candles, train from 2025-07-01
to 2026-01-01 and test from 2026-01-01 to 2026-07-01 (end exclusive, UTC).
Neither selected any of the 45 candidate pairs after Holm correction, so
neither traded. This is a selection result, not evidence of profitability.

## Run Mean Reversion and cointegration

Install the research dependencies from the repository root:

```bash
.venv/bin/python -m pip install -e '.[research]'
```

Both launchers below read existing archives in `data/raw`; they do not download
missing data. Source candles must cover the full requested period.

```bash
PYTHONPATH=src .venv/bin/python research/runners/run_mean_reversion.py \
  --symbols ADAUSDT AVAXUSDT BNBUSDT BTCUSDT DOGEUSDT ETHUSDT LINKUSDT LTCUSDT SOLUSDT XRPUSDT \
  --start 2025-07-01 --split 2026-01-01 --end 2026-07-01 --interval 4h \
  --output-dir research/reports/mean-reversion/all-crypto

PYTHONPATH=src .venv/bin/python research/runners/run_cointegration.py \
  --symbols ADAUSDT AVAXUSDT BNBUSDT BTCUSDT DOGEUSDT ETHUSDT LINKUSDT LTCUSDT SOLUSDT XRPUSDT \
  --start 2025-07-01 --split 2026-01-01 --end 2026-07-01 --interval 4h \
  --output-dir research/reports/cointegration/all-crypto
```

Both select pairs on train and execute close-based signals at the next open.
Mean Reversion additionally applies a rolling stationarity gate, loss and
holding limits, and a cooldown. See each strategy's report for assumptions.

## 4h HVN experiment

HVN Limit и HVN Reclaim дополнительно проверены на 4h криптосвечах. В каждом
TP-варианте получено по 2 заполнения и 0 полностью закрытых сделок; результаты
сохранены в соответствующих `crypto/4h-tp*/` каталогах и не смешиваются с 15m
сводками.

## Execution and robustness audit

[Audit results](reports/execution-audit/RESULTS.md) include actual-notional pair
costs, quarterly chronological tests, ten-asset pivot portfolios and open-trade
marks. [Methodology](reports/execution-audit/README.md) describes the accounting
and limitations; legacy pair figures are preserved for comparison.

```bash
PYTHONPATH=src .venv/bin/python research/runners/run_execution_audit.py
```

## Rebuild reports

After running backtests, rebuild the consolidated summary and strategy reports:

```bash
PYTHONPATH=src .venv/bin/python research/build_results.py
```

This command reads saved artifacts; it does **not** rerun backtests. The full
build requires the local CSV/JSON inputs for the sector experiments and
parameter grid, which are excluded from Git. A fresh clone does not contain
these inputs. Markdown summaries are committed so results remain readable.

Missing saved pair experiments are marked as unavailable, not zero returns.
Individual reports specify periods, fees, execution assumptions and metrics;
sector trade averages and pair-account returns should not be ranked together.

## Reports

Result matrices:

- [`reports/mean-reversion/RESULTS.md`](reports/mean-reversion/RESULTS.md)
- [`reports/cointegration/RESULTS.md`](reports/cointegration/RESULTS.md)
- [`reports/weekly-pivot-limit/RESULTS.md`](reports/weekly-pivot-limit/RESULTS.md)
- [`reports/ath-short/RESULTS.md`](reports/ath-short/RESULTS.md)
- [`reports/ath-retest-volume-short/RESULTS.md`](reports/ath-retest-volume-short/RESULTS.md)
- [`reports/defended-pivot-long/RESULTS.md`](reports/defended-pivot-long/RESULTS.md)
- [`reports/defended-pivot-hvn-limit/RESULTS.md`](reports/defended-pivot-hvn-limit/RESULTS.md)
- [`reports/defended-pivot-hvn-reclaim/RESULTS.md`](reports/defended-pivot-hvn-reclaim/RESULTS.md)
- [`reports/crypto-stat-arb/RESULTS.md`](reports/crypto-stat-arb/RESULTS.md)
- [`reports/correlation-divergence/RESULTS.md`](reports/correlation-divergence/RESULTS.md)
- [`reports/regression-spread/RESULTS.md`](reports/regression-spread/RESULTS.md)

Additional research:

- [ATH retest parameter grid](reports/ath-retest-volume-short/GRID_RESULTS.md)
- [Crypto/U.S. equity correlation studies](reports/cross-asset-correlation/README.md) — six statistical studies, not strategy backtests.
