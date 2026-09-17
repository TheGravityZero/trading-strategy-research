# Crypto and U.S. Equity Correlations

Separate correlation studies for `BTCUSDT`, `ETHUSDT`, and `HYPEUSDT` against
`SPY`, `QQQ`, `NVDA`, `TSLA`, `COIN`, and `MSTR`.

## Experiment setup

- Period: `2026-07-27` through `2026-08-25`; requested end `2026-08-26` is exclusive.
- Source: Binance USD-M futures minute archives and Yahoo Finance hourly charts.
- Sample: 126 synchronized hourly intraday returns over 21 U.S. sessions.
- Prices are converted to logarithmic returns.
- Crypto minute data is aggregated to the exact boundaries of U.S. hourly bars.
- The first U.S. bar of each day is excluded because its stock return contains
  an overnight gap and is not comparable with a one-hour crypto return.
- Lag shifts are restricted to the same trading day.

## Separate reports

- [Hourly Pearson](pearson/README.md)
- [Hourly Spearman](spearman/README.md)
- [Rolling Pearson over 5 trading days](rolling-pearson-5d/README.md)
- [Lag correlation from −2 to +2 hours](lag-correlation/README.md)
- [Downside correlation](downside-correlation/README.md)
- [Absolute-return correlation](absolute-return-correlation/README.md)

Downside correlation is conditioned separately on a negative hourly return of
the corresponding U.S. stock. Absolute-return correlation measures whether
volatility intensity moves together, regardless of direction.

## Run

```bash
PYTHONPATH=src .venv/bin/python research/runners/run_cross_asset_correlations.py \
  --end 2026-08-26 --days 30
```

CSV matrices and time series are generated beside the reports and ignored by
Git. The committed Markdown files contain the reproducible setup and summaries.
