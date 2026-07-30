#!/usr/bin/env python3
"""Run the fixed liquidation-cascade reversal study."""

from __future__ import annotations

import argparse
from pathlib import Path

from cascades.study import run_large_study
from cascades.utils.crypto import DEFAULT_CRYPTO_SYMBOLS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sector", choices=["crypto"], default="crypto")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "strategies/reports/cascade-reversal/crypto/fixed-15m-oi-filter"
        ),
    )
    parser.add_argument(
        "--symbols", nargs="+", default=DEFAULT_CRYPTO_SYMBOLS
    )
    parser.add_argument("--oi-drop-threshold", type=float, default=-0.002)
    args = parser.parse_args()
    run_large_study(
        args.raw_dir,
        args.output_dir,
        [symbol.upper() for symbol in args.symbols],
        args.oi_drop_threshold,
    )


if __name__ == "__main__":
    main()
