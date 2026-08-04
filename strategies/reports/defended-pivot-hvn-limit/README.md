# Defended Pivot HVN Limit

A standalone long-only strategy for an already-defended weekly pivot with
elevated relative volume.

After the first defense, it builds a volume profile within `pivot ±1 ATR`:

- profile window: first touch through confirmation of a 1.5 ATR bounce;
- 30 price bins;
- weight: `close × volume`;
- HVN: the bin with the highest dollar volume.

After the next pivot break, the strategy places a limit buy at the HVN center.
The order remains active for 5 days. SL is 25%, TP is 10%/15%/20%, and the
maximum holding period is 60 days.

```bash
PYTHONPATH=src python3 strategies/run_defended_pivot_hvn_limit.py \
  --sector crypto --take-profit-percent 10
```

[Aggregate results](RESULTS.md)

- [crypto](crypto/result.md)
- [IT](it/result.md)
- [semiconductors](semiconductors/result.md)
- [oil](oil/result.md)
- [metals](metals/result.md)
