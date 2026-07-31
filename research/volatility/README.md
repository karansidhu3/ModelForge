# Volatility

## Plain-English explanation

Volatility measures how much a series' *returns* have been bouncing around
recently — not the level of the series itself, but how much it moves from
one observation to the next. A price that steadily climbs 1% every day has
zero volatility by this measure, even though the price itself is changing a
lot; a price that alternates +5%/-5% every day has high volatility even if
it ends up back where it started.

This is a two-step calculation: first turn the price series into a series of
period-over-period returns, then take the rolling standard deviation of
those returns. Both steps are exposed — the return series is available as an
inspectable intermediate, not just the final volatility number — so it's
possible to see *what the volatility number was computed from*, per
`docs/validation.md`'s guidance on inspectable intermediates.

## Mathematical description

Given a series $x_0, \ldots, x_{n-1}$, the simple return at $t \geq 1$ is:

$$
r_t = \frac{x_t - x_{t-1}}{x_{t-1}}
$$

Given a window size $N \geq 1$, volatility at $t$ is the sample standard
deviation of the trailing $N$ returns:

$$
V_t = \sqrt{\frac{1}{N-1}\sum_{i=0}^{N-1}\left(r_{t-i} - \bar r_t\right)^2},
\qquad \bar r_t = \frac{1}{N}\sum_{i=0}^{N-1} r_{t-i}, \qquad t \geq N
$$

(Sample standard deviation, $N-1$ in the denominator — the same convention
`pandas.Series.std()` uses by default, matching `core/factor.py`'s general
preference for pandas' own defaults where there isn't a strong reason to
deviate.)

`required_history = N + 1`: computing $N$ returns needs $N+1$ prices, so the
first valid volatility value appears once $N+1$ observations have been seen.

## Assumptions

- **Simple returns, not log returns.** $(x_t - x_{t-1})/x_{t-1}$, not
  $\ln(x_t / x_{t-1})$. Both are standard; this implementation picks one and
  states it rather than leaving it ambiguous. A log-return variant would be
  a distinct model, not a parameter of this one.
- **Assumes strictly positive input values.** A return computed against a
  zero-valued observation ($x_{t-1} = 0$) is undefined; standard
  floating-point division produces `inf` or `nan` rather than a Python
  exception, and that's what this implementation does too — it does not
  special-case a zero price. This isn't the same failure mode as the
  documented "NaN in input" edge case: an input of exactly `0.0` is not
  itself `NaN`, so it will produce a non-finite (not necessarily `NaN`)
  return rather than a `NaN` one.
- **Not annualized.** The output is the standard deviation of returns over
  the raw sampling interval of the input (whatever that is — daily,
  weekly, ...). Multiplying by $\sqrt{\text{periods per year}}$ to annualize
  is a presentation choice left to the caller, not baked into the model.
- **Zero variance is well-defined, not an error.** A window of identical
  returns (e.g. constant percentage growth) has `V_t = 0.0` exactly — no
  division occurs in a standard-deviation calculation the way it does in a
  z-score's normalization, so there's no zero-variance failure mode to
  document beyond "the result is legitimately zero."
- **Single input series, not returns.** Same convention as the other models:
  operates on a price/level series and derives returns itself, rather than
  assuming the input already is a return series.

## Reference

Historical (realized) volatility via rolling standard deviation of returns
is standard practice; no single source paper.

## Performance

Measured with `experiments/benchmark.py`'s `benchmark_factor` (7 repeats,
median reported), `window=20`, on one development laptop:

| observations | median compute time |
|--------------:|---------------------:|
| 1,000          | 0.079 ms             |
| 10,000         | 0.155 ms             |
| 100,000        | 1.036 ms             |

Slower than momentum or the moving average since it's two rolling-style
passes (`pct_change` then a rolling `std`) rather than one — still well
within "runs on a laptop" for any realistic input size this project deals
with.
