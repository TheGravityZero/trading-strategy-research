# Crypto Rolling Regression Spread

A pair mean-reversion baseline based on a causal rolling OLS relationship:

`log(y) = intercept + beta × log(x) + spread`.

The intercept and beta at the current bar use prior completed bars only. The
strategy trades the standardized regression residual, without checking return
correlation. This isolates the contribution of the dynamic hedge ratio.

## Signal

- Positive residual z-score: short `y`, long `beta × x`.
- Negative residual z-score: long `y`, short `beta × x`.
- Exit near zero or at the stop z-score.
- Normalize PnL by `1 + abs(beta)`.
- Apply signals to the following bar and charge fees/slippage on turnover.

Rolling OLS is not proof of cointegration or spread stationarity.

## Run

```bash
PYTHONPATH=src .venv/bin/python research/runners/run_regression_spread.py \
  --y-symbol ETHUSDT --x-symbol BTCUSDT \
  --start 2025-07-01 --end 2026-07-01 --interval 1h
```

[Results](RESULTS.md)
