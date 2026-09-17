"""Causal spread mean reversion with a rolling stationarity risk gate."""
from dataclasses import dataclass
import warnings

import numpy as np
import pandas as pd

from .cointegration import CointegrationConfig, select_pairs


@dataclass(frozen=True)
class MeanReversionConfig(CointegrationConfig):
    regime_window: int = 240
    regime_every: int = 24
    regime_alpha: float = 0.05
    max_holding_bars: int = 120
    stop_loss: float = 0.05
    cooldown_bars: int = 24

    def validate(self):
        super().validate()
        for name in ('window', 'min_train_bars', 'regime_window', 'regime_every',
                     'max_holding_bars', 'cooldown_bars'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f'{name} must be a positive integer')
        if self.regime_window < 20 or self.min_train_bars < self.regime_window:
            raise ValueError('require min_train_bars >= regime_window >= 20')
        if not 0 < self.regime_alpha < 1 or not 0 < self.stop_loss < 1:
            raise ValueError('invalid regime_alpha or stop_loss')


def build_features(bars, intercept, beta, config):
    """At close t, normalize using closes strictly before t; ADF includes t."""
    from statsmodels.tsa.stattools import adfuller

    spread = bars.y_close - intercept - beta * bars.x_close
    history = spread.shift().rolling(config.window)
    z = (spread - history.mean()) / history.std().replace(0, np.nan)
    pvalues = pd.Series(np.nan, index=bars.index)
    for i in range(config.regime_window - 1, len(bars), config.regime_every):
        sample = spread.iloc[i - config.regime_window + 1:i + 1]
        pvalue = 1.0
        if sample.std() > 1e-12:
            with warnings.catch_warnings(record=True) as caught:
                try:
                    candidate = adfuller(sample, maxlag=1, autolag=None)[1]
                    if not caught and np.isfinite(candidate):
                        pvalue = float(candidate)
                except ValueError:
                    pass
        pvalues.iloc[i] = pvalue
    return pd.DataFrame({'spread': spread, 'zscore': z,
                         'regime_pvalue': pvalues.ffill()}, index=bars.index)


def backtest_mean_reversion(bars, split, intercept, beta, config=MeanReversionConfig()):
    """Fixed quantities, next-open fills, actual-notional costs, last-close exit.

    OLS coefficients must be fitted exclusively before split (see select_pairs).
    ADF is a heuristic risk gate, not a guarantee of future stationarity.
    """
    config.validate()
    if not np.isfinite([intercept, beta]).all() or beta <= 0:
        raise ValueError('require finite intercept and positive beta')
    if not isinstance(bars.index, pd.DatetimeIndex) or not bars.index.is_unique or not bars.index.is_monotonic_increasing:
        raise ValueError('require sorted unique DatetimeIndex')
    if len(bars) > 2 and bars.index.to_series().diff().dropna().nunique() != 1:
        raise ValueError('require regular bars without gaps')
    prices = bars[['y_open', 'x_open', 'y_close', 'x_close']]
    if not np.isfinite(prices).all().all() or not (prices > 0).all().all():
        raise ValueError('require finite positive prices; do not forward fill')
    test = bars.loc[bars.index >= split]
    if test.empty or (bars.index < split).sum() < config.min_train_bars:
        raise ValueError('insufficient train/test history')
    features = build_features(bars, intercept, beta, config)
    signals = features.shift()
    cash, qy, qx, state = 1.0, 0.0, 0.0, 0
    entry_equity, entry_number, blocked_until = 1.0, 0, -1
    previous_equity = 1.0
    rows, trades = [], []
    active = None
    rate = (config.fee_bps + config.slippage_bps) / 10000
    for number, (timestamp, row) in enumerate(test.iterrows()):
        signal = signals.loc[timestamp]
        z = signal.zscore
        eligible = np.isfinite(signal.regime_pvalue) and signal.regime_pvalue < config.regime_alpha
        event, reason, turnover, cost = '', '', 0.0, 0.0
        if state:
            if not np.isfinite(z) or not eligible:
                reason = 'regime_break'
            elif abs(z) >= config.stop:
                reason = 'z_stop'
            elif previous_equity <= entry_equity * (1 - config.stop_loss):
                reason = 'loss_stop'
            elif number - entry_number >= config.max_holding_bars:
                reason = 'time_stop'
            elif state * z >= 0:
                reason = 'mean_crossing'
            if reason:
                turnover = abs(qy * row.y_open) + abs(qx * row.x_open)
                cost = turnover * rate
                cash += qy * row.y_open + qx * row.x_open - cost
                trades.append({**active, 'exit_time': timestamp, 'exit_reason': reason,
                               'holding_bars': number - entry_number,
                               'net_return': cash / entry_equity - 1})
                qy, qx, state, event = 0.0, 0.0, 0, 'exit'
                if reason != 'mean_crossing':
                    blocked_until = number + config.cooldown_bars
        elif number >= blocked_until and number < len(test) - 1 and eligible and np.isfinite(z) and config.entry <= abs(z) < config.stop:
            state = -1 if z > 0 else 1
            entry_equity, entry_number = cash, number
            qy = state * cash / (row.y_open + beta * row.x_open)
            qx = -beta * qy
            turnover = abs(qy * row.y_open) + abs(qx * row.x_open)
            cost = turnover * rate
            cash -= qy * row.y_open + qx * row.x_open + cost
            event = 'entry'
            active = dict(entry_time=timestamp, direction=state, entry_zscore=z)
        if number == len(test) - 1 and state:
            terminal = abs(qy * row.y_close) + abs(qx * row.x_close)
            cash += qy * row.y_close + qx * row.x_close - terminal * rate
            turnover += terminal
            cost += terminal * rate
            reason, event = 'end_of_data', 'exit'
            trades.append({**active, 'exit_time': timestamp, 'exit_reason': reason,
                           'holding_bars': number - entry_number,
                           'net_return': cash / entry_equity - 1})
            qy, qx, state = 0.0, 0.0, 0
        equity = cash + qy * row.y_close + qx * row.x_close
        if equity <= 0:
            raise ValueError('capital exhausted; margin liquidation is not modeled')
        rows.append(dict(timestamp=timestamp, **features.loc[timestamp].to_dict(),
                         signal_zscore=z, signal_regime_pvalue=signal.regime_pvalue,
                         position=state, event=event, exit_reason=reason,
                         turnover=turnover, cost=cost, equity=equity))
        previous_equity = equity
    result = pd.DataFrame(rows).set_index('timestamp')
    result['strategy_return'] = result.equity / result.equity.shift().fillna(1) - 1
    result['drawdown'] = result.equity / result.equity.cummax().clip(lower=1) - 1
    ledger = pd.DataFrame(trades, columns=['entry_time', 'direction', 'entry_zscore',
                                         'exit_time', 'exit_reason', 'holding_bars', 'net_return'])
    return result, ledger
