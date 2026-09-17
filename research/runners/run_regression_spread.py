#!/usr/bin/env python3
"""Run the rolling-regression spread baseline without correlation filtering."""

from pair_baseline_runner import run_pair_baseline


if __name__ == "__main__":
    run_pair_baseline("regression-spread")
