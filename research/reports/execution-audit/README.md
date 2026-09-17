# Execution and robustness audit

[Results](RESULTS.md) separate signal P&L, execution costs, chronological folds,
and the effect of including open trades. This is an offline diagnostic of the
existing strategies, with no parameter optimization and no live orders.

## Reproduce

From the repository root, using the research extra (`statsmodels`):

```bash
PYTHONPATH=src .venv/bin/python research/runners/run_execution_audit.py
PYTHONPATH=src .venv/bin/python research/build_results.py
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests
```

The runner reads cached Binance archives only. The fixed experiment covers
2025-07-01 through 2026-07-01 exclusive, UTC, for ADA, AVAX, BNB, BTC, DOGE,
ETH, LINK, LTC, SOL and XRP against USDT. All source candles are checked for
coverage before 15-minute aggregation. Hourly and 4-hour bars come from the
same validated frames. Canonical frame hashes and all configurations are stored
in `latest/metadata.json`. CSV/JSON are local artifacts excluded from Git;
Markdown reports contain the results required to review the experiment.

## Pair execution

`src/trading_strategy/strategies/execution.py` tracks cash and actual quantities.
The ETH/BTC signal rules and parameters are retained from the existing three
baselines, including their exit bands. This audit does not optimize or repair
the signal rules. In particular, a jump across the exit band is not necessarily
an exit under those legacy rules.

- A signal and log-regression beta from close t execute at open t+1. Price gaps
  before the first fill do not accrue to a position that does not yet exist.
- Target dollar weights are `position/(1+abs(beta))` for Y and
  `-position*beta/(1+abs(beta))` for X, based on pre-cost opening equity.
- Quantities rebalance every active bar. Drift and beta changes incur turnover
  on both legs, even when the long/short direction stays the same.
- Fees and slippage are separate cash costs on actual traded notional. Defaults
  are 5 and 2 bps respectively. 0x and 2x scenarios rerun the whole account.
- Inventory is marked to close every bar, including losing open positions.
  Final inventory is liquidated at the last close, with costs.
- `net P&L = gross P&L - fees - slippage` holds exactly. Gross attribution adds
  paid costs back for the same executed quantities; it is not the independently
  reinvested 0x-cost account. All figures use initial equity of one.
- Capital exhaustion raises an error rather than continuing with a negative
  account. Funding, borrowing, liquidity and margin liquidation are excluded.

The full-period diagnostic starts trading after a common 360-hour warmup.
Legacy reports use different timing and approximate return aggregation, and
remain explicitly labeled as legacy. Their change relative to this audit
cannot be attributed to rebalance costs alone.

## Chronological folds

Three fixed test quarters start 2025-10-01, 2026-01-01 and 2026-04-01. Each has
three months of preceding history and begins flat with capital one. Baseline
rolling statistics update only from available history; no future test prices
select parameters. Returns are reported per fold, not summed as a portfolio.

For Engle–Granger and guarded Mean Reversion, screen all 45 pairs independently
on each training window, with Holm correction. Freeze the price-level OLS
coefficients throughout the next quarter. The existing next-open, fixed-quantity
engines handle these strategies: price-level beta is a quantity ratio, unlike
the dollar beta used in the log-regression baselines. Each selected pair receives
an equal segregated capital share; no selected pairs means cash. Guarded Mean
Reversion retains its ADF, loss, time and cooldown controls without tuning.

The historical year and asset universe were already inspected in prior work.
These are chronological out-of-training evaluations, **not a new untouched
holdout**. Current-asset selection can also cause survivorship bias. Multiple
folds, overlapping assets and repeated TP variants are not independent evidence.

## Expanded pivot sample and open positions

Weekly Pivot, HVN Limit and HVN Reclaim are rerun on all ten assets at 15min,
with the existing 10/15/20% TP variants, 25% stop and 60-day maximum holding.
This extends the universe from the three previously available crypto assets;
it does not extend the historical period or choose a winning TP after testing.

Two different outputs are reported explicitly:

1. Trade means, including last-close marks for open trades and the original
   modeled round-trip costs. The closed-only number is retained for comparison.
2. A capital-constrained long portfolio: each symbol starts with 1/10 of capital,
   reinvests within its own cash sleeve, and holds at most one position at once.
   Overlapping entries are skipped (including another entry on the exit bar).
   Each position sizes after entry costs; actual buy and sell notionals pay costs.
   Idle cash stays idle. Every bar is marked, and remaining inventory is closed
   at the boundary. Portfolio drawdown includes unrealized P&L.

Portfolio replay inherits existing OHLC fill/stop assumptions; it is not an
order-book simulation and does not resolve intrabar paths or validate gap-stop
fills. U.S. equity portfolio allocation is not simulated by this runner. Existing
sector reports across both markets now include all-filled-trade statistics,
so open losses no longer disappear from their supplementary summary tables.
A few extra signals are not enough to establish a robust edge.
