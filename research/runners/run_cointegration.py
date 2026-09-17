#!/usr/bin/env python3
"""Screen repository Binance symbols on train and backtest selected pairs on test."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import pandas as pd
from trading_strategy.strategies.cointegration import CointegrationConfig, select_pairs, backtest_pair
from run_mean_reversion import load_complete_bars


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--symbols', nargs='+', required=True)
    parser.add_argument('--start', required=True)
    parser.add_argument('--split', required=True, help='First test timestamp (UTC)')
    parser.add_argument('--end', required=True, help='Exclusive end (UTC)')
    parser.add_argument('--interval', choices=['1h', '4h', '1d'], default='1h')
    parser.add_argument('--data-dir', type=Path, default=Path('data/raw'))
    parser.add_argument('--output-dir', type=Path, default=Path('research/reports/cointegration/latest'))
    parser.add_argument('--window', type=int, default=120)
    parser.add_argument('--fee-bps', type=float, default=10)
    parser.add_argument('--slippage-bps', type=float, default=2)
    args = parser.parse_args()
    start, split, end = [pd.to_datetime(s, utc=True) for s in (args.start, args.split, args.end)]
    symbols = sorted(set(s.upper() for s in args.symbols))
    if not start < split < end or len(symbols) < 2:
        parser.error('require start < split < end and at least two symbols')
    config = CointegrationConfig(window=args.window, min_train_bars=max(240, args.window), fee_bps=args.fee_bps, slippage_bps=args.slippage_bps)
    config.validate()
    if any(t.floor(args.interval) != t for t in (start, split, end)):
        parser.error('dates must align to interval boundaries')
    if (split - start) / pd.Timedelta(args.interval) < config.min_train_bars:
        parser.error('insufficient training history')
    frames = {s: load_complete_bars(args.data_dir, s, start, end, args.interval) for s in symbols}
    selection = select_pairs(pd.DataFrame({s: f.close for s, f in frames.items()}), split, config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    selection.to_csv(args.output_dir / 'selection.csv', index=False)
    summaries = []
    for pair in selection.loc[selection.selected].itertuples():
        bars = pd.DataFrame({f'{leg}_{field}': frames[symbol][field] for leg, symbol in [('y', pair.y), ('x', pair.x)] for field in ['open', 'close']})
        result = backtest_pair(bars, split, pair.intercept, pair.beta, config)
        result.to_csv(args.output_dir / f'{pair.y}_{pair.x}.csv')
        summaries.append(dict(y=pair.y, x=pair.x, trades=int((result.event == 'entry').sum()), total_return=float(result.equity.iloc[-1] - 1), maximum_drawdown=float(result.drawdown.min()), costs=float(result.cost.sum())))
    metadata = dict(config=asdict(config), start=str(start), split=str(split), end=str(end), interval=args.interval, symbols=symbols, summaries=summaries, status='completed' if summaries else 'no_pairs_selected')
    (args.output_dir / 'metadata.json').write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
