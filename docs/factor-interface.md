# The Factor Interface

## Status

This document describes the *design* of the `Factor` interface. It is the
authoritative contract that Phase 2 implements in `core/factor.py`, and that
every model built after Phase 2 must conform to. Nothing here is implemented
yet — see `ROADMAP.md`.

## What "factor" means in this project

Borrowed from quant terminology, but used narrowly: a `Factor` is any
computation that takes a time series (or a small set of them) as input and
produces a derived series or value as output — a moving average, a momentum
score, a rolling volatility estimate. It is *not* a claim about that
computation's predictive power. The name describes the interface's shape, not
an endorsement of what any implementation is good for.

## Why one interface, not a family of interfaces

Every model in scope for this project (moving average, momentum, volatility,
z-score, mean reversion) has the same essential shape: validated time-series
input in, derived series out, some configuration in between. A single
interface keeps `core/` genuinely general — see DD-001 in
`DESIGN_DECISIONS.md` for why this is a flat interface rather than a class
hierarchy.

## The contract (design sketch)

```python
class Factor(Protocol):
    """A Factor computes a derived series from validated time-series input.

    Implementations must be pure with respect to their declared config:
    the same input series and config always produce the same output.
    No implementation performs I/O — all data arrives already loaded.
    """

    name: str
    """A short, stable identifier used in experiment records and CLI output."""

    required_history: int
    """Minimum number of observations needed before this factor can produce
    its first valid output value (e.g. a 20-day moving average needs 20)."""

    def compute(self, data: pd.Series, params: FactorParams) -> FactorResult:
        """Compute the factor's output over `data`.

        Must not mutate `data`. Must return a result whose index aligns with
        (a subset of) `data`'s index — no silent reindexing.
        """

    def describe(self) -> str:
        """A short, human-readable description of what this factor computes,
        suitable for CLI help text and generated reports."""
```

`FactorParams` is a per-model Pydantic model (e.g. `MovingAverageParams` with
a `window: int` field) — each model defines its own, and the pipeline's
top-level config references it by model name. `FactorResult` is a small
wrapper around the output series plus any intermediate values worth exposing
(see `docs/validation.md` on inspectable intermediate calculations) — e.g. a
z-score's result exposes the rolling mean and rolling standard deviation it
was computed from, not just the final score.

## What implementations must guarantee

- **Purity.** No hidden state, no I/O, no reliance on anything but the
  `data` and `params` arguments.
- **No lookahead.** A value at index `t` may only depend on data at or before
  `t`. This is a correctness requirement, not a style preference — a factor
  that leaks future data isn't wrong in a subtle statistical sense, it's wrong
  in the sense that it couldn't have been computed at the time it claims to
  represent.
- **Explicit handling of insufficient history.** If `required_history` isn't
  met, the factor must say so clearly (e.g. via `NaN` for those indices, not
  a computed-looking but meaningless value).
- **No mutation of input.** `data` belongs to the caller.

## What `core/` guarantees to implementations

- `data` arrives already validated (correct dtype, indexed by date, no
  unexpected gaps beyond what the loader documents).
- `params` arrives already validated by Pydantic before `compute` is called —
  a model never needs to check "did I get a sane parameter."

## Extension without modification

Adding a new model means adding a new class implementing `Factor` plus its own
`FactorParams`. It does not mean adding a case to a dispatcher inside `core/`
— the pipeline discovers and invokes factors by the interface, not by a
hardcoded list of known model names (the discovery mechanism itself is a
Phase 2 design detail, to be logged in `DESIGN_DECISIONS.md` once decided).
