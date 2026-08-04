# ATH Retest Volume Short

A standalone short-only strategy that enters after a significant correction
and a failed return to the previous ATH rather than shorting every new ATH.

## Scenario

1. Record the causal ATH.
2. Wait for a configurable minimum correction from the ATH.
3. Wait for the high to return to a configured zone below the ATH without
   setting a new maximum.
4. Build a 30-bin volume profile from the ATH through the failed retest.
5. Select the high-volume node with the highest dollar volume in the upper
   half of the range.
6. After price breaks below the HVN, wait for a retest from below and enter
   short at the node price.

The retest order remains active for 5 days. Only one position or pending setup
is allowed per symbol.

## Risk and exit

- Stop-loss: a fixed percentage above entry, the causal ATH, or the upper
  boundary of the HVN bin.
- Take-profit: 10%, 15%, or 20% below entry.
- Maximum holding period: 60 days.
- TP is disabled on the fill candle; a conservative stop remains enabled.
- Costs: 14 bps round trip for crypto and 8 bps for equities.

The volume profile is approximate: all volume in an OHLC candle is assigned
to its typical price, `(high + low + close) / 3`. An exact profile would
require trade-level data or lower-timeframe candles.

## Run

```bash
PYTHONPATH=src python3 strategies/run_ath_retest_volume_short.py \
  --sector semiconductors \
  --minimum-correction-percent 15 \
  --ath-retest-distance-percent 3 \
  --profile-bins 30 \
  --entry-lifetime-days 5 \
  --take-profit-percent 10 \
  --stop-mode ath
```

Run the complete `correction 7/10/12% × retest 3/5/7% × stop ATH/HVN × TP
10/15/20%` grid separately:

```bash
PYTHONPATH=src python3 strategies/run_ath_retest_volume_grid.py \
  --sector semiconductors
```

## Results

[Aggregate results](RESULTS.md)

[Parameter-grid results](GRID_RESULTS.md)

- [crypto](crypto/result.md)
- [IT](it/result.md)
- [semiconductors](semiconductors/result.md)
- [oil](oil/result.md)
- [metals](metals/result.md)
