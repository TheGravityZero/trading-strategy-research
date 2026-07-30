# Baseline research note

## Dataset

- Source: Binance Vision, USD-M Futures daily kline archive.
- Symbols: `BTCUSDT`, `ETHUSDT`.
- Interval: 1 minute.
- Period: 2025-05-01 through 2025-05-07 UTC.
- Approximate observations: 20,160.

## Fixed baseline assumptions

- Proxy event: joint extreme in 5-minute return, quote volume, candle range and
  directional taker imbalance.
- Cooldown: 30 minutes per symbol.
- Continuation horizon: 5 minutes.
- Reversal horizon: 15 minutes.
- Exhaustion proxy threshold: 0.65.
- Fees: 5 bps per side.
- Slippage: 2 bps per side.
- Total round-trip cost: 14 bps.

## Result

- Trades: 98.
- Compounded net return: -13.79%.
- Mean net return per event: -15.10 bps.
- Hit rate: 17.35%.
- Maximum drawdown: -13.64%.

This is a smoke test, not an out-of-sample performance claim. Seven days and
two correlated instruments are insufficient for statistical inference.

## Interpretation

The current proxy detector fires too frequently for a rare liquidation-cascade
strategy. It is likely detecting ordinary high-volume impulses. Short holding
periods also make the baseline highly sensitive to its 14 bps cost assumption.
There is no evidence yet that the hard-coded continuation/reversal switch has
positive net edge.

## Next experiment

1. Separate detector calibration and untouched evaluation periods.
2. Add open-interest change or Binance futures metrics to distinguish forced
   deleveraging from ordinary volume.
3. Cluster simultaneous BTC/ETH/altcoin events.
4. Analyse forward returns by return/volume/impact quantiles before defining a
   trading rule.
5. Use next-minute execution and volatility-dependent slippage.
6. Expand to at least 6–12 months and a point-in-time liquid universe.

