# Crypto Combined Stat-Arb

A market-neutral research baseline for a pair of liquid cryptocurrency
perpetual futures. The default pair treats ETHUSDT as the dependent leg (`y`)
and BTCUSDT as the explanatory/hedging leg (`x`).

## Model and features

The strategy works with aligned close prices and log returns. Before each bar,
it estimates the rolling linear relationship

`log(y) = intercept + beta × log(x) + spread`.

The intercept and hedge ratio use only bars completed before the current bar.
The current spread is standardized against the prior rolling spread history.
A separate rolling correlation of pair returns filters weak relationships.

This is the combined baseline:

- correlation as a market-regime filter;
- linear regression as a dynamic hedge-ratio estimator;
- statistical mean reversion through the spread z-score.

For component-level comparisons, see [Correlation Divergence](../correlation-divergence/README.md)
and [Rolling Regression Spread](../regression-spread/README.md).

Rolling regression is not a formal cointegration test. A later research stage
should add ADF/Engle–Granger diagnostics and reject unstable pairs before
evaluating trading performance.

## Trading rules

- Positive entry z-score: short `y`, long `beta × x`.
- Negative entry z-score: long `y`, short `beta × x`.
- Exit when the absolute z-score returns below the exit threshold.
- Close or reject an entry beyond the stop z-score.
- Only enter while absolute rolling correlation exceeds its threshold.
- Normalize returns by `1 + abs(beta)` to keep gross pair exposure comparable.

Signals are calculated at a bar close and become positions on the following
bar. Position changes pay fees and slippage through explicit turnover. Funding,
borrow constraints, order-book impact, and intrabar execution are not modeled.

## Default configuration

| Parameter | Value |
|---|---:|
| Regression window | 240 bars |
| Spread z-score window | 120 bars |
| Correlation window | 120 bars |
| Minimum absolute correlation | 0.50 |
| Entry z-score | 2.00 |
| Exit z-score | 0.25 |
| Stop z-score | 4.00 |
| Fee per side | 5 bps |
| Slippage per side | 2 bps |

## Run

First download matching histories for both symbols, then run from the repository
root:

```bash
PYTHONPATH=src .venv/bin/python research/runners/run_combined_stat_arb.py \
  --y-symbol ETHUSDT \
  --x-symbol BTCUSDT \
  --start 2025-01-01 \
  --end 2026-01-01 \
  --interval 1h

PYTHONPATH=src .venv/bin/python research/build_results.py
```

The launcher writes ignored bar-level artifacts and metadata under `latest/`.
The result builder converts the metadata into the committed summary:
[RESULTS.md](RESULTS.md).

## Optional LSTM experiment

`trading_strategy.models.lstm` provides a chronological binary classifier with
train-only scaling. It is intentionally not part of the benchmark signal. Its
out-of-sample probabilities can later be tested as an entry filter, and should
only be retained if they improve walk-forward results after costs relative to
this regression baseline.

Install it explicitly with `python3 -m pip install -e '.[ml]'`.
