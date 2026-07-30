# FourWeekLevelReversal

Standalone strategy using extrema of the four previous completed
Monday-Sunday UTC weeks.

## Rules

For a downward impulse:

1. the preceding four-hour return is aligned downward by at least 10 bps;
2. the event reaches the four-week low within a 10 bps touch zone, or sweeps it
   by no more than 100 bps;
3. price closes back above the level within five completed minutes;
4. enter long at the reclaim candle close.

The upward/short case is symmetric. The input universe already consists of
price/volume/taker-flow events with an OI-decline filter. Test is not used.

## Funnel

| Split | Input events | Touches | Reclaims | Eligible trades |
| --- | ---: | ---: | ---: | ---: |
| Research | 2,289 | 132 | 10 | 6 |
| Validation | 1,179 | 116 | 8 | 6 |

The level interaction is common enough, but a reclaim within five minutes is
rare.

## Fixed-horizon result

| Split | Horizon | Events | Gross mean | Net mean |
| --- | ---: | ---: | ---: | ---: |
| Research | 15m | 6 | -0.08 bps | -14.08 bps |
| Research | 30m | 6 | +2.02 bps | -11.98 bps |
| Research | 60m | 6 | -9.69 bps | -23.69 bps |
| Validation | 15m | 6 | +2.93 bps | -11.07 bps |
| Validation | 30m | 6 | -17.45 bps | -31.45 bps |
| Validation | 60m | 6 | -9.38 bps | -23.38 bps |

The sample is too small for inference and all bootstrap intervals cross zero.
The strict strategy is currently a No-Go.

## Next variants

Keep the strategy module separate, but compare mutually exclusive states:

1. touch without a sweep;
2. sweep and reclaim;
3. sweep, reclaim and weak retest;
4. breakout without reclaim, evaluated as continuation.

The research objective should be increasing independent coverage without
selecting parameters on validation or test.

