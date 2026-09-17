# ATH short — metals

Data: Yahoo Finance, regular session, 1h, latest available year. Short-only: after a causal ATH update, a limit entry is placed 7% above the ATH, with a 15% SL, a 4-hour order lifetime, and a maximum 60-day holding period.

| TP | Setups | Fills | Completed | Mean net | Median net | Win rate | TP hits | Stops | Time exit | Open |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10% | 410 | 9 | 9 | 0.64% | 9.92% | 66.67% | 5 | 3 | 1 | 0 |
| 15% | 410 | 9 | 9 | 3.42% | 14.92% | 66.67% | 5 | 3 | 1 | 0 |
| 20% | 406 | 9 | 9 | 6.19% | 19.92% | 66.67% | 5 | 3 | 1 | 0 |

ATH is calculated causally as the maximum of all candles available before the current one. For equities, this is the maximum in the loaded one-year history, not the full historical all-time high.

## All filled trades, including marked open positions

| TP | Filled | Closed | Open | Mean gross, all | Mean net, all | Mean modeled costs |
|---:|---:|---:|---:|---:|---:|---:|
| 10% | 9 | 9 | 0 | 0.72% | 0.64% | 0.08% |
| 15% | 9 | 9 | 0 | 3.50% | 3.42% | 0.08% |
| 20% | 9 | 9 | 0 | 6.27% | 6.19% | 0.08% |

Open trades use their saved last-close mark and modeled round-trip costs (including a hypothetical exit). These are trade averages, not portfolio returns; overlapping signals and capital allocation are not resolved by this table.
