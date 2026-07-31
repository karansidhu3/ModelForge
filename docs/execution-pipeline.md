# Execution Pipeline

## Two different things called "pipeline" here

It's worth being precise, because this project uses "pipeline" in two related
but distinct senses:

1. **The engineering workflow** — the nine-step human process every model goes
   through (research → plain English → math → implementation → validation →
   testing → benchmarking → experiment tracking → documentation), described in
   `CLAUDE.md` and `CONTRIBUTING.md`.
2. **The runtime pipeline** — the actual code path a single execution takes
   through `core/pipeline.py` when a model is run against data. This document
   is about the second one.

## Runtime pipeline stages

```
Config  →  Load Data  →  Run Factor  →  Validate Result  →  Record Experiment  →  Output
```

1. **Config** — a Pydantic config object specifies which model, which
   parameters, which dataset, and which date range. It is validated at
   construction; a malformed config never reaches the later stages.
2. **Load Data** — `data/` resolves the requested dataset (CSV, Yahoo Finance,
   or FRED) into a common, validated series format. This is the only stage
   permitted to perform I/O against an external source.
3. **Run Factor** — the requested model, implementing the `Factor` interface,
   computes its result against the loaded data.
4. **Validate Result** — the result passes through the validation framework
   (see `docs/validation.md`) before it's considered usable: shape checks,
   NaN handling, and — where the model config specifies known-answer
   fixtures — a numerical spot check.
5. **Record Experiment** — `experiments/` writes a record of the run: what
   config produced what output, when, in how long (see
   `docs/experiment-tracking.md`).
6. **Output** — the validated, tracked result is returned to the caller (the
   CLI, a test, or an example script).

## Why validation is its own stage, not folded into "Run Factor"

A model computing a result and that result being *trustworthy* are different
claims. Keeping validation as an explicit, separate stage means every model
gets the same baseline scrutiny regardless of how careful (or not) its author
was inside the model's own code — see `DESIGN_DECISIONS.md`, DD-006.

## Failure behavior

Each stage fails loudly and stops the pipeline rather than passing a
degraded or partial result forward:

- An invalid config raises before any data is loaded.
- A data-loading failure (missing file, unavailable series) raises before any
  model runs.
- A validation failure marks the run as failed in the experiment record — it
  is never silently discarded, because "this run failed validation" is itself
  useful information worth keeping.

## Where this is implemented

`core/pipeline.py`, planned for Phase 2 (see `ROADMAP.md`). This document
describes the intended design; it will be updated if implementation reveals the
design needs to change, with the change logged in `DESIGN_DECISIONS.md`.
