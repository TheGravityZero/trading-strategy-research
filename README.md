# Trading Strategy Research

A research repository for reproducible backtests of trading strategies across
cryptocurrency and U.S. equity markets.

This is research code, not investment advice or a production-ready execution
system.

## Implemented strategies

| Strategy | Sectors | Current result | Launcher | Report |
|---|---|---|---|---|
| Weekly-pivot limit | crypto, it, semiconductors, oil, metals | Sector-dependent | `strategies/run_weekly_pivot_limit.py` | `strategies/reports/weekly-pivot-limit/` |
| ATH short | crypto, it, semiconductors, oil, metals | Negative aggregate result | `strategies/run_ath_short.py` | `strategies/reports/ath-short/` |
| ATH retest volume short | crypto, it, semiconductors, oil, metals | Failed retest with volume profile | `strategies/run_ath_retest_volume_short.py` | `strategies/reports/ath-retest-volume-short/` |
| Defended pivot long | crypto, it, semiconductors, oil, metals | Defenses found, no fills | `strategies/run_defended_pivot_long.py` | `strategies/reports/defended-pivot-long/` |
| Defended pivot HVN limit | crypto, it, semiconductors, oil, metals | Entry at the center of the volume zone | `strategies/run_defended_pivot_hvn_limit.py` | `strategies/reports/defended-pivot-hvn-limit/` |
| Defended pivot HVN reclaim | crypto, it, semiconductors, oil, metals | Entry after reclaiming the volume zone | `strategies/run_defended_pivot_hvn_reclaim.py` | `strategies/reports/defended-pivot-hvn-reclaim/` |

## Repository structure

```text
.
├── strategies/
│   ├── run_weekly_pivot_limit.py       # weekly pivot long
│   ├── run_ath_short.py                # causal ATH short
│   ├── run_ath_retest_volume_short.py  # failed ATH retest + HVN
│   ├── run_defended_pivot_long.py      # volume + prior defense
│   ├── run_defended_pivot_hvn_limit.py # limit at the HVN center
│   ├── run_defended_pivot_hvn_reclaim.py # sweep + HVN reclaim
│   └── reports/                        # strategy/sector/result.md + artifacts
├── src/trading_strategy/
│   ├── strategies/                     # trading logic and simulation
│   ├── utils/
│   │   ├── crypto.py                   # Binance archives and 15m+ OHLC
│   │   └── stocks.py                   # hourly stocks, NY time, weekly pivots
│   ├── data.py                         # low-level Binance readers/downloaders
│   └── cli.py                          # shared research CLI
└── tests/
```

## Installation

Python 3.10+ is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Without an editable install, run commands with `PYTHONPATH=src`, as shown
below.

## Running strategies

### Weekly-pivot limit

The long strategy enters 5% below a confirmed weekly pivot low. The order
remains active for 4 hours and the position can be held for up to 60 days.

```bash
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector crypto
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector it
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector semiconductors
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector oil
PYTHONPATH=src python strategies/run_weekly_pivot_limit.py --sector metals
```

All launchers support `--help` and strategy/data-path parameters.

### ATH short

After a causal ATH update, the strategy places a limit short 7% above the
level. The stop-loss is 15%; take-profit values of 10%, 15%, and 20% are
tested.

```bash
PYTHONPATH=src python strategies/run_ath_short.py --sector crypto
PYTHONPATH=src python strategies/run_ath_short.py --sector semiconductors
PYTHONPATH=src python strategies/run_ath_short.py --sector metals
```

### Defended pivot long

Trades only weekly pivot lows whose volume is at least 1.5× the median of the
previous 12 weeks and that have already produced a confirmed 1.5 ATR bounce.

```bash
PYTHONPATH=src python strategies/run_defended_pivot_long.py --sector crypto
PYTHONPATH=src python strategies/run_defended_pivot_long.py --sector it
```

### Defended pivot HVN

Both variants build a relative dollar-volume profile during the pivot's first
defense. `limit` buys at the HVN center; `reclaim` waits for a sweep below the
zone followed by a close back above its lower boundary.

```bash
PYTHONPATH=src python strategies/run_defended_pivot_hvn_limit.py --sector crypto
PYTHONPATH=src python strategies/run_defended_pivot_hvn_reclaim.py --sector crypto
```

### ATH retest volume short

After a significant correction, the strategy waits for a return toward the
ATH without a new high, builds a volume profile, and enters short on a retest
of the upper high-volume node.

```bash
PYTHONPATH=src python strategies/run_ath_retest_volume_short.py --sector crypto
PYTHONPATH=src python strategies/run_ath_retest_volume_short.py --sector semiconductors
```

## Downloading crypto data

The following command downloads candle archives. Strategies aggregate them to
15m and reject timeframes below 15 minutes:

```bash
PYTHONPATH=src python -m trading_strategy.cli download \
  --symbols HYPEUSDT BTCUSDT SOLUSDT ETHUSDT \
  --start 2025-05-01 --end 2025-05-31
```

Source: [Binance Public Data](https://github.com/binance/binance-public-data).

## Methodology

- Weekly levels become available only after all confirmation candles close.
- Take-profit is disabled on the fill candle because OHLC data cannot recover
  the order of intrabar extremes; a conservative stop remains possible.
- Open positions are excluded from realized performance.
- Fees and slippage are explicit strategy configuration parameters.

## Reports

Configuration summaries are stored in sector-level `result.md` files under
[`strategies/reports`](strategies/reports). CSV/JSON artifacts are generated
locally and excluded from Git.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Main limitations

- The Yahoo chart endpoint is not a guaranteed production data feed.
- Hourly OHLC cannot reconstruct queue position or the intrabar path.
- Equity short borrow availability and borrow fees are not modeled.
- Perpetual futures funding is not included.
- Trades are not combined in a capital-constrained portfolio simulation.
- Equity results use a short one-year sample and require validation on a
  longer out-of-sample period.
