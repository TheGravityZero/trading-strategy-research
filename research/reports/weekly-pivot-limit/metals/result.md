# Weekly pivot limit — metals

Data: Yahoo Finance, regular session, 1h, latest available year. Shared market logic: long-only, entry 5% below a confirmed weekly pivot, 25% SL, 4-hour limit order, and a maximum 60-day holding period.

| Configuration | Setups | Fills | Completed | Mean net | Median net | Win rate | TP | Stop | Time exit | Open |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TP 10% | 35 | 4 | 3 | 9.92% | 9.92% | 100.00% | 3 | 0 | 0 | 1 |
| TP 15% | 35 | 4 | 3 | 6.87% | 14.92% | 66.67% | 2 | 0 | 1 | 1 |
| TP 20% | 35 | 4 | 3 | -4.80% | -9.24% | 33.33% | 1 | 1 | 1 | 1 |

Note: the trade sample is small; this is an exploratory backtest, not statistical confirmation of an edge.

## All filled trades, including marked open positions

| TP | Filled | Closed | Open | Mean gross, all | Mean net, all | Mean modeled costs |
|---:|---:|---:|---:|---:|---:|---:|
| 10% | 4 | 3 | 1 | 3.41% | 3.33% | 0.08% |
| 15% | 4 | 3 | 1 | 1.12% | 1.04% | 0.08% |
| 20% | 4 | 3 | 1 | -7.63% | -7.71% | 0.08% |

Open trades use their saved last-close mark and modeled round-trip costs (including a hypothetical exit). These are trade averages, not portfolio returns; overlapping signals and capital allocation are not resolved by this table.
