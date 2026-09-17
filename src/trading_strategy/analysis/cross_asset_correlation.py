"""Independent correlation estimators for synchronized cross-asset returns."""

from __future__ import annotations

import pandas as pd


def _cross_block(
    matrix: pd.DataFrame, crypto_symbols: list[str], stock_symbols: list[str]
) -> pd.DataFrame:
    return matrix.loc[crypto_symbols, stock_symbols]


def pearson_correlation(
    returns: pd.DataFrame, crypto_symbols: list[str], stock_symbols: list[str]
) -> pd.DataFrame:
    return _cross_block(returns.corr(method="pearson"), crypto_symbols, stock_symbols)


def spearman_correlation(
    returns: pd.DataFrame, crypto_symbols: list[str], stock_symbols: list[str]
) -> pd.DataFrame:
    return _cross_block(returns.corr(method="spearman"), crypto_symbols, stock_symbols)


def absolute_return_correlation(
    returns: pd.DataFrame, crypto_symbols: list[str], stock_symbols: list[str]
) -> pd.DataFrame:
    return _cross_block(returns.abs().corr(method="pearson"), crypto_symbols, stock_symbols)


def downside_correlation(
    returns: pd.DataFrame, crypto_symbols: list[str], stock_symbols: list[str]
) -> pd.DataFrame:
    """Pearson correlation conditional on each stock's negative return."""
    result = pd.DataFrame(index=crypto_symbols, columns=stock_symbols, dtype=float)
    for stock in stock_symbols:
        downside = returns.loc[returns[stock] < 0]
        for crypto in crypto_symbols:
            result.loc[crypto, stock] = downside[crypto].corr(downside[stock])
    return result


def rolling_pearson(
    returns: pd.DataFrame,
    crypto_symbols: list[str],
    stock_symbols: list[str],
    window: int,
) -> pd.DataFrame:
    """Return a tidy time series for every crypto/stock pair."""
    records = []
    for crypto in crypto_symbols:
        for stock in stock_symbols:
            values = returns[crypto].rolling(window).corr(returns[stock])
            records.append(
                pd.DataFrame(
                    {
                        "timestamp": returns.index,
                        "crypto": crypto,
                        "stock": stock,
                        "correlation": values.to_numpy(),
                    }
                )
            )
    return pd.concat(records, ignore_index=True).dropna(subset=["correlation"])


def lag_correlation(
    returns: pd.DataFrame,
    trading_dates: pd.Series,
    crypto_symbols: list[str],
    stock_symbols: list[str],
    lags: range,
) -> pd.DataFrame:
    """Correlate crypto[t] with stock[t+lag] without crossing session days.

    A positive lag means crypto leads the stock; a negative lag means the stock
    leads crypto. Rows are shifted only within the same U.S. trading date.
    """
    records = []
    dates = pd.Series(trading_dates.to_numpy(), index=returns.index)
    for lag in lags:
        for crypto in crypto_symbols:
            for stock in stock_symbols:
                future_stock = returns[stock].groupby(dates).shift(-lag)
                paired = pd.concat([returns[crypto], future_stock], axis=1).dropna()
                records.append(
                    {
                        "lag_hours": lag,
                        "crypto": crypto,
                        "stock": stock,
                        "correlation": paired.iloc[:, 0].corr(paired.iloc[:, 1]),
                        "observations": len(paired),
                    }
                )
    return pd.DataFrame(records)
