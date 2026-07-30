# Sequential hypothesis test: OI depth, then absorption

## Protocol

Thresholds were derived exclusively from the research split
(2025-07 through 2025-12). Validation covers 2026-01 through 2026-03. The test
split was not used for threshold selection or evaluation in this experiment.

Assumed round-trip cost: 14 bps.

Cluster bootstrap resamples 10-minute temporal event clusters rather than
treating correlated asset-events as independent.

## Hypothesis 1: deeper OI decline predicts stronger reversal

The research-set quartiles of 15-minute OI change were frozen and applied to
validation. The strongest bucket is:

`OI change <= -0.5478%`

### Five-minute reversal by OI bucket

| OI bucket | Research gross | Validation gross |
| --- | ---: | ---: |
| Q1, deepest decline | +5.20 bps | +0.83 bps |
| Q2 | +3.50 bps | +1.54 bps |
| Q3 | +3.77 bps | +2.55 bps |
| Q4, shallowest decline | +0.55 bps | +1.43 bps |

The research ordering is directionally plausible but not monotonic, and Q1
does not outperform on validation.

### Strong-OI subset

| Horizon | Research gross | Validation gross | Validation net |
| --- | ---: | ---: | ---: |
| 5m | +5.20 bps | +0.83 bps | -13.17 bps |
| 15m | -3.22 bps | +7.95 bps | -6.06 bps |
| 30m | -14.17 bps | +15.81 bps | +1.81 bps |

The attractive validation 30-minute mean is not confirmed on research. Its
95% cluster-bootstrap interval is `[-6.32, +40.85] bps`, crossing zero widely.
Validation median gross return is 13.50 bps, still below costs, and exactly 50%
of events beat costs.

**Decision:** hypothesis 1 is not confirmed as a standalone selection rule.
OI depth may interact with horizon or market regime, but selecting the
30-minute result would be post-hoc.

## Hypothesis 2: absorption improves the strong-OI subset

The existing causal efficiency proxy compares current one-minute price
movement per log quote-volume with the maximum of the preceding five minutes.
Lower values mean high activity is producing less marginal price movement.

Within strong-OI research events, the lowest research quartile was frozen:

`efficiency ratio <= 0.5119`

### Strong OI plus absorption

| Horizon | Research gross | Validation gross | Validation net |
| --- | ---: | ---: | ---: |
| 5m | +13.67 bps | -5.43 bps | -19.43 bps |
| 15m | +1.50 bps | +4.82 bps | -9.18 bps |
| 30m | -25.94 bps | +12.19 bps | -1.81 bps |

Coverage falls from 573 to 144 research events and from 280 to 69 validation
events. The apparent research improvement at 5 minutes reverses sign on
validation. All bootstrap intervals cross zero.

**Decision:** hypothesis 2 is rejected in its current definition. The proxy is
too noisy and likely conflates genuine absorption with a temporary pause
inside a continuing move.

## Conclusions

1. A deeper OI decline alone does not reliably identify stronger short-term
   rebounds.
2. The current single-minute absorption proxy does not generalize.
3. Neither filter produces a stable mean move above 14 bps costs.
4. Test remains unused for this experiment and should stay locked.

## Better formulation of absorption

The next absorption test should require a short causal sequence rather than
one ratio at the event timestamp:

1. forced impulse and OI decline;
2. no new extreme for 1–3 minutes;
3. continued aggressive flow with declining price impact;
4. taker imbalance weakens or changes sign;
5. entry only after price re-enters the impulse candle.

This changes the question from “is impact low at detection?” to “has the
market demonstrated absorption after detection?”

