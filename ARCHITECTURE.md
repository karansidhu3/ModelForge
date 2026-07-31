# Architecture

## Purpose of this document

This describes how ModelForge is structured and, more importantly, *why* it's
structured that way. Layout without rationale rots; the next person (or the next
version of the author) needs to know what constraint each boundary is protecting.

## Guiding constraint

`core/` must never need to change to support a new model. Everything about the
architecture follows from that one sentence: it's what forces the model interface
to be genuinely general, and it's what keeps the framework from becoming a pile of
special cases.

## Layers

```
┌─────────────────────────────────────────────────────────┐
│  cli/            Typer commands — argument parsing only  │
├─────────────────────────────────────────────────────────┤
│  experiments/    Run tracking: params, outputs, metadata │
├─────────────────────────────────────────────────────────┤
│  core/           Pipeline · Factor interface · Config ·  │
│                  Validation framework                    │
├─────────────────────────────────────────────────────────┤
│  <model packages>  Concrete Factor implementations        │
│                    (moving average, momentum, z-score…)  │
├─────────────────────────────────────────────────────────┤
│  data/           Loaders: CSV, Yahoo Finance, FRED        │
└─────────────────────────────────────────────────────────┘
```

Data flows up: `data/` produces a validated series, a model package consumes it
through the `Factor` interface, `core/` orchestrates the run and validates the
result, `experiments/` records what happened, and `cli/` is how a human triggers
any of it.

### `core/` — interfaces and orchestration

The load-bearing module. It defines, but does not implement, what a model is (the
`Factor` interface — see `docs/factor-interface.md`), how a run is configured (via
Pydantic models), how a run is executed (the pipeline), and how a result is
checked before it's trusted (the validation framework). `core/` has zero
knowledge of moving averages, momentum, or any other specific model — if it did,
adding model #6 would require editing code that model #1 through #5 also depend
on, which is exactly the coupling this repository exists to avoid.

### `data/` — the only module allowed to touch the outside world

Every external data source (Yahoo Finance, a CSV on disk, FRED) is accessed only
through `data/`. This isn't just tidiness: it means every other module can be
tested with fully deterministic, offline fixtures, and it means "swap the data
source" is a one-file change instead of a search-and-replace across the codebase.

### Model packages — concrete `Factor` implementations

Each model (moving average, momentum, volatility, z-score, mean reversion) is a
self-contained implementation of the `Factor` interface. A model package knows
nothing about the pipeline, the CLI, or experiment tracking — it takes validated
input and returns a result. This is what "composition over inheritance" means in
practice here: models don't inherit shared behavior from a deep base class tree;
they implement a narrow interface and get orchestrated from outside.

### `experiments/` — lightweight, local, opinionated about *what*, not *how*

Tracks that a run happened, with what config, against what data, producing what
output, in how long. It does not know or care what the model computed internally.
See `docs/experiment-tracking.md` for the record format.

### `cli/` — a thin shell

`cli/` exists so a human can invoke the pipeline from a terminal. It contains no
logic beyond argument parsing and calling into `core/`. If a CLI command needs a
unit test beyond "does it call the right function with the right arguments,"
that's a sign logic leaked into the wrong layer.

## Why not a deeper class hierarchy for models

An earlier instinct for a project like this is `BaseFactor` → `TimeSeriesFactor` →
`RollingWindowFactor` → `MovingAverageFactor`, each layer adding behavior. That's
attractive right up until model #4 needs to skip a layer's assumption, at which
point the hierarchy either grows an escape hatch or gets refactored. ModelForge
uses one flat interface (`Factor`) and shared *utilities* (e.g. rolling-window
helpers) that implementations call, rather than inherit from. A model either
implements the interface correctly or it doesn't; there's no ambiguity from
partially-overridden parent behavior.

## Configuration

Every run is described by a Pydantic config model: which model, which
parameters, which dataset, which date range. Config objects are validated at
construction time — a malformed parameter fails immediately with a clear error,
not after a benchmark has been running for ten minutes. Configs are also the unit
of reproducibility: a saved config plus a commit hash should be sufficient to
regenerate a run's output exactly.

## Validation as a layer, not a step

Validation sits inside `core/` as a first-class component, not as ad hoc
assertions scattered through model code. A model's output passes through the
validation framework before it's considered a usable result — see
`docs/validation.md` for what that framework checks and why it exists separately
from unit tests.

## Extension points

Adding a new model should only ever require:

1. A new folder under `research/<model>/` with the math and assumptions.
2. A new model package implementing `Factor`.
3. Tests for that package.

It should never require changing `core/`, `data/`, `experiments/`, or `cli/`. If
it does, that's a signal the `Factor` interface is missing something general,
and the fix belongs in the interface — logged as a design decision — not as a
one-off accommodation for a single model.
