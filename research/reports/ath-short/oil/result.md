# ATH short — oil

Data: Yahoo Finance, regular session, 1h, latest available year. Short-only: after a causal ATH update, a limit entry is placed 7% above the ATH, with a 15% SL, a 4-hour order lifetime, and a maximum 60-day holding period.

| TP | Setups | Fills | Completed | Mean net | Median net | Win rate | TP hits | Stops | Time exit | Open |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10% | 375 | 3 | 3 | -6.75% | -15.08% | 33.33% | 1 | 2 | 0 | 0 |
| 15% | 370 | 3 | 3 | -15.08% | -15.08% | 0.00% | 0 | 3 | 0 | 0 |
| 20% | 370 | 3 | 3 | -15.08% | -15.08% | 0.00% | 0 | 3 | 0 | 0 |

ATH is calculated causally as the maximum of all candles available before the current one. For equities, this is the maximum in the loaded one-year history, not the full historical all-time high.

## All filled trades, including marked open positions

| TP | Filled | Closed | Open | Mean gross, all | Mean net, all | Mean modeled costs |
|---:|---:|---:|---:|---:|---:|---:|
| 10% | 3 | 3 | 0 | -6.67% | -6.75% | 0.08% |
| 15% | 3 | 3 | 0 | -15.00% | -15.08% | 0.08% |
| 20% | 3 | 3 | 0 | -15.00% | -15.08% | 0.08% |

Open trades use their saved last-close mark and modeled round-trip costs (including a hypothetical exit). These are trade averages, not portfolio returns; overlapping signals and capital allocation are not resolved by this table.
