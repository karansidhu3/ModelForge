# research/

One folder per model, created *before* that model's code is written — the math
and assumptions come first, the implementation is a translation of what's
documented here.

## Layout

```
research/
├── moving_average/README.md
├── momentum/README.md
├── volatility/README.md
├── z_score/README.md
└── mean_reversion/README.md
```

Each `research/<model>/README.md` contains, at minimum:

1. A plain-English explanation of what the model computes and why it's
   computed that way.
2. The formal mathematical definition.
3. Explicit assumptions (e.g. "assumes evenly spaced trading-day
   observations; does not adjust for corporate actions").
4. Any reference material the implementation is derived from.
5. Measured (not guessed) performance numbers, via
   `experiments/benchmark.py`.

See `CLAUDE.md` and `CONTRIBUTING.md` for how this fits into the full
per-model workflow.
