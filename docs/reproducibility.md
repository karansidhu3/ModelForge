# Reproducibility

## The guarantee this project aims for

Given a recorded experiment (its config plus the commit hash the code was at),
re-running it should produce the same output. If it doesn't, that's treated as
a bug in the framework, not an accepted limitation.

## What makes a run reproducible

- **Config-driven execution.** Every run is fully described by its Pydantic
  config — model, parameters, dataset reference, date range. Nothing about a
  run's behavior depends on ambient state (environment variables, a notebook's
  execution order, a value someone forgot they'd changed in a REPL).
- **Deterministic computation.** No unseeded randomness anywhere in a model's
  computation. If a future model genuinely needs randomness (e.g. a
  bootstrap), the seed is part of its config and recorded with the run.
- **Pinned dependencies.** `pyproject.toml` pins minimum versions; a
  `requirements-dev.txt` lockstep keeps the dev toolchain consistent. The
  goal is that "works on my machine" and "works on a fresh clone" are the same
  claim.
- **Versioned code.** Every tracked experiment records the commit hash it ran
  at (see `docs/experiment-tracking.md`), so "reproduce this run" means "check
  out this commit, load this config, run it" — not "hope the code hasn't
  changed since."
- **Data referenced, not silently re-fetched with different results.** A
  dataset reference in a config specifies exactly what was loaded (source,
  symbol, date range). For CSV-based data this is inherently stable; for
  network-sourced data (Yahoo Finance, FRED) this is a known limitation —
  see below.

## A known limitation, stated honestly

Yahoo Finance and FRED data can be revised or extended after the fact (e.g. a
data provider corrects a historical value, or a series gets a later data point
appended). A dataset reference pins *what was requested*, not a guarantee that
the provider will return byte-identical data on every future fetch. Where
exact reproducibility matters, the recommended path is to snapshot the fetched
data to a local CSV as part of the run and reference that snapshot — this is
noted here rather than glossed over, because a reproducibility document that
hides its own limitations isn't a reproducibility document.

## Environment capture

Beyond pinned dependency versions, nothing exotic is planned here (no
Docker image, no full environment freeze) — that would be infrastructure this
project's constraints explicitly rule out (no cloud, no paid services,
everything on a laptop). If reproducing a run across machines becomes a real
problem in practice, that's a design decision to make deliberately and log in
`DESIGN_DECISIONS.md`, not to solve preemptively.
