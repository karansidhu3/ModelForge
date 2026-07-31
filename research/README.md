# research/

One folder per model, created *before* that model's code is written — the math
and assumptions come first, the implementation is a translation of what's
documented here.

## Layout (starting Phase 3)

```
research/
└── moving_average/
    └── README.md   Plain-English explanation, mathematical description,
                     documented assumptions, and any relevant references
```

Each `research/<model>/README.md` should contain, at minimum:

1. A plain-English explanation of what the model computes and why it's
   computed that way.
2. The formal mathematical definition.
3. Explicit assumptions (e.g. "assumes evenly spaced trading-day
   observations; does not adjust for corporate actions").
4. Any reference material the implementation is derived from.

See `CLAUDE.md` and `CONTRIBUTING.md` for how this fits into the full
per-model workflow. Nothing lives here yet — Phase 1 only establishes the
convention; the first entry arrives in Phase 3 (see `ROADMAP.md`).
