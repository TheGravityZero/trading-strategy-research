# US equities: confirmed weekly pivot limit, 1 year

## Setup

- Universe: 23 requested US equities.
- Data: Yahoo Finance regular-session 1-hour OHLCV, 2025-07-30 through
  2026-07-30, approximately 1,753 bars per symbol.
- Pivot: weekly high/low confirmed by two completed weeks on each side.
- Trade: fade a later breakdown of a pivot low (long) or breakout of a pivot
  high (short).
- Limit entry: 5% beyond the pivot.
- Order lifetime: 4 elapsed hours.
- Take profit: pivot.
- Stop loss: 25% from entry.
- Maximum holding: 90 calendar days.
- Cost assumption: 1 bp fee + 3 bps slippage per side (8 bps round trip).
- Conservative hourly ambiguity rule: a take-profit cannot execute in the
  same hourly candle as the entry; a stop can.

## Aggregate result

| Metric | Result |
|---|---:|
| Potential setups | 189 |
| Filled orders | 21 (11.1%) |
| Symbols with fills | 12 of 23 |
| Mean net return per trade | -3.27% |
| Median net return | +4.68% |
| Win rate | 71.4% |
| Take profits | 14 |
| Stops | 5 |
| Time exits | 2 |

The result has a negatively skewed payoff: many roughly +5% reversals are
overwhelmed by a small number of -25% stops.

## Direction

| Side | Trades | Mean net | Median net | Win rate |
|---|---:|---:|---:|---:|
| Long after pivot-low breakdown | 7 | +4.80% | +5.18% | 100.0% |
| Short after pivot-high breakout | 14 | -7.30% | +4.68% | 57.1% |

All five stops occurred in short trades. The one-year result therefore rejects
the symmetric version of the strategy and suggests testing the long-only
variant. This is a hypothesis generated from the same sample, not an
out-of-sample conclusion.

## Symbols with filled orders

| Symbol | Trades | Mean net |
|---|---:|---:|
| AMZN | 2 | +5.18% |
| CRWV | 2 | +5.18% |
| GOOGL | 1 | +5.18% |
| NOW | 1 | +4.68% |
| ORCL | 1 | +4.68% |
| QCOM | 2 | +4.68% |
| META | 3 | +4.12% |
| NBIS | 4 | -2.76% |
| AVGO | 1 | -14.31% |
| AMD | 1 | -25.08% |
| INTC | 2 | -25.08% |
| LRCX | 1 | -25.08% |

No orders filled for MSFT, AAPL, CRM, ADBE, PLTR, NVDA, MU, AMAT, KLAC, TSM,
or SNDK during the tested window.

## Limitations

- Hourly OHLCV cannot reconstruct the exact intrabar path or exact queue fill.
- Results are event-level, not a capital-constrained portfolio simulation;
  overlapping trades can consume capital simultaneously.
- Short borrow availability and borrow fees are not modeled.
- Earnings announcements, gaps, dividends, and taxes are not modeled.
- One year and 21 fills are insufficient for a reliable estimate.
- The first weeks are necessarily a pivot warm-up period.

The next defensible experiment is a predeclared long-only run on a longer
history, followed by minute-level validation of the selected events.
