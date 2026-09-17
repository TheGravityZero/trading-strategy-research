# Weekly pivot limit — crypto

Data: Binance Public Data, 15m, 2025-07-01 — 2026-07-01. Shared market logic: long-only, entry 5% below a confirmed weekly pivot, 25% SL, 4-hour limit order, and a maximum 60-day holding period.

| Configuration | Setups | Fills | Completed | Mean net | Median net | Win rate | TP | Stop | Time exit | Open |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TP 10% | 20 | 4 | 4 | 4.63% | 9.86% | 75.00% | 3 | 0 | 1 | 0 |
| TP 15% | 20 | 4 | 4 | -2.19% | -6.28% | 25.00% | 1 | 0 | 3 | 0 |
| TP 20% | 20 | 4 | 4 | -0.94% | -6.28% | 25.00% | 1 | 0 | 3 | 0 |

Unavailable assets: `HYPEUSDT` (No kline archives for HYPEUSDT).

Note: the trade sample is small; this is an exploratory backtest, not statistical confirmation of an edge.

## All filled trades, including marked open positions

| TP | Filled | Closed | Open | Mean gross, all | Mean net, all | Mean modeled costs |
|---:|---:|---:|---:|---:|---:|---:|
| 10% | 4 | 4 | 0 | 4.77% | 4.63% | 0.14% |
| 15% | 4 | 4 | 0 | -2.05% | -2.19% | 0.14% |
| 20% | 4 | 4 | 0 | -0.80% | -0.94% | 0.14% |

Open trades use their saved last-close mark and modeled round-trip costs (including a hypothetical exit). These are trade averages, not portfolio returns; overlapping signals and capital allocation are not resolved by this table.
