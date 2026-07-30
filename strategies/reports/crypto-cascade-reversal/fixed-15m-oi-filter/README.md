# Twelve-month open-data event study

> Historical result: этот отчёт построен на старой вселенной из десяти
> контрактов. После перехода на HYPE, BTC, SOL и ETH требуется новый прогон.

## Dataset

- Period: 2025-07-01 through 2026-06-30 UTC.
- Symbols: BTC, ETH, SOL, XRP, BNB, DOGE, ADA, LINK, AVAX and LTC perpetuals.
- Source: public Binance Vision USD-M Futures archives.
- Klines: 5,256,000 one-minute rows.
- Metrics: 1,051,151 five-minute rows.
- Minute gaps: zero for every symbol.
- OI coverage after conservative one-minute publication lag: 99.99%+.
- Raw compressed dataset size: 238 MB.

The universe is fixed rather than point-in-time selected. This is a known
survivorship-selection limitation, although all ten contracts existed for the
entire study period.

## Fixed detector

The event definition was carried over from the seven-day prototype:

- extreme five-minute return;
- abnormal quote volume and candle range;
- directional taker imbalance;
- 15-minute open-interest decline of at least 0.2%;
- 30-minute per-symbol cooldown.

No detector thresholds were selected using validation or test PnL.

## Chronological split

| Split | Period | Events | Independent 10m clusters |
| --- | --- | ---: | ---: |
| Research | 2025-07 through 2025-12 | 2,289 | 1,230 |
| Validation | 2026-01 through 2026-03 | 1,179 | 585 |
| Test | 2026-04 through 2026-06 | 1,158 | 589 |

Total: 4,626 asset-events grouped into 2,404 temporal clusters.

## Fixed 15-minute reversal result

Assumed round-trip cost is 14 bps: 5 bps taker fee plus 2 bps slippage per
side.

| Split | Mean gross | Mean net | Net-positive events |
| --- | ---: | ---: | ---: |
| Research | +2.62 bps | -11.38 bps | 43.86% |
| Validation | +2.36 bps | -11.64 bps | 44.19% |
| Test | +2.68 bps | -11.32 bps | 40.50% |

The sign of the gross effect is stable across all three chronological splits,
but its magnitude is far below assumed execution costs.

## Local versus market-wide events

Test-set mean reversal:

| Scope | Events | Clusters | 5m | 15m | 30m |
| --- | ---: | ---: | ---: | ---: | ---: |
| Local | 354 | 354 | +5.45 bps | +3.64 bps | +4.16 bps |
| Market-wide | 804 | 235 | +2.21 bps | +2.25 bps | +3.53 bps |

Local events have a stronger short-horizon reversal in validation and test,
but still do not cover 14 bps. Market-wide rows are event-weighted, so broad
cascades contribute several correlated asset observations; inference must use
cluster-level resampling.

## Decision

The expanded sample confirms a small, stable **gross reversal effect**, not a
tradeable taker strategy. The original seven-day pattern was not purely random,
but its magnitude was overstated by the small sample.

Current decision: **No-Go for immediate execution, Go for selective
meta-model research.**

The next hypothesis should not attempt to trade every detected event. It should
predict which local events have enough expected move to exceed costs, while
leaving the test period untouched during model development.

## Required next checks

1. Cluster-level bootstrap confidence intervals.
2. Research/validation-only feature and threshold analysis.
3. Next-minute execution and volatility-dependent slippage.
4. PnL attribution by symbol, month, direction and OI-drop quantile.
5. Passive-entry feasibility after absorption.
6. A calibrated baseline model for `P(net return > 0)` trained without test.
