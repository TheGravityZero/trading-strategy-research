# Execution and robustness audit

[Methodology and reproduction](README.md)

Data: `2025-07-01 00:00:00+00:00` — `2026-07-01 00:00:00+00:00` (exclusive), 10 crypto assets.

## Pair accounting: ETHUSDT/BTCUSDT, 1h

A common 360-hour warmup precedes trading. Gross is P&L on the same executed quantities with paid fees/slippage added back; the 0x row is a separately simulated cost-free account. 1x = 5 bps fee + 2 bps slippage on each traded leg notional. Terminal exits are included.

| Strategy | Cost multiplier | Entries | Gross P&L / initial equity | Fees | Slippage | Net return | Max DD | Rebalance turnover |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| correlation-divergence | 0x | 107 | -1.24% | 0.00% | 0.00% | -1.24% | -16.52% | 14.56 |
| correlation-divergence | 1x | 107 | -2.33% | 9.72% | 3.89% | -15.94% | -21.52% | 13.53 |
| correlation-divergence | 2x | 107 | -3.31% | 17.96% | 7.18% | -28.46% | -29.42% | 12.60 |
| regression-spread | 0x | 104 | 0.96% | 0.00% | 0.00% | 0.96% | -10.02% | 26.41 |
| regression-spread | 1x | 104 | 0.83% | 10.83% | 4.33% | -14.34% | -18.14% | 25.02 |
| regression-spread | 2x | 104 | 0.70% | 20.02% | 8.01% | -27.33% | -29.17% | 23.77 |
| crypto-stat-arb | 0x | 104 | 0.96% | 0.00% | 0.00% | 0.96% | -10.02% | 26.41 |
| crypto-stat-arb | 1x | 104 | 0.83% | 10.83% | 4.33% | -14.34% | -18.14% | 25.02 |
| crypto-stat-arb | 2x | 104 | 0.70% | 20.02% | 8.01% | -27.33% | -29.17% | 23.77 |

## Quarterly chronological evaluation

Each test quarter follows three months of training/warmup; trade state resets to cash. Rolling features update causally during test. Parameters stay fixed; no best-window selection. These dates were already inspected in earlier research, so this is not a fresh holdout.

| Strategy | Train start | Test start | Test end (exclusive) | Entries | Gross | Fees + slippage | Net | Max DD |
|---|---|---|---|---:|---:|---:|---:|---:|
| correlation-divergence | 2025-07-01 | 2025-10-01 | 2026-01-01 | 27 | 4.71% | 4.16% | 0.55% | -5.27% |
| correlation-divergence | 2025-10-01 | 2026-01-01 | 2026-04-01 | 32 | 4.46% | 4.66% | -0.21% | -7.44% |
| correlation-divergence | 2026-01-01 | 2026-04-01 | 2026-07-01 | 30 | 4.29% | 4.48% | -0.19% | -4.08% |
| regression-spread | 2025-07-01 | 2025-10-01 | 2026-01-01 | 31 | 0.75% | 4.51% | -3.76% | -5.96% |
| regression-spread | 2025-10-01 | 2026-01-01 | 2026-04-01 | 28 | 0.26% | 4.18% | -3.93% | -6.24% |
| regression-spread | 2026-01-01 | 2026-04-01 | 2026-07-01 | 32 | 1.26% | 4.81% | -3.56% | -8.17% |
| crypto-stat-arb | 2025-07-01 | 2025-10-01 | 2026-01-01 | 31 | 0.75% | 4.51% | -3.76% | -5.96% |
| crypto-stat-arb | 2025-10-01 | 2026-01-01 | 2026-04-01 | 28 | 0.26% | 4.18% | -3.93% | -6.24% |
| crypto-stat-arb | 2026-01-01 | 2026-04-01 | 2026-07-01 | 32 | 1.26% | 4.81% | -3.56% | -8.17% |

## Refit cointegration each quarter, 4h

Each fold screens all 45 pairs with Holm correction on its own preceding three months. Selected pairs receive equal, segregated capital shares; an empty selection stays in cash. This does not net exposures to the same asset across pairs.

| Strategy | Train start | Test start | Selected pairs (Holm p) | Selected / candidates | Entries | Gross attribution | Net | Max DD |
|---|---|---|---|---:|---:|---:|---:|---:|
| cointegration | 2025-07-01 | 2025-10-01 | — | 0 / 45 | 0 | 0.00% | 0.00% | 0.00% |
| mean-reversion | 2025-07-01 | 2025-10-01 | — | 0 / 45 | 0 | 0.00% | 0.00% | 0.00% |
| cointegration | 2025-10-01 | 2026-01-01 | BNBUSDT/SOLUSDT (0.0376) | 1 / 45 | 9 | 0.51% | -1.64% | -9.88% |
| mean-reversion | 2025-10-01 | 2026-01-01 | BNBUSDT/SOLUSDT (0.0376) | 1 / 45 | 5 | 3.59% | 2.37% | -1.41% |
| cointegration | 2026-01-01 | 2026-04-01 | DOGEUSDT/LTCUSDT (0.0058) | 1 / 45 | 12 | 0.24% | -2.59% | -8.60% |
| mean-reversion | 2026-01-01 | 2026-04-01 | DOGEUSDT/LTCUSDT (0.0058) | 1 / 45 | 6 | 3.35% | 1.90% | -2.40% |

## Expanded crypto sample: ten assets, 15min

Fixed existing parameters for TP 10/15/20%; this is universe expansion on the same historical year. All-marked trade means include open positions at their last stored close. The portfolio uses equal initial cash sleeves per symbol, reinvests within each sleeve, skips overlapping signals for occupied symbols and charges actual-notional costs. Positions still open at the boundary are liquidated at their last close.

| Strategy | TP | Fills | Closed | Open | Mean net, closed | Mean net, all marked | Portfolio entries | Overlaps skipped | Portfolio net | Portfolio max DD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| weekly-pivot-limit | 10% | 14 | 13 | 1 | 0.69% | 0.47% | 14 | 0 | 0.80% | -8.12% |
| weekly-pivot-limit | 15% | 14 | 13 | 1 | -2.17% | -2.19% | 14 | 0 | -3.06% | -13.67% |
| weekly-pivot-limit | 20% | 14 | 13 | 1 | 0.13% | -0.05% | 14 | 0 | -0.02% | -13.15% |
| defended-pivot-hvn-limit | 10% | 5 | 2 | 3 | 9.86% | -3.71% | 5 | 0 | -1.85% | -4.21% |
| defended-pivot-hvn-limit | 15% | 5 | 1 | 4 | 14.86% | -6.89% | 5 | 0 | -3.44% | -6.37% |
| defended-pivot-hvn-limit | 20% | 5 | 1 | 4 | 19.86% | -5.89% | 5 | 0 | -2.94% | -6.34% |
| defended-pivot-hvn-reclaim | 10% | 4 | 2 | 2 | 9.86% | 0.67% | 4 | 0 | 0.27% | -2.11% |
| defended-pivot-hvn-reclaim | 15% | 4 | 1 | 3 | 14.86% | -3.27% | 4 | 0 | -1.31% | -4.38% |
| defended-pivot-hvn-reclaim | 20% | 4 | 1 | 3 | 19.86% | -2.02% | 4 | 0 | -0.81% | -4.36% |

## Previously omitted open positions in saved sector reports

Only configurations with open trades are listed here; every sector report now includes all-marked means.

| Strategy | Sector | Configuration | Closed / open | Mean net, closed | Mean net, all marked |
|---|---|---|---:|---:|---:|
| ath-retest-volume-short | it | tp10-hold60d | 4 / 1 | 3.67% | 2.93% |
| ath-retest-volume-short | it | tp15-hold60d | 4 / 1 | -2.63% | -2.11% |
| ath-retest-volume-short | it | tp20-hold60d | 4 / 1 | -1.38% | -1.11% |
| ath-retest-volume-short | metals | tp10-hold60d | 3 / 1 | -6.75% | -6.70% |
| ath-retest-volume-short | metals | tp15-hold60d | 3 / 1 | -5.08% | -5.45% |
| ath-retest-volume-short | metals | tp20-hold60d | 3 / 1 | -3.41% | -4.20% |
| ath-retest-volume-short | oil | tp10-hold60d | 3 / 1 | -12.00% | -9.41% |
| ath-retest-volume-short | oil | tp15-hold60d | 3 / 1 | -12.00% | -9.41% |
| ath-retest-volume-short | oil | tp20-hold60d | 3 / 1 | -12.00% | -9.41% |
| defended-pivot-hvn-limit | crypto | tp10-hold60d | 0 / 2 | — | -7.82% |
| defended-pivot-hvn-limit | crypto | tp15-hold60d | 0 / 2 | — | -7.82% |
| defended-pivot-hvn-limit | crypto | tp20-hold60d | 0 / 2 | — | -7.82% |
| defended-pivot-hvn-reclaim | crypto | tp10-hold60d | 0 / 2 | — | -8.15% |
| defended-pivot-hvn-reclaim | crypto | tp15-hold60d | 0 / 2 | — | -8.15% |
| defended-pivot-hvn-reclaim | crypto | tp20-hold60d | 0 / 2 | — | -8.15% |
| weekly-pivot-limit | it | tp10-hold60d | 4 / 1 | 4.59% | 4.72% |
| weekly-pivot-limit | it | tp15-hold60d | 4 / 1 | 5.84% | 5.72% |
| weekly-pivot-limit | it | tp20-hold60d | 4 / 1 | 7.09% | 6.72% |
| weekly-pivot-limit | metals | tp10-hold60d | 3 / 1 | 9.92% | 3.33% |
| weekly-pivot-limit | metals | tp15-hold60d | 3 / 1 | 6.87% | 1.04% |
| weekly-pivot-limit | metals | tp20-hold60d | 3 / 1 | -4.80% | -7.71% |

Funding, borrowing, liquidity, margin calls and market impact beyond the stated slippage are excluded. Expanded long portfolios inherit the original OHLC fill/stop assumptions; they do not validate actual order-book execution. Correlated trades and repeated TP variants are not independent observations. No confidence claim or live-trading recommendation follows.
