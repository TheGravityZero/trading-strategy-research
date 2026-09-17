"""Train-only Engle–Granger selection and next-open, fixed-quantity pair trading."""
from dataclasses import dataclass
from itertools import combinations
import warnings

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CointegrationConfig:
    window: int = 120
    entry: float = 2.0
    stop: float = 3.5
    fee_bps: float = 10.0
    slippage_bps: float = 2.0
    alpha: float = 0.05
    min_train_bars: int = 240

    def validate(self):
        if self.window < 3 or self.min_train_bars < self.window:
            raise ValueError('require min_train_bars >= window >= 3')
        if not 0 < self.entry < self.stop or not 0 < self.alpha < 1:
            raise ValueError('invalid thresholds')
        if not np.isfinite([self.entry, self.stop, self.fee_bps, self.slippage_bps]).all() or min(self.fee_bps, self.slippage_bps) < 0:
            raise ValueError('invalid costs or thresholds')


def select_pairs(closes, split, config=CointegrationConfig()):
    """OLS on price levels; Holm correction across all candidate pairs.

    Symbols are sorted to fix the asymmetric EG test direction in advance.
    Missing train history excludes a pair; test data never affects selection.
    """
    from statsmodels.tsa.stattools import coint
    from statsmodels.stats.multitest import multipletests
    config.validate()
    train = closes.loc[closes.index < split]
    if not train.index.is_monotonic_increasing or not train.index.is_unique:
        raise ValueError('timestamps must be sorted and unique')
    rows = []
    for y, x in combinations(sorted(closes.columns), 2):
        pair = train[[y, x]]
        p, intercept, beta = 1.0, np.nan, np.nan
        if len(pair) >= config.min_train_bars and np.isfinite(pair).all().all() and (pair > 0).all().all() and (pair.std() > 0).all():
            intercept, beta = np.linalg.lstsq(np.column_stack([np.ones(len(pair)), pair[x]]), pair[y], rcond=None)[0]
            with warnings.catch_warnings(record=True) as caught:
                statistic, candidate_p, _ = coint(pair[y], pair[x], trend='c', autolag='aic')
            if not caught and np.isfinite(statistic) and np.isfinite(candidate_p):
                p = float(candidate_p)
        rows.append(dict(y=y, x=x, pvalue=p, intercept=intercept, beta=beta))
    result = pd.DataFrame(rows, columns=['y', 'x', 'pvalue', 'intercept', 'beta'])
    result['adjusted_pvalue'] = multipletests(result.pvalue, method='holm')[1] if len(result) else pd.Series(dtype=float)
    result['selected'] = (result.adjusted_pvalue < config.alpha) & (result.beta > 0)
    return result


def backtest_pair(bars, split, intercept, beta, config=CointegrationConfig()):
    """bars has y_open, x_open, y_close, x_close on a regular time grid.

    Signals use previous close, fills use current open. Quantities remain fixed
    until exit; cash and marked positions produce simple equity, including costs
    on actual traded notional. Final liquidation is at the last close.
    """
    config.validate()
    if not np.isfinite([intercept, beta]).all() or beta <= 0:
        raise ValueError('require finite intercept and positive beta')
    if not bars.index.is_unique or not bars.index.is_monotonic_increasing:
        raise ValueError('timestamps must be sorted and unique')
    prices = bars[['y_open', 'x_open', 'y_close', 'x_close']]
    if not np.isfinite(prices).all().all() or not (prices > 0).all().all():
        raise ValueError('missing or invalid pair prices; do not forward fill')
    spread = bars.y_close - intercept - beta * bars.x_close
    history = spread.shift(1).rolling(config.window)
    z = (spread - history.mean()) / history.std().replace(0, np.nan)
    signals = z.shift(1)
    test = bars.loc[bars.index >= split]
    if test.empty or (bars.index < split).sum() < config.window:
        raise ValueError('insufficient train/test history')
    cash, qy, qx, state = 1.0, 0.0, 0.0, 0
    rows = []
    rate = (config.fee_bps + config.slippage_bps) / 10000
    for number, (timestamp, row) in enumerate(test.iterrows()):
        signal = signals.loc[timestamp]
        cost, turnover, event = 0.0, 0.0, ''
        exit_now = state and (not np.isfinite(signal) or state * signal >= 0 or abs(signal) >= config.stop)
        if exit_now:
            turnover = abs(qy * row.y_open) + abs(qx * row.x_open)
            cost = turnover * rate
            cash += qy * row.y_open + qx * row.x_open - cost
            qy, qx, state, event = 0.0, 0.0, 0, 'exit'
        elif not state and number < len(test) - 1 and np.isfinite(signal) and config.entry <= abs(signal) < config.stop and cash > 0:
            state = -1 if signal > 0 else 1
            qy = state * cash / (row.y_open + beta * row.x_open)
            qx = -beta * qy
            turnover = abs(qy * row.y_open) + abs(qx * row.x_open)
            cost = turnover * rate
            cash -= qy * row.y_open + qx * row.x_open + cost
            event = 'entry'
        if number == len(test) - 1 and state:
            terminal = abs(qy * row.y_close) + abs(qx * row.x_close)
            terminal_cost = terminal * rate
            cash += qy * row.y_close + qx * row.x_close - terminal_cost
            turnover += terminal
            cost += terminal_cost
            qy, qx, state, event = 0.0, 0.0, 0, 'terminal_exit'
        equity = cash + qy * row.y_close + qx * row.x_close
        if equity <= 0:
            raise ValueError('pair capital exhausted; leveraged liquidation is not modeled')
        rows.append(dict(timestamp=timestamp, zscore=z.loc[timestamp], signal_zscore=signal,
                         position=state, event=event, turnover=turnover, cost=cost, equity=equity))
    result = pd.DataFrame(rows).set_index('timestamp')
    result['strategy_return'] = result.equity / result.equity.shift(1).fillna(1.0) - 1
    result['drawdown'] = result.equity / result.equity.cummax().clip(lower=1) - 1
    return result
