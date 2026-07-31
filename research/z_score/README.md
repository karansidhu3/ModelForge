# Z-Score

## Plain-English explanation

A z-score answers: "how unusual is this observation, relative to what's been
typical recently?" It expresses the current value as a number of standard
deviations away from the rolling mean of the last `window` observations. A
z-score of 0 means the value is exactly at the recent average; +2 means it's
two recent-typical-swings above average; -1 means one swing below.

Unlike volatility (which measures *how much things have been moving*, in
absolute terms), a z-score expresses *where a specific point sits*, in units
of that movement — it combines a location measurement (the rolling mean) and
a scale measurement (the rolling standard deviation) into one normalized
number. Both the rolling mean and the rolling standard deviation are exposed
as inspectable intermediates: this is the canonical example
`docs/factor-interface.md` and `docs/validation.md` both use when explaining
why intermediate calculations should be inspectable, not buried.

## Mathematical description

Given a series $x_0, \ldots, x_{n-1}$ and a window size $N \geq 1$:

$$
Z_t = \frac{x_t - \bar{x}_t}{s_t}, \qquad
\bar{x}_t = \frac{1}{N}\sum_{i=0}^{N-1} x_{t-i}, \qquad
s_t = \sqrt{\frac{1}{N-1}\sum_{i=0}^{N-1}\left(x_{t-i} - \bar x_t\right)^2},
\qquad t \geq N-1
$$

The window used for $\bar x_t$ and $s_t$ *includes* $x_t$ itself — this is
the standard "rolling z-score" convention (normalizing a point against a
window that contains it), as opposed to normalizing against only prior
points. `required_history = N`, matching the moving average's window
semantics exactly (this model's mean is computed the same way the moving
average's is).

## Assumptions

- **Sample standard deviation** ($N-1$ denominator), same convention as
  `models/volatility.py` and pandas' own default.
- **Zero variance produces `NaN`, not an error or an arbitrary sentinel.** If
  every value in a window is identical, $s_t = 0$ and $x_t - \bar x_t = 0$
  too (since $x_t$ is one of the identical values) — so $Z_t$ is a genuine
  $0/0$, which floating-point arithmetic evaluates to `NaN`. This is the
  "zero variance" edge case `docs/testing-strategy.md` calls out by name for
  this model specifically. It's handled by *not* handling it: the natural
  floating-point result already communicates "undefined here," and adding
  special-case logic to catch it would just be reproducing what IEEE 754
  division already does correctly.
- **A window is either fully evaluable or entirely undefined.** Same
  `min_periods=window` convention as every rolling-window model here: one
  `NaN` inside a window makes the whole window's mean, std, and therefore
  z-score `NaN` — no partial-window statistics.
- **Single input series, not returns**, same convention as the other models.

## Reference

Standard statistical normalization technique (also called standardization);
no single source paper.

## Performance

Measured with `experiments/benchmark.py`'s `benchmark_factor` (7 repeats,
median reported), `window=20`, on one development laptop:

| observations | median compute time |
|--------------:|---------------------:|
| 1,000          | 0.073 ms             |
| 10,000         | 0.194 ms             |
| 100,000        | 1.392 ms             |

Two rolling passes (mean and std) plus a division — the most expensive of
the five models so far, still comfortably within "runs on a laptop."
