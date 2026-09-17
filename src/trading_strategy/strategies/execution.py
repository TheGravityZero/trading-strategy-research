"""Cash/quantity accounting for next-open pair execution and cost attribution."""
from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_account(bars, signals, beta, start, *, fee_bps=5., slippage_bps=2.):
    """Rebalance to previous-close dollar weights at open, at 1x gross exposure.

    beta is the log-regression dollar hedge ratio, not a price-level quantity
    ratio. Gross equity adds paid costs back to the SAME executed quantities;
    it is a P&L attribution, not a separately compounded cost-free strategy.
    Remaining inventory is marked each close and liquidated at final close.
    """
    if not np.isfinite([fee_bps, slippage_bps]).all() or min(fee_bps, slippage_bps) < 0:
        raise ValueError('costs must be finite and nonnegative')
    if not isinstance(bars.index, pd.DatetimeIndex) or not bars.index.is_unique or not bars.index.is_monotonic_increasing:
        raise ValueError('require sorted unique DatetimeIndex')
    if len(bars) > 2 and bars.index.to_series().diff().dropna().nunique() != 1:
        raise ValueError('require regular bars without gaps')
    prices = bars[['y_open', 'x_open', 'y_close', 'x_close']]
    if not np.isfinite(prices).all().all() or not (prices > 0).all().all():
        raise ValueError('require positive finite prices')
    if not signals.index.equals(bars.index) or not beta.index.equals(bars.index):
        raise ValueError('signals and beta must have exactly the bar index')
    if not signals.isin([-1, 0, 1]).all():
        raise ValueError('signals must be -1, 0 or 1')
    decision = signals.shift().fillna(0)
    hedge = beta.shift()
    test = prices.loc[prices.index >= start]
    if test.empty:
        raise ValueError('empty test period')
    cash, qy, qx, previous_equity = 1., 0., 0., 1.
    cumulative_cost, state = 0., 0
    rows = []
    for number, (timestamp, row) in enumerate(test.iterrows()):
        equity_open = cash + qy * row.y_open + qx * row.x_open
        if equity_open <= 0:
            raise ValueError('capital exhausted at open; liquidation is not modeled')
        desired, b = int(decision.loc[timestamp]), hedge.loc[timestamp]
        if not np.isfinite(b):
            desired = 0
        if number == len(test) - 1 and state == 0:
            desired = 0
        if desired:
            weight_y = desired / (1 + abs(b))
            weight_x = -desired * b / (1 + abs(b))
            target_y = equity_open * weight_y / row.y_open
            target_x = equity_open * weight_x / row.x_open
        else:
            target_y = target_x = 0.
        turnover = abs((target_y - qy) * row.y_open) + abs((target_x - qx) * row.x_open)
        fees, slippage = turnover * fee_bps / 10000, turnover * slippage_bps / 10000
        cash -= (target_y - qy) * row.y_open + (target_x - qx) * row.x_open + fees + slippage
        entry = int(desired != 0 and desired != state)
        rebalance = turnover if desired != 0 and desired == state else 0.
        qy, qx, state = target_y, target_x, desired
        inventory_value = qy * row.y_close + qx * row.x_close
        if number == len(test) - 1:
            terminal = abs(qy * row.y_close) + abs(qx * row.x_close)
            cash += inventory_value - terminal * (fee_bps + slippage_bps) / 10000
            fees += terminal * fee_bps / 10000
            slippage += terminal * slippage_bps / 10000
            turnover += terminal
            qy, qx, state = 0., 0., 0
            inventory_value = 0.
        equity = cash + inventory_value
        if equity <= 0:
            raise ValueError('capital exhausted at close; liquidation is not modeled')
        costs = fees + slippage
        cumulative_cost += costs
        gross_pnl = equity - previous_equity + costs
        rows.append(dict(timestamp=timestamp, position=state, entries=entry,
                         qy=qy, qx=qx, cash=cash, inventory_value=inventory_value,
                         turnover=turnover, rebalance_turnover=rebalance,
                         fees=fees, slippage=slippage, gross_pnl=gross_pnl,
                         net_pnl=equity - previous_equity, equity=equity,
                         gross_equity=equity + cumulative_cost,
                         strategy_return=equity / previous_equity - 1))
        previous_equity = equity
    result = pd.DataFrame(rows).set_index('timestamp')
    result['drawdown'] = result.equity / result.equity.cummax().clip(lower=1.) - 1
    return result


def account_summary(result):
    return dict(trades=int(result.entries.sum()), net_return=float(result.equity.iloc[-1] - 1),
                gross_return=float(result.gross_pnl.sum()), fees=float(result.fees.sum()),
                slippage=float(result.slippage.sum()),
                maximum_drawdown=float(result.drawdown.min()),
                turnover=float(result.turnover.sum()),
                rebalance_turnover=float(result.rebalance_turnover.sum()))


def simulate_long_portfolio(frames, trades, *, fee_bps=5., slippage_bps=2.):
    """Replay existing long fills in equal symbol cash sleeves, no leverage.

    Each symbol gets 1/N initial capital; simultaneous signals for an occupied
    symbol are skipped. OHLC entry/exit assumptions belong to the signal engine.
    Open inventory is marked every bar and liquidated at final close.
    """
    rate = (fee_bps + slippage_bps) / 10000
    if not np.isfinite([fee_bps, slippage_bps]).all() or min(fee_bps, slippage_bps) < 0:
        raise ValueError('invalid costs')
    if not frames:
        raise ValueError('no frames')
    index = next(iter(frames.values())).index
    if not isinstance(index, pd.DatetimeIndex) or not len(index) or not index.is_unique or not index.is_monotonic_increasing:
        raise ValueError('require a sorted unique nonempty DatetimeIndex')
    if rate >= 1:
        raise ValueError('cost rate must be less than 100%')
    if any(not frame.index.equals(index) for frame in frames.values()):
        raise ValueError('portfolio frames must have the same time grid')
    if any(not np.isfinite(frame.close).all() or not (frame.close > 0).all() for frame in frames.values()):
        raise ValueError('require positive finite close prices')
    equity = pd.Series(0., index=index)
    costs = pd.Series(0., index=index)
    accepted, skipped = 0, 0
    filled = trades.loc[trades.order_filled.eq(True)].copy() if 'order_filled' in trades else pd.DataFrame()
    if len(filled) and not set(filled.symbol).issubset(frames):
        raise ValueError('trade symbol has no price frame')
    for symbol, frame in frames.items():
        cash = 1 / len(frames)
        sleeve = pd.Series(cash, index=index)
        available = -1
        selected = filled.loc[filled.symbol == symbol].sort_values('entry_timestamp', kind='stable') if len(filled) else filled
        for trade in selected.itertuples():
            if trade.side != 'long':
                raise ValueError('long portfolio only')
            entry_time, exit_time = pd.to_datetime(trade.entry_timestamp, utc=True), pd.to_datetime(trade.exit_timestamp, utc=True)
            begin, finish = index.get_indexer([entry_time, exit_time])
            if min(begin, finish) < 0 or finish < begin:
                raise ValueError('invalid trade timestamps')
            if trade.exit_reason == 'open' and (finish != len(index) - 1 or not np.isclose(trade.exit_price, frame.close.iloc[-1])):
                raise ValueError('open trades must be marked at the final close')
            if begin <= available:
                skipped += 1
                continue
            entry, exit_ = float(trade.entry_price), float(trade.exit_price)
            if not np.isfinite([entry, exit_]).all() or min(entry, exit_) <= 0:
                raise ValueError('invalid fills')
            quantity = cash / (entry * (1 + rate))
            entry_cost = quantity * entry * rate
            exit_cost = quantity * exit_ * rate
            costs.iloc[begin] += entry_cost
            costs.iloc[finish] += exit_cost
            sleeve.iloc[begin:finish] = quantity * frame.close.iloc[begin:finish]
            cash = quantity * exit_ - exit_cost
            sleeve.iloc[finish:] = cash
            accepted += 1
            available = finish
        equity += sleeve
    result = pd.DataFrame({'equity': equity, 'costs': costs})
    result['gross_equity'] = equity + costs.cumsum()
    result['drawdown'] = equity / equity.cummax().clip(lower=1) - 1
    return result, dict(accepted=accepted, skipped_overlap=skipped,
                        net_return=float(equity.iloc[-1] - 1),
                        gross_return=float(result.gross_equity.iloc[-1] - 1),
                        costs=float(costs.sum()), maximum_drawdown=float(result.drawdown.min()))
