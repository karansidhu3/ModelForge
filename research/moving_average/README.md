# Moving Average

## Plain-English explanation

A moving average smooths a series by replacing each point with the average of
itself and the `window - 1` points before it. As you move forward in time,
the window "moves" with you — you drop the oldest point and add the newest
one. It's the simplest possible way to damp short-term noise in a series and
see the underlying trend: a single spike in the raw data only ever affects
`window` consecutive output points, and its effect on any one of them is
diluted by the other `window - 1` points sharing the average.

This is the *simple* moving average (SMA) — every point in the window is
weighted equally. That's a deliberate simplification: exponential and other
weighted moving averages exist and weight recent points more heavily, but
they're a different, separate model, not a variant of this one.

## Mathematical description

Given a series $x_0, x_1, \ldots, x_{n-1}$ and a window size $N \geq 1$, the
simple moving average at index $t$ is:

$$
\mathrm{SMA}_t = \frac{1}{N} \sum_{i=0}^{N-1} x_{t-i}, \qquad t \geq N - 1
$$

For $t < N - 1$ there are not yet $N$ observations available, so
$\mathrm{SMA}_t$ is undefined (represented as `NaN` in the implementation,
per the no-lookahead and explicit-insufficient-history requirements in
`docs/factor-interface.md`).

`required_history = N`: the factor cannot produce its first valid value until
`N` observations have been seen.

## Assumptions

- **Order, not spacing, is what matters.** The average is over the last `N`
  *observations* in the series, not the last `N` units of calendar time. A
  gap in the input (e.g. a missing trading day) is not filled or
  interpolated — see `data/loaders.py`, which loads exactly the rows present
  in the file — so the window silently spans whatever time gap exists between
  those rows. This implementation does not assume or enforce a trading-day
  calendar.
- **No adjustment for corporate actions.** If the input series is a raw price
  series that isn't split/dividend-adjusted, the average isn't either. That's
  a data-quality concern for whatever produced the input series, not
  something this model corrects for.
- **A window needs `N` non-null observations, not just `N` rows.** Consistent
  with `pandas.Series.rolling(window=N, min_periods=N)` semantics: if any
  point inside a window is `NaN`, that window doesn't have `N` usable
  observations and the output is `NaN` there too — the `NaN` "propagates"
  forward until it ages out of the window (see the known-answer test in
  `tests/models/test_moving_average.py::test_a_single_nan_propagates_exactly_window_minus_one_steps_forward`).
  This is standard rolling-window behavior, not a bug — it's why
  `core/validation.py`'s NaN-propagation check is a heuristic warning rather
  than a hard failure: this is a legitimate, expected way for a `NaN` to
  appear after `required_history` observations have technically been seen.
- **Single input series, not returns.** The model operates on whatever series
  it's given (e.g. a price level series) — it does not assume returns,
  log-returns, or any particular transformation has already been applied.

## Reference

Standard technique; no single source paper. The definition above is the
textbook definition of a simple moving average, used here as-is.

## Performance

Measured, not guessed (per `CLAUDE.md`): `MovingAverageFactor.compute` on a
synthetic series, `window=20`, on one run on a single development laptop —
no formal benchmarking harness exists yet (that's `core/pipeline.py`
Phase 4 scope), so these are single measurements, not statistically
rigorous benchmarks:

| observations | compute time |
|--------------:|-------------:|
| 1,000          | 0.12 ms      |
| 10,000         | 0.08 ms      |
| 100,000        | 0.53 ms      |

Backed by `pandas.Series.rolling`, which is a compiled, vectorized
implementation — well within "runs on a laptop" for any realistic input size
this project deals with. No optimization work is warranted here.
