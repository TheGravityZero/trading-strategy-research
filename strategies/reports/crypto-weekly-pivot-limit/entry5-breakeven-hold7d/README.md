# ConfirmedWeeklyPivotLimit — 5% entry / 25% initial stop

## Configuration

- Long entry: `pivot low × 0.95`.
- Short entry: `pivot high × 1.05`.
- Limit lifetime: four hours.
- Take-profit: pivot.
- Initial stop-loss: 25% adverse from entry.
- Breakeven activation: after five completed minutes.
- Maximum holding: seven days.
- Test is not used.

If the market is already beyond entry when breakeven activates, the backtest
exits at the activation candle open rather than assuming an impossible fill at
entry.

## Result

- Confirmed pivot-cross setups: 17.
- Filled orders: 2.
- Research fills: 0.
- Validation fills: 2.

| Symbol | Exit | Gross | Net |
|---|---|---:|---:|
| AVAXUSDT | Breakeven activation at available price | -2.59% | -2.73% |
| BTCUSDT | Breakeven | 0.00% | -0.14% |

Mean validation net return: **−1.43%**. Конфигурация статистически неоценима:
обе сделки относятся к validation, в research исполнений нет.
