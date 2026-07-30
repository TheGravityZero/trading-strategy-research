# Confirmed post-event absorption

## Fixed causal rule

The experiment starts from the previously frozen strong-OI subset:

`15-minute OI change <= -0.5478%`

An entry is allowed only if all conditions occur simultaneously within the
next three completed one-minute candles:

1. no new extreme beyond the event candle;
2. price-impact efficiency is at most 50% of the event-minute value;
3. direction-aligned taker imbalance weakens by at least 0.15;
4. price crosses the midpoint of the event candle.

Entry is priced at the close of the confirmation candle. Research and
validation are evaluated; test remains unused.

## Gate funnel

| Stage | Research events | Validation events |
| --- | ---: | ---: |
| Strong OI input | 573 | 280 |
| No new extreme | 280 | 131 |
| Plus impact decay | 234 | 111 |
| Plus flow weakening | 225 | 107 |
| Plus midpoint re-entry | 171 | 88 |
| All gates simultaneously | 133 | 66 |

The similar funnel rates show that the causal pattern itself is not obviously
distribution-specific.

## Returns from confirmation entry

| Horizon | Research gross | Validation gross | Validation net |
| --- | ---: | ---: | ---: |
| 5m | +5.47 bps | -3.36 bps | -17.36 bps |
| 15m | +2.44 bps | +3.97 bps | -10.03 bps |
| 30m | +3.99 bps | +24.28 bps | +10.28 bps |

The five-minute result fails to transfer. The attractive validation
30-minute mean is not robust:

- median gross return: +5.43 bps;
- only 43.94% of events beat 14 bps costs;
- cluster-bootstrap 95% interval: `[-7.88, +68.23] bps`;
- 10% trimmed mean: +7.19 bps;
- excluding the top three events: +1.60 bps.

The two largest validation returns, +701 and +568 bps, are LINK and ADA rows
from the same market cluster on 2026-02-06. They are correlated observations,
not two independent confirmations.

## Decision

**Reject as a standalone trading rule.**

Requiring post-event confirmation removes hindsight from the entry and creates
a stable event funnel, but it does not produce a stable return distribution.
The apparent 30-minute validation profitability is dominated by one broad
market event and is absent in research.

The result is still useful: the gates describe a recognizable market state,
but they should become model features rather than hard filters. A next model
should predict tail probability or expected MFE/MAE using research only, with
cluster-aware weighting.

