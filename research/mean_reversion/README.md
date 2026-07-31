# Mean Reversion

## Plain-English explanation

"Mean reversion" is a family of ideas, not one formula — the common thread is
"how far has this series strayed from its own recent typical level, and by
how much (in relative terms)?" This implementation picks the most direct,
literal formalization of that question: the percentage gap between the
current value and its own trailing moving average.

This is deliberately *not* the same computation as the z-score. A z-score
normalizes distance-from-mean by recent *volatility* (in units of standard
deviation) — "how unusual is this, given how much things have been
bouncing around?" Mean reversion here normalizes distance-from-mean by the
*price level* itself (in units of percent) — "how far above or below its own
recent average is this, as a fraction of that average?" Two prices can have
identical z-scores while having very different mean-reversion percentages
(if their recent volatility differs), and vice versa. They answer different
questions and can disagree.

The trailing moving average this model computes is exposed as an inspectable
intermediate — the same "don't bury the intermediate step" principle applied
in `models/z_score.py` and `models/volatility.py`.

## Mathematical description

Given a series $x_0, \ldots, x_{n-1}$ and a window size $N \geq 1$:

$$
D_t = \frac{x_t - \mathrm{MA}_t}{\mathrm{MA}_t}, \qquad
\mathrm{MA}_t = \frac{1}{N}\sum_{i=0}^{N-1} x_{t-i}, \qquad t \geq N-1
$$

`required_history = N`, identical to the moving average's window semantics —
$\mathrm{MA}_t$ is computed exactly the way `models/moving_average.py`
computes it.

## Assumptions

- **Computes its own rolling mean rather than depending on
  `MovingAverageFactor`.** The formula for $\mathrm{MA}_t$ duplicates one
  line from `models/moving_average.py` instead of importing and calling that
  model directly. This is a deliberate choice, not an oversight — see DD-001
  in `DESIGN_DECISIONS.md`: models here share *utility patterns*
  (`data.rolling(...)`), not *dependencies on each other*. A model importing
  a sibling model would mean a change to one model could require touching
  another — exactly the coupling `ARCHITECTURE.md` rules out. The
  duplicated line is small and unlikely to need to change independently in
  a way that would cause drift.
- **Division by the moving average, not by price level directly** — the same
  assumption `models/volatility.py` makes about returns applies here: if
  $\mathrm{MA}_t = 0$, the result is `inf` (assuming $x_t \neq 0$ too) rather
  than a raised exception. This implementation assumes strictly positive
  input values and does not special-case a zero or negative moving average.
- **A window is either fully evaluable or entirely undefined** — same
  `min_periods=window` convention as every other rolling-window model here.
- **Single input series, not returns**, same convention as the other models.

## Reference

"Percentage price oscillator" / "distance from moving average" is a standard
technical-analysis construction; no single source paper.

## Performance

Measured with `experiments/benchmark.py`'s `benchmark_factor` (7 repeats,
median reported), `window=20`, on one development laptop:

| observations | median compute time |
|--------------:|---------------------:|
| 1,000          | 0.043 ms             |
| 10,000         | 0.082 ms             |
| 100,000        | 0.477 ms             |

One rolling mean plus a division — no optimization warranted.
