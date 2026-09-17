# Crypto Correlation Divergence

The simplest pair baseline. It assumes equal hedge weights (`beta = 1`) and
trades deviations of the relative log price `log(y) − log(x)` only while the
two assets' prior rolling return correlation is sufficiently high.

## Signal

- Standardize the relative log price using the prior rolling mean and standard deviation.
- Enter short `y` / long `x` above the positive entry z-score.
- Enter long `y` / short `x` below the negative entry z-score.
- Exit near zero or at the stop z-score.
- Calculate the signal at close and hold it beginning with the following bar.

There is no regression and no claim that the relative-price spread is
stationary. This strategy isolates whether correlation plus simple divergence
contains useful information.

## Run

```bash
PYTHONPATH=src .venv/bin/python research/runners/run_correlation_divergence.py \
  --y-symbol ETHUSDT --x-symbol BTCUSDT \
  --start 2025-07-01 --end 2026-07-01 --interval 1h
```

[Results](RESULTS.md)
