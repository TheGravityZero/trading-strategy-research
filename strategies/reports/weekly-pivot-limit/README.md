# Weekly Pivot Limit

A long-only mean-reversion strategy around confirmed weekly pivot lows for
cryptocurrencies and U.S. equities.

## Idea

After breaking a significant weekly low, price may continue lower before
bouncing. The strategy does not buy directly at the level: after the break it
places a limit order farther below the pivot to enter closer to local
capitulation.

## Pivot formation

Candles are aggregated into weeks using the relevant market calendar:

- crypto: UTC, primary timeframe `15m`;
- equities: `America/New_York`, timeframe `1h`.

A weekly low is a pivot low when it is the minimum in a symmetric five-week
window: two weeks to the left, the current week, and two weeks to the right.
The level becomes available only after both right-hand weeks have closed.
This prevents look-ahead bias: a pivot cannot be used before confirmation.

## Entry

Only the first subsequent break is used for each confirmed pivot:

1. The previous candle closes at or above the pivot.
2. The current candle's low crosses below the pivot, creating the trigger.
3. Place a limit buy:

   `entry = pivot × (1 − entry_offset_percent / 100)`.

4. The order remains active for `order_lifetime_hours`. If price does not
   touch entry during that period, the setup remains unfilled.

The default configuration uses a 5% offset and a 4-hour order lifetime.

## Exit

- Take-profit is defined as a percentage above entry. The current grid tests
  +10%, +15%, and +20%.
- The default stop-loss is 25% below entry.
- If neither TP nor SL is reached, the position closes at the last available
  price after `maximum_holding_days`, normally 60 days.
- If the history ends earlier, the position is marked `open` and excluded
  from realized performance.

A conservative stop is allowed on the fill candle, while take-profit is
disabled because OHLC cannot determine whether TP occurred before or after
the limit-order touch. If stop and TP are both reached on a later candle,
stop takes priority.

## Costs

Net return is calculated after round-trip fees and slippage:

`net_return = gross_return − 2 × (fee_bps_per_side + slippage_bps_per_side)`.

Current assumptions:

| Market | Fee per side | Slippage per side | Round trip |
|---|---:|---:|---:|
| Crypto | 5 bps | 2 bps | 14 bps |
| Equities | 1 bp | 3 bps | 8 bps |

Perpetual futures funding, order-size impact, and limit-order queue position
are not modeled.

## Run

From the repository root:

```bash
PYTHONPATH=src python3 strategies/run_weekly_pivot_limit.py --sector crypto
PYTHONPATH=src python3 strategies/run_weekly_pivot_limit.py --sector it
PYTHONPATH=src python3 strategies/run_weekly_pivot_limit.py --sector semiconductors
PYTHONPATH=src python3 strategies/run_weekly_pivot_limit.py --sector oil
PYTHONPATH=src python3 strategies/run_weekly_pivot_limit.py --sector metals
```

Example custom configuration:

```bash
PYTHONPATH=src python3 strategies/run_weekly_pivot_limit.py \
  --sector crypto \
  --crypto-interval 30min \
  --entry-offset-percent 5 \
  --take-profit-percent 10 \
  --stop-loss-percent 25 \
  --order-lifetime-hours 4 \
  --maximum-holding-days 60
```

## Results

[Aggregate results](RESULTS.md)

Sector-level configuration summaries:

- [crypto](crypto/result.md)
- [IT](it/result.md)
- [semiconductors](semiconductors/result.md)
- [oil](oil/result.md)
- [metals](metals/result.md)

The current one-year sample contains few trades, so results should be treated
as exploratory and validated on a longer out-of-sample period.
