#!/usr/bin/env python3
"""Run guarded mean reversion on cached Binance archives, without downloads."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

import numpy as np
import pandas as pd

from trading_strategy.data import read_kline_archive
from trading_strategy.strategies.mean_reversion import (
    MeanReversionConfig, backtest_mean_reversion, select_pairs,
)


def load_complete_bars(raw_dir, symbol, start, end, interval, *, include_ohlcv=False):
    """Use one native resolution; reject partial aggregate bars and duplicates."""
    target = pd.Timedelta(interval)
    for native, frequency in [('1h', '1h'), ('30m', '30min'), ('15m', '15min'), ('1m', '1min')]:
        step = pd.Timedelta(frequency)
        paths = sorted((raw_dir / symbol / native).glob('**/*.zip'))
        if paths and step <= target and target % step == pd.Timedelta(0):
            break
    else:
        raise ValueError(f'No suitable cached archives for {symbol}')
    chunks = []
    for path in paths:
        stamp = path.stem.removeprefix(f'{symbol}-{native}-')
        archive_start = pd.to_datetime(stamp, utc=True)
        archive_end = archive_start + (pd.offsets.MonthBegin(1) if len(stamp) == 7 else pd.Timedelta(days=1))
        if archive_start >= end or archive_end <= start:
            continue
        chunks.append(read_kline_archive(path, symbol))
    if not chunks:
        raise ValueError(f'No cached data in requested range for {symbol}')
    frame = pd.concat(chunks).set_index('timestamp').sort_index()
    frame = frame.loc[(frame.index >= start) & (frame.index < end)]
    # Daily and monthly archives may overlap, but must agree on prices.
    duplicate = frame.index.duplicated(keep=False)
    if (frame.loc[duplicate].groupby(level=0)[['open', 'close']].nunique() > 1).any().any():
        raise ValueError(f'Conflicting archives for {symbol}')
    frame = frame.loc[~frame.index.duplicated()]
    expected = pd.date_range(start, end, freq=frequency, inclusive='left')
    frame = frame.reindex(expected)
    if frame[['open', 'close']].isna().any().any():
        raise ValueError(f'Missing source bars for {symbol}; choose a fully covered range')
    if not np.isfinite(frame[['open', 'close']]).all().all() or not (frame[['open', 'close']] > 0).all().all():
        raise ValueError(f'Invalid source prices for {symbol}')
    if include_ohlcv:
        fields = frame[['open', 'high', 'low', 'close', 'volume']]
        if not np.isfinite(fields).all().all() or (fields.volume < 0).any() or not (fields[['open', 'high', 'low', 'close']] > 0).all().all():
            raise ValueError(f'Invalid OHLCV for {symbol}')
        if (fields.high < fields[['open', 'close', 'low']].max(axis=1)).any() or (fields.low > fields[['open', 'close', 'high']].min(axis=1)).any():
            raise ValueError(f'Invalid OHLC relation for {symbol}')
        return frame.resample(interval).agg(open=('open', 'first'), high=('high', 'max'),
                                          low=('low', 'min'), close=('close', 'last'),
                                          volume=('volume', 'sum'))
    return frame.resample(interval).agg(open=('open', 'first'), close=('close', 'last'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--symbols', nargs='+', default=['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
    for field in ('start', 'split', 'end'):
        parser.add_argument(f'--{field}', required=True)
    parser.add_argument('--interval', choices=['1h', '4h', '1d'], default='1h')
    parser.add_argument('--data-dir', type=Path, default=Path('data/raw'))
    parser.add_argument('--output-dir', type=Path, default=Path('research/reports/mean-reversion/latest'))
    defaults = MeanReversionConfig()
    for name, value in asdict(defaults).items():
        parser.add_argument('--' + name.replace('_', '-'), type=type(value), default=value)
    args = parser.parse_args()
    start, split, end = [pd.to_datetime(getattr(args, key), utc=True) for key in ('start', 'split', 'end')]
    symbols = sorted(set(s.upper() for s in args.symbols))
    if len(symbols) < 2 or not start < split < end:
        parser.error('require at least two symbols and start < split < end')
    if any(t.floor(args.interval) != t for t in (start, split, end)):
        parser.error('dates must align to interval boundaries')
    config = MeanReversionConfig(**{k: getattr(args, k) for k in asdict(defaults)})
    config.validate()
    if (split - start) / pd.Timedelta(args.interval) < config.min_train_bars:
        parser.error('training range is shorter than min_train_bars')
    frames = {s: load_complete_bars(args.data_dir, s, start, end, args.interval) for s in symbols}
    selection = select_pairs(pd.DataFrame({s: f.close for s, f in frames.items()}), split, config)
    summaries, outputs = [], {}
    for pair in selection.loc[selection.selected].itertuples():
        bars = pd.DataFrame({f'{leg}_{field}': frames[symbol][field]
                             for leg, symbol in [('y', pair.y), ('x', pair.x)]
                             for field in ('open', 'close')})
        result, trades = backtest_mean_reversion(bars, split, pair.intercept, pair.beta, config)
        key = f'{pair.y}_{pair.x}'
        outputs[key] = (result, trades)
        summaries.append(dict(pair=key, trades=len(trades),
                              win_rate=float((trades.net_return > 0).mean()) if len(trades) else None,
                              total_return=float(result.equity.iloc[-1] - 1),
                              maximum_drawdown=float(result.drawdown.min()),
                              costs=float(result.cost.sum())))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    selection.to_csv(args.output_dir / 'selection.csv', index=False)
    for key, (result, trades) in outputs.items():
        result.to_csv(args.output_dir / f'{key}_bars.csv')
        trades.to_csv(args.output_dir / f'{key}_trades.csv', index=False)
    metadata = dict(config=asdict(config), start=str(start), split=str(split), end=str(end),
                    interval=args.interval, symbols=symbols, summaries=summaries,
                    status='completed' if summaries else 'no_pairs_selected')
    (args.output_dir / 'metadata.json').write_text(json.dumps(metadata, indent=2, allow_nan=False) + '\n')
    print(json.dumps(metadata, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
