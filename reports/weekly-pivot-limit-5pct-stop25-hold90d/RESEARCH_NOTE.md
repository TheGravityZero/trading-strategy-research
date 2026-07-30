# Weekly pivot limit — 90-day holding experiment

## Configuration

- Entry: 5% beyond confirmed weekly pivot.
- Limit lifetime: four hours.
- Take-profit: pivot.
- Permanent stop-loss: 25% adverse from entry.
- Breakeven disabled.
- Maximum holding time: 90 days.

## Result

| Symbol | Exit | Holding | Gross | Net |
| --- | --- | ---: | ---: | ---: |
| AVAXUSDT | pivot take-profit | 96 minutes | +5.26% | +5.12% |
| BTCUSDT | 90-day time exit | 129,600 minutes | +2.38% | +2.24% |

Mean net return: **+3.68%**. Both trades are positive and neither reaches the
25% stop.

## Important limitations

1. There are only two filled trades and no research fill.
2. The BTC trade enters on 2026-01-31 and exits on 2026-05-01. Its outcome
   therefore consumes prices from the nominal test period, despite the entry
   event belonging to validation. This is not a clean validation result.
3. Funding payments are not included.
4. Capital is tied up for 90 days, so raw return is not comparable with a
   short-horizon strategy without capital and exposure accounting.
5. Maximum adverse excursion is not yet reported.

This variant is an interesting scenario, not statistical evidence of edge.

