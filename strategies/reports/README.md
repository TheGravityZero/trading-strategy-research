# Backtest results

Каждый `result.md` объединяет результаты разных конфигураций одной стратегии для одного сектора. CSV/JSON с полными сделками создаются локально и исключены из Git.

| Стратегия | crypto | it | semiconductors | oil | metals |
|---|---|---|---|---|---|
| Cascade reversal | [result](cascade-reversal/crypto/result.md) | N/A | N/A | N/A | N/A |
| Four-week reversal | [result](four-week-reversal/crypto/result.md) | N/A | N/A | N/A | N/A |
| Weekly pivot limit | [result](weekly-pivot-limit/crypto/result.md) | [result](weekly-pivot-limit/it/result.md) | [result](weekly-pivot-limit/semiconductors/result.md) | [result](weekly-pivot-limit/oil/result.md) | [result](weekly-pivot-limit/metals/result.md) |

`N/A` означает, что стратегия требует liquidation-cascade событий и minute futures metrics, которых нет для equity-секторов.
