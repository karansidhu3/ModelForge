# ModelForge

ModelForge is an engineering framework for translating quantitative research into
reliable, testable, and reproducible software. It exists to practice — and
demonstrate — the discipline of turning a mathematical idea into production-quality
code, not to generate trading signals or investment advice.

## What this is

A small internal platform, modeled loosely on how a research-engineering team at an
investment firm would structure their tooling: a common interface for defining a
model ("factor"), a pipeline that runs it against data, a validation layer that
distrusts every implementation until it's proven correct, and a lightweight
experiment tracker that makes every run reproducible.

## What this is not

- Not a trading bot, and it will never place or simulate a live trade.
- Not an alpha-generation or portfolio-optimization system.
- Not a claim of financial performance of any kind.

The models implemented here (moving average, momentum, volatility, z-score, mean
reversion) are simple and well-published on purpose. The interesting engineering
problem isn't inventing a clever model — it's building the scaffolding that makes
*any* model correct, testable, and trustworthy.

## Why this exists

Quantitative research code has a reputation for being fragile: notebooks full of
unvalidated assumptions, results nobody can reproduce six months later, and "it
worked on my machine." ModelForge is the opposite of that on purpose. Every model
that enters this repository goes through the same pipeline — research, plain-English
explanation, math, implementation, validation, tests, benchmarks, tracked
experiments, documentation — and nothing skips validation.

See [`CLAUDE.md`](./CLAUDE.md) for the engineering rules this repository holds
itself to, and [`ARCHITECTURE.md`](./ARCHITECTURE.md) for how the pieces fit
together.

## Repository layout

```
modelforge/
├── README.md              This file
├── CLAUDE.md               Engineering constitution — rules for all future work
├── ARCHITECTURE.md         System design and module responsibilities
├── ROADMAP.md              Phased development plan and current status
├── DESIGN_DECISIONS.md     Why things are built the way they are (ADR-style log)
├── CONTRIBUTING.md         How to add a new model to the framework
├── LICENSE
├── pyproject.toml
├── requirements-dev.txt
├── docs/                   Deep-dive documentation (validation, tracking, etc.)
├── research/               One folder per model: paper notes, math, assumptions
├── examples/               Runnable end-to-end examples, one per model
├── tests/                  Test suite, mirrors src/modelforge/
└── src/modelforge/         The framework itself
    ├── core/                Factor interface, config, pipeline, validation
    ├── data/                Local/free data loaders (CSV, Yahoo Finance, FRED)
    ├── models/              Concrete Factor implementations (five: moving
    │                        average, momentum, volatility, z-score, mean
    │                        reversion)
    ├── experiments/         Local experiment tracking + benchmarking harness
    └── cli/                 Typer-based command-line entrypoint
```

## Status

This repository has completed **Phase 5 — Additional Models, Refactoring,
Documentation**, the last phase on the roadmap: all five planned models
(moving average, momentum, volatility, z-score, mean reversion) are
implemented, validated, tested, benchmarked, and documented, each through
the same core execution engine with no model-specific logic in `core/`. See
[`ROADMAP.md`](./ROADMAP.md) for the phase-by-phase history and what
"done" means at each stage.

## Requirements

- Python 3.11+
- No paid APIs, no cloud services, no GPU. Everything here runs on a laptop.

## Quickstart

```bash
pip install -e ".[dev]"
pytest
python examples/moving_average.py
modelforge experiments list
```

Every model in `src/modelforge/models/` has a runnable example in
`examples/` (`moving_average.py`, `momentum.py`, `volatility.py`,
`z_score.py`, `mean_reversion.py`) — each loads a small synthetic price
series, runs that model through the pipeline, prints the validated result,
and records it as a tracked experiment. `modelforge experiments list`
summarizes every run recorded so far.
