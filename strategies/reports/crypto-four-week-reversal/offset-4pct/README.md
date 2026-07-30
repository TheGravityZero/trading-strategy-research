# FourWeekLevelReversal — 4% offset limit

## Entry

After a detected break of the four-week level:

- long limit: `four_week_low × 0.96`;
- short limit: `four_week_high × 1.04`;
- order lifetime: 60 completed minutes;
- fill: exact limit price when minute low/high crosses it;
- no reclaim is required.

The rule is symmetric and test remains unused.

## Coverage

- Input research/validation events: 3,468.
- Four-week level touches/breaks: 248.
- Limit fills: 146.
- Fills with aligned preceding four-hour trend: 130.
- Research: 62 trades in 44 clusters.
- Validation: 68 trades in 26 clusters.

## Results

| Split | Horizon | Gross mean | Median | Net mean |
| --- | ---: | ---: | ---: | ---: |
| Research | 15m | -357.15 bps | -235.18 bps | -371.15 bps |
| Research | 30m | -357.31 bps | -257.75 bps | -371.31 bps |
| Research | 60m | -320.86 bps | -237.53 bps | -334.86 bps |
| Validation | 15m | -515.60 bps | -538.69 bps | -529.60 bps |
| Validation | 30m | -484.23 bps | -526.18 bps | -498.23 bps |
| Validation | 60m | -460.89 bps | -466.70 bps | -474.89 bps |

All cluster-bootstrap intervals are strictly negative. Price tends to continue
moving in the breakout direction after the 4% limit fill.

## Decision

**Reject the unconditional 4% counter-trend limit entry.**

The implementation follows the requested rule, but it catches continuing
deleveraging rather than exhaustion. A 4% displacement may still be useful as
an alert or setup condition, followed by reclaim/absorption confirmation.

The stored stop level is not yet executed by the event backtest, so these are
fixed-horizon returns rather than stop-loss-controlled trade returns.
