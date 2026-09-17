# Weekly pivot limit — it

Data: Yahoo Finance, regular session, 1h, latest available year. Shared market logic: long-only, entry 5% below a confirmed weekly pivot, 25% SL, 4-hour limit order, and a maximum 60-day holding period.

| Configuration | Setups | Fills | Completed | Mean net | Median net | Win rate | TP | Stop | Time exit | Open |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TP 10% | 52 | 5 | 4 | 4.59% | 3.72% | 100.00% | 1 | 0 | 3 | 1 |
| TP 15% | 52 | 5 | 4 | 5.84% | 3.72% | 100.00% | 1 | 0 | 3 | 1 |
| TP 20% | 52 | 5 | 4 | 7.09% | 3.72% | 100.00% | 1 | 0 | 3 | 1 |

Note: the trade sample is small; this is an exploratory backtest, not statistical confirmation of an edge.

## All filled trades, including marked open positions

| TP | Filled | Closed | Open | Mean gross, all | Mean net, all | Mean modeled costs |
|---:|---:|---:|---:|---:|---:|---:|
| 10% | 5 | 4 | 1 | 4.80% | 4.72% | 0.08% |
| 15% | 5 | 4 | 1 | 5.80% | 5.72% | 0.08% |
| 20% | 5 | 4 | 1 | 6.80% | 6.72% | 0.08% |

Open trades use their saved last-close mark and modeled round-trip costs (including a hypothetical exit). These are trade averages, not portfolio returns; overlapping signals and capital allocation are not resolved by this table.
