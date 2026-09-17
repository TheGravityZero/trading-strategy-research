# Engle–Granger pair strategy

[Results](RESULTS.md)

Separate strategy using repository Binance archives, with fixed train OLS on
price levels (`Y = intercept + beta * X`) and Holm-adjusted Engle–Granger
p-values below 0.05. Positive beta only. Symbol sorting fixes test direction.
The test assumes I(1) input prices; it does not prove future mean reversion.
See [statsmodels coint](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html).

```bash
uv pip install --python .venv/bin/python -e '.[research]'
PYTHONPATH=src .venv/bin/python research/runners/run_cointegration.py \
  --symbols ADAUSDT AVAXUSDT BNBUSDT BTCUSDT DOGEUSDT ETHUSDT LINKUSDT LTCUSDT SOLUSDT XRPUSDT \
  --start 2025-07-01 --split 2026-01-01 --end 2026-07-01 --interval 4h \
  --output-dir research/reports/cointegration/all-crypto
```

Download the required archives first using the repository download CLI. This
runner uses explicitly supplied symbols, not a historically reconstructed top-50
universe. Choose the universe before viewing test results. No window optimization
is performed: the default 120-bar window is fixed in advance. Any tuning requires
an inner chronological train/validation split, leaving test untouched.

Signals use a spread z-score against the preceding rolling window. Entry at
2 <= |z| < 3.5; exit at zero crossing or |z| >= 3.5. Orders execute at the next
open. Both legs keep fixed quantities with initial gross exposure of 100% of
pair equity. Fees default to 10 bps (0.1%) plus 2 bps slippage on each leg's
actual traded notional, on entry and exit. Slippage is modeled as a cash cost.
Terminal positions liquidate at the last close with costs. Equity includes
unrealized P&L until liquidation. Outputs: selection.csv (all hypotheses), pair
bar CSVs, metadata.json (configuration and test summaries). No selection is a
valid outcome, not a reason to relax thresholds after seeing test data.

The crypto runner shares the complete-bar loader with Mean Reversion: it
rejects missing source bars before aggregation and conflicting overlapping
archives, rather than filling prices. Dates must align to interval boundaries
and the training range must cover at least 240 bars. The Python API accepts aligned equity open/close data on a trading-session
grid as well. Equity corporate-action adjustments must be consistent.

Results are independent pair accounts, not an aggregated portfolio. Funding,
borrow costs, short availability, margin calls and liquidity constraints are not
modeled. Spot shorts require a separate borrowing/execution arrangement. There
is no measured profitability or claim that fees consume 40% of profits here;
that requires a real data experiment. Current-universe selection can introduce
survivorship bias. Gaps beyond the z-stop can cause larger losses.
