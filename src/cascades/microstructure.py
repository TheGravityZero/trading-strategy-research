from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

from .aggtrades import deterministic_sample
from .data import download_daily_aggtrades, read_aggtrades_archive


def _features(trades: pd.DataFrame, event: pd.Series) -> dict:
    t = event["timestamp"]
    direction = event["direction"]
    pre = trades[(trades.timestamp >= t - pd.Timedelta("5m")) & (trades.timestamp < t)].copy()
    post = trades[(trades.timestamp >= t) & (trades.timestamp <= t + pd.Timedelta("5m"))].copy()
    result = {"trades": len(trades), "pre_trades": len(pre), "post_trades": len(post)}
    if pre.empty or post.empty:
        return result
    for frame in (pre, post):
        frame["quote"] = frame.price * frame.quantity
        frame["delta"] = np.where(frame.buyer_maker, -frame.quote, frame.quote)
    event_price = event["close"]
    bin_bps = 5
    post["price_bin"] = np.round(np.log(post.price) * 10_000 / bin_bps).astype(int)
    profile = post.groupby("price_bin").agg(volume=("quote", "sum"), delta=("delta", "sum"))
    total_volume = profile.volume.sum()
    extreme_price = post.price.min() if direction < 0 else post.price.max()
    distance_bps = 10_000 * np.abs(np.log(post.price / extreme_price))
    extreme = post[distance_bps <= 10]
    impulse_aggressive = post[
        (post.buyer_maker if direction < 0 else ~post.buyer_maker)
    ]
    impulse_quote = impulse_aggressive.quote.sum()
    further_move = (
        max(0.0, 10_000 * np.log(event_price / post.price.min()))
        if direction < 0
        else max(0.0, 10_000 * np.log(post.price.max() / event_price))
    )
    aggressive_vwap = np.average(
        impulse_aggressive.price, weights=impulse_aggressive.quantity
    ) if len(impulse_aggressive) else np.nan
    pre_level = pre.price.min() if direction < 0 else pre.price.max()
    swept = event_price < pre_level if direction < 0 else event_price > pre_level
    reclaimed = (
        post.price.max() > pre_level if direction < 0 else post.price.min() < pre_level
    )
    vwap_reclaimed = (
        post.price.max() > aggressive_vwap
        if direction < 0
        else post.price.min() < aggressive_vwap
    )
    poc_bin = profile.volume.idxmax()
    poc_price = np.exp(poc_bin * bin_bps / 10_000)
    poc_reclaimed = (
        post.price.max() > poc_price if direction < 0 else post.price.min() < poc_price
    )
    first = post[post.timestamp < t + pd.Timedelta("2m")]
    later = post[post.timestamp >= t + pd.Timedelta("2m")]
    first_extreme = first.price.min() if direction < 0 else first.price.max()
    retest = (
        later.price.min() <= first_extreme * 1.0005
        if direction < 0 and len(later)
        else later.price.max() >= first_extreme * 0.9995
        if len(later)
        else False
    )
    result.update(
        {
            "entry_price_5m": post.iloc[-1].price,
            "absorption_score": impulse_quote / (further_move + 1.0),
            "normalized_absorption": (impulse_quote / total_volume) / (further_move + 1.0),
            "extreme_volume_share": extreme.quote.sum() / total_volume,
            "failed_auction_score": 1 - extreme.quote.sum() / total_volume,
            "sweep_reclaim": bool(swept and reclaimed),
            "aggressor_vwap_reclaim": bool(vwap_reclaimed),
            "cvd_post": post.delta.sum(),
            "aligned_cvd_post": direction * post.delta.sum(),
            "normalized_aligned_cvd": direction * post.delta.sum() / total_volume,
            "poc_distance_bps": 10_000 * abs(np.log(event_price / poc_price)),
            "poc_reclaim": bool(poc_reclaimed),
            "volume_concentration": profile.volume.max() / total_volume,
            "retest": bool(retest),
        }
    )
    return result


def collect_microstructure(
    events_path: Path,
    thresholds_path: Path,
    cache_dir: Path,
    output_path: Path,
    per_group: int = 5,
) -> None:
    events = pd.read_csv(events_path, parse_dates=["timestamp"])
    threshold = json.loads(thresholds_path.read_text())["oi_threshold_research_q25"]
    eligible = events[
        events["split"].isin(["research", "validation"])
        & (events.oi_change_15m <= threshold)
    ]
    sample = deterministic_sample(eligible, per_group)
    days = sample.assign(day=sample.timestamp.dt.date)[["symbol", "day"]].drop_duplicates()
    jobs = list(days.itertuples(index=False, name=None))
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(download_daily_aggtrades, symbol, day, cache_dir): (symbol, day)
            for symbol, day in jobs
        }
        for number, future in enumerate(as_completed(futures), start=1):
            print(f"download [{number}/{len(days)}] {future.result()}", flush=True)
    records = []
    loaded: dict[tuple[str, object], pd.DataFrame] = {}
    for number, (_, event) in enumerate(sample.iterrows(), start=1):
        key = (event.symbol, event.timestamp.date())
        if key not in loaded:
            path = cache_dir / event.symbol / "aggTrades" / (
                f"{event.symbol}-aggTrades-{event.timestamp.date()}.zip"
            )
            loaded[key] = read_aggtrades_archive(path)
        day_trades = loaded[key]
        trades = day_trades[
            (day_trades.timestamp >= event.timestamp - pd.Timedelta("5m"))
            & (day_trades.timestamp <= event.timestamp + pd.Timedelta("5m"))
        ].copy()
        record = event.to_dict()
        record.update(_features(trades, event))
        records.append(record)
        print(f"feature [{number}/{len(sample)}] {event.symbol}: {len(trades)}", flush=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(output_path, index=False)
