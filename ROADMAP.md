# Roadmap

Development proceeds in phases. Each phase is expected to leave the repository
in a stable, usable state — nothing half-wired between phases.

## Phase 1 — Repository Design (current: complete)

- [x] Repository structure
- [x] `CLAUDE.md` engineering constitution
- [x] `ARCHITECTURE.md`
- [x] `DESIGN_DECISIONS.md`
- [x] `CONTRIBUTING.md`
- [x] Deep-dive docs: philosophy, execution pipeline, validation, experiment
      tracking, reproducibility, factor interface (design only), testing
      strategy
- [x] Packaging scaffolding (`pyproject.toml`, `requirements-dev.txt`,
      `.gitignore`, `LICENSE`)
- [x] Folder skeleton for `src/`, `docs/`, `research/`, `examples/`, `tests/`

No execution logic exists yet. That's intentional — this phase is about getting
the shape of the system right before any code depends on it.

## Phase 2 — Core Execution Engine (complete)

- [x] `core/config.py` — Pydantic config schema for a run
- [x] `core/factor.py` — the `Factor` interface, implemented per
      `docs/factor-interface.md`
- [x] `core/pipeline.py` — orchestrates: load data → run factor → validate →
      record experiment
- [x] `core/validation.py` — the validation framework described in
      `docs/validation.md`
- [x] `data/loaders.py` — CSV loader first (fully offline, no network
      dependency for tests); Yahoo Finance and FRED loaders after
- [x] Tests for all of the above, using synthetic fixture data

Exit criterion: a hand-written toy `Factor` can be run end-to-end through the
pipeline against a CSV fixture and produce a validated, tracked result. Met —
see `tests/core/test_pipeline.py`. "Tracked" is currently a no-op stub;
`experiments/` recording lands in Phase 4 as originally scoped. Factor
dispatch is direct injection rather than a name-based registry — see DD-008
in `DESIGN_DECISIONS.md`.

## Phase 3 — First Real Model (complete)

- [x] `research/moving_average/README.md` — plain-English explanation and math
- [x] Moving Average `Factor` implementation
- [x] Known-input/known-output tests, edge cases (insufficient window, NaNs)
- [x] Assumptions documented
- [x] One tracked experiment run

Exit criterion: the first model is implemented, validated, tested, and
documented end to end — establishing the template every later model follows.
Met — see `src/modelforge/models/moving_average.py`,
`tests/models/test_moving_average.py`, and `examples/moving_average.py` (runs
the model end-to-end through `run_pipeline`; "tracked" is still the Phase 2
no-op stub, same caveat as Phase 2's exit criterion — real recording is
Phase 4 scope).

## Phase 4 — Experiment Runner, Benchmarking, Reporting (complete)

- [x] `experiments/tracker.py` — local run recording per
      `docs/experiment-tracking.md`
- [x] Benchmarking harness (runtime characteristics per model, recorded not
      guessed)
- [x] Basic reporting: summarize tracked experiments (e.g. table of runs, params,
      runtime) via the CLI

Exit criterion: running the same model twice with different parameters produces
two comparable, inspectable tracked experiments. Met — see
`tests/core/test_pipeline.py::test_two_runs_with_different_params_produce_comparable_tracked_experiments`
and `examples/moving_average.py`, which now produces a real record under
`experiments/runs/` when run. `core/pipeline.py`'s experiment-recording stage
is no longer a stub — it calls `experiments/tracker.py` for real, including a
commit hash (now that real git history exists, per
`docs/experiment-tracking.md`'s "Commit hash: planned" note). `modelforge
experiments list` reports on what's been recorded; there is still no `modelforge
run` command — see the Phase 4 update to DD-008 in `DESIGN_DECISIONS.md`.

## Phase 5 — Additional Models, Refactoring, Documentation (complete)

- [x] Momentum
- [x] Volatility
- [x] Z-Score
- [x] Mean Reversion
- [x] Revisit `core/` for any generalization the additional models revealed was
      missing (logged in `DESIGN_DECISIONS.md`, not made silently)
- [x] Documentation pass across the whole repository

Exit criterion: five models, one shared framework, no model-specific logic
leaked into `core/`. Met — see `src/modelforge/models/`,
`research/<model>/README.md` for each, and `examples/<model>.py` for each.
**No `core/` changes were needed** to support the four new models: `FactorResult.intermediates`
(already part of the Phase 2 design) was sufficient for volatility, z-score,
and mean reversion to expose their intermediate calculations; the flat
`Factor` Protocol needed no new attributes; `core/validation.py`'s
same-index-only NaN heuristic surfaced a real, already-documented limitation
on momentum (a benign warning, not a failure — see
`research/momentum/README.md`) rather than requiring a change. Since there
was no generalization to make, there's nothing new to log in
`DESIGN_DECISIONS.md` beyond DD-001's existing rationale for why models don't
depend on each other (momentum, volatility, z-score, and mean reversion each
compute their own rolling statistics rather than sharing a helper or calling
into `moving_average.py`, even where the math overlaps).
`research/README.md`, `tests/README.md`, and `examples/README.md` — all
stale since Phase 1 — were updated to reflect the current repository state.

## Explicitly out of scope, always

- Live or simulated trade execution
- Portfolio optimization or capital allocation
- Any claim of financial performance
- Paid APIs, cloud infrastructure, or GPU requirements
