# btc-cent-forecast-01 — BTC 4h-ahead forecaster

Forecasts Bitcoin's US-dollar price 240 minutes ahead, once per case, from the
case's own 1-minute closes. Python 3.13, standard library only, no network,
no randomness — deterministic byte-for-byte across runs (~0.002 s per case).

## Approach

Mild mean reversion to the 24-hour mean. The forecast is the checkpoint close
moved a damped step back toward the mean of the last 1440 closes:

```
forecast = last_close * exp(clip(-0.3 * ln(last_close / MA1440), -0.02, +0.02))
```

rounded to 5 decimals and clamped to (0.00001, 9999999.99999). If a case holds
fewer than 1440 closes, all of them are used; with fewer than 2 prices the
forecast is the last close.

Why this: BTC 4h-ahead moves are near-unpredictable and persistence is hard to
beat. Every momentum/trend model tested on the kit's practice window was worse
than persistence (short-horizon momentum catastrophically so; Holt linear
trend +244%). The only signal with a consistent edge across the larger samples
is mild mean reversion to the 24h mean — the price oscillates around its daily
mean, and this pool's price is a single Orca pool where a large trade moves it
for a moment. k=0.3 sits on a flat optimum; the ±2% cap almost never binds
in-sample (largest in-sample move 0.51%) and exists only as protection against
pathological inputs. The signal is scale-free, so it adapts to whatever price
regime the final's 12 checkpoints land in.

## Validation (honest numbers — the edge is small and regime-dependent)

Backtested on the kit's practice window (2026-11-07 to 2026-11-11):

- **64 rolling pseudo-cases** (single stitched 5520-min series, checkpoints
  every 60 min, up to 4320 min history each): persistence MAE 42,871 cents;
  this model **40,417 cents (-5.7%)**, wins 34/64.
- k-grid on the same 64: k=0.10 → 41,576; 0.15 → 41,141; 0.20 → 40,884;
  0.25 → 40,651; **0.30 → 40,417**; 0.35 → 40,486; 0.40 → 40,635;
  0.50 → 41,300. Flat optimum around 0.3 — not a sharp overfit peak.
- **5 real practice cases p00–p04** (full 4320 history, true actuals recovered
  from the overlapping inputs; p05's actual is outside every input file):
  persistence 47,055; this model 49,572 (+5.3% — 2 wins, 3 losses; p02's
  trend-continuation day dominates). The 5-case sample is noise-dominated;
  the 64-case sample is the better guide, but both are reported honestly.
- Rejected by the same backtests: all momentum variants (60/240/1440-min,
  k≥0.3), EWMA trends, Holt (+244%), 72h mean reversion (+2–5%), median
  anchors, ensembles, vol-scaled variants (no gain over plain reversion).
- Published practice baseline (6 cases): persistence 44,521.58 cents, mean
  error $445.22, worst $766.97.

Sanity run of the final formula on p00–p05: forecasts 74,734 / 74,532 /
73,981 / 73,582 / 73,920 / 73,686; moves -0.04%…+0.51%; deterministic.

## Run

```sh
MAKEFUN_INPUT_DIR=<input dir> MAKEFUN_OUTPUT_DIR=<output dir> python3 main.py
```

Reads every `*.in` file in the input dir and writes one `<case>.out` per case
with `{"forecasts": [{"case": "<id>", "price": <number>}]}`.

## License

MIT — see LICENSE.
