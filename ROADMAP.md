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

## Phase 3 — First Real Model (not started)

- [ ] `research/moving_average/README.md` — plain-English explanation and math
- [ ] Moving Average `Factor` implementation
- [ ] Known-input/known-output tests, edge cases (insufficient window, NaNs)
- [ ] Assumptions documented
- [ ] One tracked experiment run

Exit criterion: the first model is implemented, validated, tested, and
documented end to end — establishing the template every later model follows.

## Phase 4 — Experiment Runner, Benchmarking, Reporting (not started)

- [ ] `experiments/tracker.py` — local run recording per
      `docs/experiment-tracking.md`
- [ ] Benchmarking harness (runtime characteristics per model, recorded not
      guessed)
- [ ] Basic reporting: summarize tracked experiments (e.g. table of runs, params,
      runtime) via the CLI

Exit criterion: running the same model twice with different parameters produces
two comparable, inspectable tracked experiments.

## Phase 5 — Additional Models, Refactoring, Documentation (not started)

- [ ] Momentum
- [ ] Volatility
- [ ] Z-Score
- [ ] Mean Reversion
- [ ] Revisit `core/` for any generalization the additional models revealed was
      missing (logged in `DESIGN_DECISIONS.md`, not made silently)
- [ ] Documentation pass across the whole repository

Exit criterion: five models, one shared framework, no model-specific logic
leaked into `core/`.

## Explicitly out of scope, always

- Live or simulated trade execution
- Portfolio optimization or capital allocation
- Any claim of financial performance
- Paid APIs, cloud infrastructure, or GPU requirements
