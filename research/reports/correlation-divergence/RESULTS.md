# Crypto Correlation Divergence Results

[Strategy description](README.md)

Pair `ETHUSDT/BTCUSDT`, interval `1h`, period `2025-07-01T00:00:00+00:00` — `2026-06-30T23:00:00+00:00`.

| Trades | Total return | Maximum drawdown | Bar Sharpe | Turnover |
|---:|---:|---:|---:|---:|
| 111 | -19.40% | -25.03% | -0.018 | 221.00 |

Configuration: `zscore_window=120`, `correlation_window=120`, `minimum_correlation=0.5`, `entry_zscore=2.0`, `exit_zscore=0.25`, `stop_zscore=4.0`, `fee_bps_per_side=5.0`, `slippage_bps_per_side=2.0`.
