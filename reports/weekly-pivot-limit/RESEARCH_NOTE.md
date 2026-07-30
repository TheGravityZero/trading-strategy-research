# ConfirmedWeeklyPivotLimit

## Rules

- Weekly pivot uses two completed weeks on each side.
- A pivot becomes tradable only after both right-hand weeks have closed.
- A later detector event must cross the confirmed pivot.
- Long limit: `pivot low × 0.93`.
- Short limit: `pivot high × 1.07`.
- Order lifetime: 240 minutes after the crossing event.
- Initial stop: 25% adverse from entry.
- After five completed minutes, stop moves to entry.
- Take-profit: the pivot itself.
- Maximum holding time: seven days.
- If stop and take-profit are both inside one minute candle, stop is assumed
  to execute first.
- Test is not used.

## Result

- Confirmed pivot-cross setups: 17.
- Filled limit orders: 1.
- Filled trade belongs to validation.
- Exit: breakeven after five minutes.
- Gross return: 0%.
- Net return after assumed 14 bps round-trip costs: -0.14%.

No research trade was filled, so transfer from research to validation cannot be
evaluated.

## Decision

The implementation is valid but the combination of a confirmed weekly pivot,
a 7% offset and a four-hour order lifetime is too rare for the current
ten-symbol, one-year dataset.

Possible coverage experiments must be defined before looking at test:

1. keep 7% but extend order lifetime;
2. keep four hours but compare 3%, 5% and 7% offsets on research only;
3. use confirmed daily pivots while preserving the same execution rules;
4. expand the point-in-time universe.

