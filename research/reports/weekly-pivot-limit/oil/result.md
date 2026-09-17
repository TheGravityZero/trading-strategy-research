# Weekly pivot limit — oil

Data: Yahoo Finance, regular session, 1h, latest available year. Shared market logic: long-only, entry 5% below a confirmed weekly pivot, 25% SL, 4-hour limit order, and a maximum 60-day holding period.

| Configuration | Setups | Fills | Completed | Mean net | Median net | Win rate | TP | Stop | Time exit | Open |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TP 10% | 30 | 0 | 0 | — | — | — | 0 | 0 | 0 | 0 |
| TP 15% | 30 | 0 | 0 | — | — | — | 0 | 0 | 0 | 0 |
| TP 20% | 30 | 0 | 0 | — | — | — | 0 | 0 | 0 | 0 |

Note: the trade sample is small; this is an exploratory backtest, not statistical confirmation of an edge.

## All filled trades, including marked open positions

| TP | Filled | Closed | Open | Mean gross, all | Mean net, all | Mean modeled costs |
|---:|---:|---:|---:|---:|---:|---:|
| 10% | 0 | 0 | 0 | — | — | — |
| 15% | 0 | 0 | 0 | — | — | — |
| 20% | 0 | 0 | 0 | — | — | — |

Open trades use their saved last-close mark and modeled round-trip costs (including a hypothetical exit). These are trade averages, not portfolio returns; overlapping signals and capital allocation are not resolved by this table.
