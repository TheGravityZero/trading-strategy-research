# Defended Pivot Long

A standalone long-only strategy that trades weekly levels with elevated
relative volume and a confirmed prior defense.

## Relative volume

Dollar volume is calculated for each week:

`weekly_dollar_volume = Σ(close × volume)`.

The baseline is the median of the previous 12 completed weeks, excluding the
pivot week. A pivot is eligible when:

`pivot_volume / baseline_volume ≥ 1.5`.

The comparison is performed independently for each asset.

## First defense

After causal confirmation of a pivot low, the strategy waits for:

1. A touch of the `pivot ± 0.5 daily ATR(14)` zone.
2. A rise to `pivot + 1.5 ATR` within five days of the touch.

ATR uses only previously completed days. The first defense does not trigger an
entry; it only changes the level state to `defended`.

## Trade entry

After defense confirmation, the strategy waits for the next downward break of
the pivot and places a limit buy:

`entry = pivot × 0.95`.

The order remains active for 4 hours. Stop-loss is 25% below entry, the
maximum holding period is 60 days, and TP values of 10%, 15%, and 20% are
tested.

## Run

```bash
PYTHONPATH=src python3 research/runners/run_defended_pivot_long.py \
  --sector crypto \
  --minimum-volume-ratio 1.5 \
  --touch-zone-atr 0.5 \
  --minimum-bounce-atr 1.5 \
  --bounce-window-days 5 \
  --entry-offset-percent 5 \
  --take-profit-percent 10
```

Sectors: `crypto`, `it`, `semiconductors`, `oil`, and `metals`.

## Results

[Aggregate results](RESULTS.md)

- [crypto](crypto/result.md)
- [IT](it/result.md)
- [semiconductors](semiconductors/result.md)
- [oil](oil/result.md)
- [metals](metals/result.md)

The initial configuration found defended levels but produced no fills: after
the repeated break, price did not reach the limit another 5% below the pivot
within four hours.
