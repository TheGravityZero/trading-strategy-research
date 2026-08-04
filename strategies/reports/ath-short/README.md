# ATH Short

A standalone short-only strategy for cryptocurrencies and U.S. equities.

## Idea and signal

Before each candle, the strategy calculates the causal ATH: the highest high
strictly available before that candle. When the current candle sets a new
high, the strategy places a limit short 7% above the previous ATH:

`entry = prior_ath × 1.07`.

The order remains active for 4 hours. Only one active order or short position
is allowed per symbol. For equities, ATH is limited to the available one-year
Yahoo history and is not the full exchange all-time high.

## Exit

- Stop-loss: 15% above entry.
- Take-profit variants: 10%, 15%, and 20% below entry.
- Maximum holding period: 60 days.
- TP is disabled on the fill candle because the intrabar path is unknown; a
  conservative stop remains enabled.
- If TP and stop are both reached on a later candle, stop takes priority.

Crypto uses 15m candles and equities use 1h candles. Round-trip fees and
slippage are deducted: 14 bps for crypto and 8 bps for equities. Funding,
borrow fees, limit-order queue position, and market impact are not modeled.

## Run

```bash
PYTHONPATH=src python3 strategies/run_ath_short.py \
  --sector semiconductors \
  --entry-offset-percent 7 \
  --take-profit-percent 10 \
  --stop-loss-percent 15 \
  --order-lifetime-hours 4 \
  --maximum-holding-days 60
```

Sectors: `crypto`, `it`, `semiconductors`, `oil`, and `metals`.

## Results

[Aggregate results](RESULTS.md)

- [crypto](crypto/result.md)
- [IT](it/result.md)
- [semiconductors](semiconductors/result.md)
- [oil](oil/result.md)
- [metals](metals/result.md)
