# US equities: long-only, TP 15%, maximum holding 60 days

## Configuration

- Universe: 23 requested US equities.
- Data: regular-session 1-hour OHLCV, 2025-07-30 through 2026-07-30.
- Signal: later breakdown of a causally confirmed weekly pivot low.
- Direction: long only.
- Limit entry: 5% below the pivot.
- Order lifetime: 4 elapsed hours.
- Take profit: 15% above entry.
- Stop loss: 25% below entry.
- Maximum holding: 60 calendar days.
- Assumed round-trip costs: 8 bps.
- Fill-bar take-profit is prohibited; fill-bar stop remains possible.

## Result

| Metric | Result |
|---|---:|
| Potential setups | 88 |
| Filled orders | 7 |
| Completed trades | 6 |
| Open trades | 1 |
| Mean net return, completed | +7.98% |
| Median net return, completed | +7.18% |
| Win rate, completed | 100% |
| Mean holding period | 42.0 calendar days |
| Median holding period | 58.6 calendar days |
| Take profits | 2 |
| Time exits | 4 |
| Stops | 0 |

The currently open GOOGL trade is excluded from realized performance.

## Completed trades

| Symbol | Exit | Holding | Net return |
|---|---|---:|---:|
| META | Time exit | 57.3 days | +1.00% |
| META | Take profit | 14.0 days | +14.92% |
| AMZN | Time exit | 60.0 days | +4.75% |
| AMZN | Time exit | 60.0 days | +2.69% |
| CRWV | Time exit | 60.0 days | +9.61% |
| CRWV | Take profit | 0.9 days | +14.92% |

The two AMZN records are distinct weekly pivots filled during the same hourly
candle. They are valid event-level signals but would represent simultaneous
tranches in a portfolio simulation.

## Interpretation

Only two of six completed trades reached the 15% target. Four positions were
closed by the 60-day limit while still profitable. This suggests that the
60-day time exit is materially binding. The positive result is encouraging but
is based on only six completed trades, includes correlated/overlapping signals,
and was selected after inspecting the same one-year sample.
