# ATH short — it

Data: Yahoo Finance, regular session, 1h, latest available year. Short-only: after a causal ATH update, a limit entry is placed 7% above the ATH, with a 15% SL, a 4-hour order lifetime, and a maximum 60-day holding period.

| TP | Setups | Fills | Completed | Mean net | Median net | Win rate | TP hits | Stops | Time exit | Open |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10% | 126 | 6 | 6 | 0.03% | 5.25% | 66.67% | 3 | 2 | 1 | 0 |
| 15% | 126 | 6 | 6 | -0.20% | 3.38% | 66.67% | 1 | 2 | 3 | 0 |
| 20% | 126 | 6 | 6 | -2.74% | 0.14% | 50.00% | 0 | 2 | 4 | 0 |

ATH is calculated causally as the maximum of all candles available before the current one. For equities, this is the maximum in the loaded one-year history, not the full historical all-time high.

## All filled trades, including marked open positions

| TP | Filled | Closed | Open | Mean gross, all | Mean net, all | Mean modeled costs |
|---:|---:|---:|---:|---:|---:|---:|
| 10% | 6 | 6 | 0 | 0.11% | 0.03% | 0.08% |
| 15% | 6 | 6 | 0 | -0.12% | -0.20% | 0.08% |
| 20% | 6 | 6 | 0 | -2.66% | -2.74% | 0.08% |

Open trades use their saved last-close mark and modeled round-trip costs (including a hypothetical exit). These are trade averages, not portfolio returns; overlapping signals and capital allocation are not resolved by this table.
