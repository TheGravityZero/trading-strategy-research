# US equities take-profit grid

Same 23-symbol, one-year hourly sample and execution rules as the baseline.
Open positions are excluded from realized performance.

## All directions

| Target from entry | Completed | Open | Mean net | Median net | Win rate |
|---|---:|---:|---:|---:|---:|
| Pivot (~5%) | 21 | 0 | -3.27% | +4.68% | 71.4% |
| 7.5% | 21 | 0 | -1.59% | +7.42% | 71.4% |
| 10% | 20 | 1 | -0.41% | +9.92% | 70.0% |
| 12.5% | 20 | 1 | -0.66% | +12.42% | 65.0% |
| 15% | 20 | 1 | +0.84% | +14.92% | 65.0% |
| **20%** | **20** | **1** | **+3.58%** | **+19.92%** | **65.0%** |
| 25% | 19 | 2 | +2.72% | +14.85% | 57.9% |
| 30% | 18 | 3 | +2.09% | +1.62% | 55.6% |

The best aggregate point in this grid is 20%. Performance deteriorates at
25-30%, while more positions remain unresolved.

## Long-only

| Target from entry | Completed | Open | Mean net | Win rate |
|---|---:|---:|---:|---:|
| Pivot (~5%) | 7 | 0 | +4.80% | 100% |
| 10% | 6 | 1 | +8.68% | 100% |
| 15% | 6 | 1 | +12.85% | 100% |
| 20% | 6 | 1 | +17.02% | 100% |
| 25% | 6 | 1 | +21.18% | 100% |
| 30% | 5 | 2 | +18.60% | 100% |

The apparent long-only optimum is 25%, but it is based on only six completed
trades and was selected on the evaluation sample. The more defensible candidate
for the next out-of-sample test is a fixed 20% target: it is the aggregate
optimum, has fewer unresolved positions than larger targets, and sits below the
edge of the long-only plateau.

This grid is exploratory and does not establish future profitability.
