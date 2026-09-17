#!/usr/bin/env python3
"""Offline execution audit, quarterly chronological tests and sample expansion."""
from dataclasses import asdict
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_mean_reversion import load_complete_bars
from trading_strategy.strategies.execution import simulate_account, account_summary, simulate_long_portfolio
from trading_strategy.strategies.stat_arb import StatArbConfig, build_pair_features
from trading_strategy.strategies.regression_spread import RegressionSpreadConfig, build_regression_features
from trading_strategy.strategies.correlation_divergence import CorrelationDivergenceConfig, build_correlation_features
from trading_strategy.strategies.pair_reversion import position_from_zscore
from trading_strategy.strategies.cointegration import CointegrationConfig, select_pairs, backtest_pair
from trading_strategy.strategies.mean_reversion import MeanReversionConfig, backtest_mean_reversion
from trading_strategy.strategies.weekly_pivot_limit import WeeklyPivotConfig, backtest_weekly_pivot
from trading_strategy.strategies.defended_pivot_long import DefendedPivotConfig, backtest_defended_pivot


SYMBOLS = ['ADAUSDT', 'AVAXUSDT', 'BNBUSDT', 'BTCUSDT', 'DOGEUSDT', 'ETHUSDT', 'LINKUSDT', 'LTCUSDT', 'SOLUSDT', 'XRPUSDT']
BASELINES = [('correlation-divergence', CorrelationDivergenceConfig(), build_correlation_features),
             ('regression-spread', RegressionSpreadConfig(), build_regression_features),
             ('crypto-stat-arb', StatArbConfig(), build_pair_features)]


def trade_statistics(trades):
    filled = trades.loc[trades.order_filled.eq(True)] if 'order_filled' in trades else pd.DataFrame()
    if filled.empty:
        return dict(fills=0, closed=0, open=0, closed_mean=None, all_marked_mean=None, gross_mean=None, costs_mean=None)
    closed = filled.loc[filled.exit_reason != 'open']
    return dict(fills=len(filled), closed=len(closed), open=int((filled.exit_reason == 'open').sum()),
                closed_mean=float(closed.net_return.mean()) if len(closed) else None,
                all_marked_mean=float(filled.net_return.mean()), gross_mean=float(filled.gross_return.mean()),
                costs_mean=float((filled.gross_return - filled.net_return).mean()))


def baseline_run(frames, train_start, start, end, definition, cost_multiplier=1.):
    slug, config, builder = definition
    legs = {s: f.loc[(f.index >= train_start) & (f.index < end)] for s, f in frames.items() if s in ('ETHUSDT', 'BTCUSDT')}
    features = builder(legs['ETHUSDT'].rename_axis('timestamp').reset_index(), legs['BTCUSDT'].rename_axis('timestamp').reset_index(), config).set_index('timestamp')
    prices = pd.DataFrame({f'{leg}_{field}': legs[symbol][field] for leg, symbol in [('y', 'ETHUSDT'), ('x', 'BTCUSDT')] for field in ('open', 'close')})
    eligible = features.correlation.abs() >= config.minimum_correlation if hasattr(config, 'minimum_correlation') else pd.Series(True, index=features.index)
    # Reset trade state at each fold; last train close can place the first test order.
    decisions = features.index >= features.index[features.index < start][-1]
    signals = pd.Series(0, index=features.index, dtype='int8')
    signals.loc[decisions] = position_from_zscore(features.loc[decisions, 'zscore'], entry=config.entry_zscore,
                                               exit_=config.exit_zscore, stop=config.stop_zscore,
                                               eligible=eligible.loc[decisions])
    return simulate_account(prices, signals, features.beta, start,
                            fee_bps=config.fee_bps_per_side * cost_multiplier,
                            slippage_bps=config.slippage_bps_per_side * cost_multiplier)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path('data/raw'))
    parser.add_argument('--output-dir', type=Path, default=Path('research/reports/execution-audit/latest'))
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    start, end = pd.Timestamp('2025-07-01', tz='UTC'), pd.Timestamp('2026-07-01', tz='UTC')
    frames = {}
    for symbol in SYMBOLS:
        frames[symbol] = load_complete_bars(args.data_dir, symbol, start, end, '15min', include_ohlcv=True)
        print(f'Validated {symbol}: {len(frames[symbol])} bars', flush=True)
    hourly = {s: f.resample('1h').agg(open=('open', 'first'), close=('close', 'last')) for s, f in frames.items()}
    daily4 = {s: f.resample('4h').agg(open=('open', 'first'), close=('close', 'last')) for s, f in frames.items()}
    boundaries = pd.date_range('2025-10-01', '2026-07-01', freq='QS', tz='UTC')
    pairs, walk, selections = [], [], []
    for definition in BASELINES:
        slug = definition[0]
        # A common 360-hour feature warmup; historical diagnostic, not new holdout.
        for multiplier in (0., 1., 2.):
            result = baseline_run(hourly, start, start + pd.Timedelta(hours=360), end, definition, multiplier)
            result.to_csv(out / f'{slug}_cost{multiplier:g}.csv')
            pairs.append(dict(strategy=slug, cost_multiplier=multiplier, **account_summary(result)))
        for left, right in zip(boundaries[:-1], boundaries[1:]):
            train_start = left - pd.DateOffset(months=3)
            result = baseline_run(hourly, train_start, left, right, definition)
            result.to_csv(out / f'{slug}_{left.date()}.csv')
            walk.append(dict(strategy=slug, train_start=str(train_start), test_start=str(left), test_end=str(right), **account_summary(result)))
        print(f'Pair accounting and folds: {slug}', flush=True)
    for left, right in zip(boundaries[:-1], boundaries[1:]):
        train_start = left - pd.DateOffset(months=3)
        subset = {s: f.loc[(f.index >= train_start) & (f.index < right)] for s, f in daily4.items()}
        selection = select_pairs(pd.DataFrame({s: f.close for s, f in subset.items()}), left)
        selection.to_csv(out / f'selection_{left.date()}.csv', index=False)
        for slug in ('cointegration', 'mean-reversion'):
            accounts, gross_accounts, count = [], [], 0
            for pair in selection.loc[selection.selected].itertuples():
                bars = pd.DataFrame({f'{leg}_{field}': subset[symbol][field] for leg, symbol in [('y', pair.y), ('x', pair.x)] for field in ('open', 'close')})
                if slug == 'cointegration':
                    result = backtest_pair(bars, left, pair.intercept, pair.beta)
                else:
                    result, _ = backtest_mean_reversion(bars, left, pair.intercept, pair.beta)
                result.to_csv(out / f'{slug}_{pair.y}_{pair.x}_{left.date()}.csv')
                accounts.append(result.equity)
                gross_accounts.append(result.equity + result.cost.cumsum())
                count += int((result.event == 'entry').sum())
            equity = pd.concat(accounts, axis=1).mean(axis=1) if accounts else pd.Series(1., index=next(iter(subset.values())).loc[left:].index)
            gross = pd.concat(gross_accounts, axis=1).mean(axis=1) if accounts else equity
            selections.append(dict(strategy=slug, train_start=str(train_start), test_start=str(left), test_end=str(right),
                                   candidates=len(selection), selected=int(selection.selected.sum()), trades=count,
                                   selected_pairs=selection.loc[selection.selected, ['y', 'x', 'adjusted_pvalue']].to_dict('records'),
                                   net_return=float(equity.iloc[-1] - 1), gross_return=float(gross.iloc[-1] - 1),
                                   maximum_drawdown=float((equity / equity.cummax().clip(lower=1) - 1).min())))
        print(f'Train-only pair selection: {left.date()}', flush=True)
    existing = []
    for path in sorted(Path('research/reports').glob('*/*/tp*-hold60d/trades.csv')):
        try:
            trades = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            trades = pd.DataFrame()
        existing.append(dict(strategy=path.parts[2], sector=path.parts[3], configuration=path.parts[4], **trade_statistics(trades)))
    expanded = []
    for slug, mode in [('weekly-pivot-limit', None), ('defended-pivot-hvn-limit', 'hvn_limit_center'), ('defended-pivot-hvn-reclaim', 'hvn_reclaim_low')]:
        for tp in (10., 15., 20.):
            config = (WeeklyPivotConfig(take_profit_percent=tp, long_only=True, maximum_holding_days=60, fee_bps_per_side=5., slippage_bps_per_side=2., market_timezone='UTC') if mode is None else
                      DefendedPivotConfig(take_profit_percent=tp, entry_mode=mode, fee_bps_per_side=5., slippage_bps_per_side=2., market_timezone='UTC'))
            trades = []
            for symbol, f in frames.items():
                frame = f.rename_axis('timestamp').reset_index().assign(symbol=symbol)
                trades.append(backtest_weekly_pivot(frame, config) if mode is None else backtest_defended_pivot(frame, config))
            trades = pd.concat(trades, ignore_index=True)
            trades.to_csv(out / f'{slug}_tp{tp:g}_trades.csv', index=False)
            portfolio, summary = simulate_long_portfolio(frames, trades)
            portfolio.to_csv(out / f'{slug}_tp{tp:g}_portfolio.csv')
            expanded.append(dict(strategy=slug, tp=tp, config=asdict(config), **trade_statistics(trades), portfolio=summary))
            print(f'Expanded sample: {slug} TP {tp:g}: {len(trades)} setups', flush=True)
    metadata = dict(start=str(start), end=str(end), symbols=SYMBOLS,
                    frame_sha256={s: hashlib.sha256(pd.util.hash_pandas_object(f).values.tobytes()).hexdigest() for s, f in frames.items()},
                    baseline_configs={slug: asdict(config) for slug, config, _ in BASELINES},
                    cointegration_config=asdict(CointegrationConfig()), mean_reversion_config=asdict(MeanReversionConfig()),
                    pairs=pairs, walk_forward=walk, selection_folds=selections, existing_trades=existing, expanded=expanded)
    (out / 'metadata.json').write_text(json.dumps(metadata, indent=2, allow_nan=False) + '\n')
    print(f'Wrote {out / "metadata.json"}', flush=True)


if __name__ == '__main__':
    main()
