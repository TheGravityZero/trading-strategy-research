# Open-interest filter experiment

## Change from baseline

The detector now consumes public Binance Futures metrics sampled every five
minutes. A metric stamped at `t` is treated as available from `t + 1 minute`.
An event must satisfy the original price/volume/taker-flow conditions and:

`15-minute open-interest change <= -0.2%`

The threshold was fixed before this run. It was not selected by maximizing PnL
on the evaluated period.

## Comparison on the same BTC/ETH period

| Variant | Events | Mean net/event | Compounded event return |
| --- | ---: | ---: | ---: |
| Original auto-switch baseline | 98 | -15.10 bps | -13.79% |
| OI filter + auto switch | 25 | -13.89 bps | -3.42% |
| OI filter + fixed 15m reversal | 25 | -5.46 bps | -1.36% |

The compounded event return treats events as sequential and is not yet a
capital-aware portfolio return.

## Event study

For the 25 OI-filtered events, mean direction-adjusted forward returns were:

| Horizon | Continuation | Reversal |
| --- | ---: | ---: |
| 1 minute | +1.69 bps | -1.69 bps |
| 5 minutes | -3.30 bps | +3.30 bps |
| 15 minutes | -8.54 bps | +8.54 bps |
| 30 minutes | -12.45 bps | +12.45 bps |

There is an exploratory reversal pattern after the first minute, but its mean
15-minute gross move is below the assumed 14 bps round-trip cost. The current
sample is also far too small and correlated to establish significance.

## Decision

The OI filter is directionally useful: it removes roughly three quarters of
the original candidates and reveals a cleaner reversal-shaped average path.
The strategy is still a **No-Go** at the current frequency and cost model.

Next, evaluate the detector over 6–12 months and a broader liquid universe,
cluster simultaneous events, and use an untouched chronological test split.
Do not tune the threshold or horizon further on this seven-day sample.
