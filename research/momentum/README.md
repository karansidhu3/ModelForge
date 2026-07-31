# Momentum

## Plain-English explanation

Momentum measures how much a series has moved over a fixed look-back
distance: "where is it now, compared to `lookback` observations ago?" A
positive value means the series has risen over that stretch; negative means
it has fallen; the magnitude is how much.

This is the simple, *absolute* form of momentum — a plain difference, not a
percentage. A percentage ("rate of change") version is a different,
common formulation, but it divides by the earlier price and is therefore
undefined when that price is zero. The absolute form avoids that failure
mode entirely and is the more basic of the two, so it's what's implemented
here; a percentage variant is a distinct model, not a parameter of this one.

## Mathematical description

Given a series $x_0, \ldots, x_{n-1}$ and a look-back distance
$L \geq 1$:

$$
M_t = x_t - x_{t-L}, \qquad t \geq L
$$

For $t < L$ there's no $x_{t-L}$ to compare against, so $M_t$ is undefined
(`NaN`).

`required_history = L + 1`: the factor needs the current observation *and*
one from `L` steps earlier, so its first valid value appears once `L + 1`
observations have been seen (at index `L`).

## Assumptions

- **Position-based look-back, not time-based.** `L` counts *observations*,
  not calendar time — same convention as the moving average (see
  `research/moving_average/README.md`). A gap in the input isn't
  compensated for.
- **A single missing input value invalidates exactly two output points, not
  a range.** Unlike a rolling-window model, momentum only ever reads two
  points — $x_t$ and $x_{t-L}$ — so a `NaN` at position $p$ in the input
  makes $M_p$ undefined (missing the arrival value) *and* $M_{p+L}$
  undefined (missing the comparison value), with nothing in between
  affected.
- **This trips a benign false-positive in the validation framework's
  NaN-propagation heuristic.** `core/validation.py`'s heuristic flags an
  output `NaN` as a warning whenever the *same-index* input is clean — it
  has no way to know an output also depends on some other index. At $t = p +
  L$, the input at $t$ is perfectly clean (the missing value was at $p$, not
  $t$), so the heuristic warns about it anyway. That warning is a correct
  application of a heuristic that's documented as same-index-only, not a
  bug — see
  `tests/models/test_momentum.py::test_nan_propagation_at_the_lookback_offset_triggers_a_benign_validation_warning`
  for a concrete demonstration, and the heuristic's own docstring in
  `core/validation.py` for why it's scoped this way regardless.
- **Single input series, not returns.** Same as the moving average: this
  operates on whatever series it's given, without assuming it's already a
  return series.

## Reference

Standard technical-analysis indicator ("rate of change" is the common name
for the percentage variant; this is its absolute-difference sibling). No
single source paper.

## Performance

Measured with `experiments/benchmark.py`'s `benchmark_factor` (7 repeats,
median reported), `lookback=20`, on one development laptop:

| observations | median compute time |
|--------------:|---------------------:|
| 1,000          | 0.030 ms             |
| 10,000         | 0.027 ms             |
| 100,000        | 0.047 ms             |

A single `pandas.Series.shift` and subtraction — no optimization warranted.
