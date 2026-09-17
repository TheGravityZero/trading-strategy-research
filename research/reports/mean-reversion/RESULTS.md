# Mean Reversion Results

[Strategy description](README.md)

## all-crypto

Train: `2025-07-01 00:00:00+00:00` to `2026-01-01 00:00:00+00:00`. Test: `2026-01-01 00:00:00+00:00` to `2026-07-01 00:00:00+00:00` (exclusive). Interval: `4h`.

Symbols: `ADAUSDT`, `AVAXUSDT`, `BNBUSDT`, `BTCUSDT`, `DOGEUSDT`, `ETHUSDT`, `LINKUSDT`, `LTCUSDT`, `SOLUSDT`, `XRPUSDT`.

| Candidate pairs | Selected pairs | Completed trades |
|---:|---:|---:|
| 45 | 0 | 0 |

No pairs passed the train-only cointegration selection with Holm correction. No trades were taken; this does not establish profitability of the trading rules.

Configuration: `window=120`, `entry=2.0`, `stop=3.5`, `fee_bps=10.0`, `slippage_bps=2.0`, `alpha=0.05`, `min_train_bars=240`, `regime_window=240`, `regime_every=24`, `regime_alpha=0.05`, `max_holding_bars=120`, `stop_loss=0.05`, `cooldown_bars=24`.

## latest

Train: `2025-07-01 00:00:00+00:00` to `2026-01-01 00:00:00+00:00`. Test: `2026-01-01 00:00:00+00:00` to `2026-07-01 00:00:00+00:00` (exclusive). Interval: `4h`.

Symbols: `BTCUSDT`, `ETHUSDT`, `SOLUSDT`.

| Candidate pairs | Selected pairs | Completed trades |
|---:|---:|---:|
| 3 | 0 | 0 |

No pairs passed the train-only cointegration selection with Holm correction. No trades were taken; this does not establish profitability of the trading rules.

Configuration: `window=120`, `entry=2.0`, `stop=3.5`, `fee_bps=10.0`, `slippage_bps=2.0`, `alpha=0.05`, `min_train_bars=240`, `regime_window=240`, `regime_every=24`, `regime_alpha=0.05`, `max_holding_bars=120`, `stop_loss=0.05`, `cooldown_bars=24`.

Signals execute at the next open. Fees and slippage are included; funding, borrowing, market impact and margin liquidation are not modeled.
Raw CSV/JSON artifacts remain local and are excluded from Git.
