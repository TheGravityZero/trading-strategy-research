# Defended Pivot HVN Reclaim

A standalone confirmation-based long-only strategy for a defended weekly
pivot.

The HVN is built from the first defense in the same way as for HVN Limit.
After the next break, the strategy waits for a sweep below the HVN's lower
boundary and a candle close back above it. Entry occurs at the reclaim
candle's close.

The reclaim window is 5 days. SL is 25%, TP is 10%/15%/20%, and the maximum
holding period is 60 days.

```bash
PYTHONPATH=src python3 research/runners/run_defended_pivot_hvn_reclaim.py \
  --sector crypto --take-profit-percent 10
```

[Aggregate results](RESULTS.md)

Дополнительный crypto-прогон на 4h за 2025-07-01—2026-07-01 дал по 2
заполнения и 0 полностью закрытых сделок для TP 10%, 15% и 20%. Результаты
сохранены в `crypto/4h-tp10/`, `crypto/4h-tp15/` и `crypto/4h-tp20/`; они не
смешиваются с основной 15m-сводкой.

- [crypto](crypto/result.md)
- [IT](it/result.md)
- [semiconductors](semiconductors/result.md)
- [oil](oil/result.md)
- [metals](metals/result.md)
