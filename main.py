#!/usr/bin/env python3
"""Forecast BTC's US-dollar price 240 minutes ahead.

Model: mild mean reversion to the 24-hour mean. The forecast is the checkpoint
close moved a damped step back toward the mean of the last 1440 closes:
    forecast = last * exp(clip(-0.3 * ln(last / mean1440), -0.02, +0.02))
Pure arithmetic on the case's own prices: no network, no randomness, no fitted
levels — the signal is scale-free, so it adapts to whatever price regime the
final's 12 checkpoints land in. Validated on the kit's practice window
(2026-11-07 to 2026-11-11): 40,417 cents MAE over 64 rolling pseudo-cases vs
42,871 for persistence (-5.7%); k=0.3 sits on a flat optimum (0.25–0.35 all
within 0.6%). Momentum and trend models were all worse than persistence there.
"""
import json
import math
import os
from pathlib import Path

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

WINDOW = 1440          # 24 hours of 1-minute closes
K = 0.3                # reversion strength (flat optimum 0.25-0.35)
CAP = 0.02             # max |log move| allowed, safety only
MIN_PRICE = 0.00001
MAX_PRICE = 9_999_999.99999


def price5(x):
    """x kept on the grid's 5 decimals and inside the scorer's bounds."""
    return round(min(MAX_PRICE, max(MIN_PRICE, x)) * 1e5) / 1e5


def forecast(prices):
    """One forecast from one case's closes (last element is the checkpoint)."""
    if not prices:
        raise ValueError("no prices")
    last = prices[-1]
    if not math.isfinite(last):
        raise ValueError("last price is not finite")
    n = min(WINDOW, len(prices))
    if n < 2:
        return price5(last)
    window = prices[-n:]
    mean = sum(window) / n
    if not (mean > 0) or not math.isfinite(mean):
        return price5(last)
    move = -K * math.log(last / mean)
    move = max(-CAP, min(CAP, move))
    return price5(last * math.exp(move))


def main():
    in_dir = Path(INPUT_DIR)
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(in_dir.glob("*.in")):
        case_id = path.name[:-3]
        case = json.loads(path.read_text(encoding="utf-8"))
        markets = case["markets"]
        if len(markets) != 1:
            raise ValueError(f"{path.name} does not hold exactly one market")
        price = forecast(markets[0]["prices"])
        out = {"forecasts": [{"case": case_id, "price": price}]}
        (out_dir / f"{case_id}.out").write_text(
            json.dumps(out) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
