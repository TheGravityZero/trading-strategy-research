# Weekly pivot limit — semiconductors

Data: Yahoo Finance, regular session, 1h, latest available year. Shared market logic: long-only, entry 5% below a confirmed weekly pivot, 25% SL, 4-hour limit order, and a maximum 60-day holding period.

| Configuration | Setups | Fills | Completed | Mean net | Median net | Win rate | TP | Stop | Time exit | Open |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TP 10% | 36 | 2 | 2 | 9.92% | 9.92% | 100.00% | 2 | 0 | 0 | 0 |
| TP 15% | 36 | 2 | 2 | 12.27% | 12.27% | 100.00% | 1 | 0 | 1 | 0 |
| TP 20% | 36 | 2 | 2 | 14.77% | 14.77% | 100.00% | 1 | 0 | 1 | 0 |

Note: the trade sample is small; this is an exploratory backtest, not statistical confirmation of an edge.

## All filled trades, including marked open positions

| TP | Filled | Closed | Open | Mean gross, all | Mean net, all | Mean modeled costs |
|---:|---:|---:|---:|---:|---:|---:|
| 10% | 2 | 2 | 0 | 10.00% | 9.92% | 0.08% |
| 15% | 2 | 2 | 0 | 12.35% | 12.27% | 0.08% |
| 20% | 2 | 2 | 0 | 14.85% | 14.77% | 0.08% |

Open trades use their saved last-close mark and modeled round-trip costs (including a hypothetical exit). These are trade averages, not portfolio returns; overlapping signals and capital allocation are not resolved by this table.
