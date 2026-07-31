# CLAUDE.md — Engineering Constitution for ModelForge

This document governs how work gets done in this repository. It applies to every
contributor, human or AI. If a change conflicts with this document, the change is
wrong until this document is updated on purpose — it doesn't get quietly
overridden.

## Mission

Build an engineering framework that turns published quantitative research into
correct, tested, reproducible software. Every decision in this repository is
judged against that mission, not against whether it would make a better trading
system.

## Non-goals (do not drift toward these)

- This is not a trading bot and never executes or simulates trades.
- This is not an alpha-generation or portfolio-optimization project.
- No claim of financial performance is ever made in code, docs, comments, or
  commit messages.

If a proposed feature's main value is "this would make the models more
profitable," it does not belong here. If its value is "this would make the
platform more correct, more testable, or more explainable," it does.

## Project philosophy

1. **Assume every implementation is wrong until proven otherwise.** Validation is
   not a phase that happens after the "real" work — it *is* the real work.
2. **Explicit over clever.** A junior engineer six months from now should be able
   to read any module and understand what it does without reverse-engineering
   intent.
3. **Composition over inheritance.** Deep class hierarchies are a smell here.
   Prefer small interfaces and objects that compose.
4. **One responsibility per module.** If you're explaining a module with "and,"
   it's two modules.
5. **Reproducibility is a requirement, not a nice-to-have.** If a result can't be
   regenerated from a config file and a commit hash, it doesn't count as a
   result.

## Coding standards

- Python 3.11+, fully type-hinted. No untyped public functions.
- Small functions with a single, nameable purpose. If a function needs a comment
  to explain *what* it does (as opposed to *why*), it should probably be split
  or renamed.
- Public interfaces are defined with abstract base classes or `Protocol`s and
  documented with docstrings that describe the contract, not just the
  parameters.
- Configuration is defined with Pydantic models — no bare dicts passed around as
  implicit config.
- No global mutable state. Pipelines and factors are constructed with their
  dependencies, not reaching out to globals.
- Prefer `pathlib.Path` over string paths.
- Format with `black`, lint with `ruff`, type-check with `mypy`. All three must
  pass before a change is considered done.

## Documentation standards

- Every module has a module-level docstring explaining its responsibility and
  what it explicitly does *not* do.
- Every new model gets a corresponding folder under `research/` before its code
  is written — the math comes first, the code is a translation of it.
- Documentation explains *why*, not just *what*. "We use Pydantic for config
  validation because malformed experiment parameters should fail at load time,
  not three hours into a benchmark run" is a good doc sentence. "This class
  loads config" is not.
- If a design decision was non-obvious or had real trade-offs, it goes in
  `DESIGN_DECISIONS.md`, not just in a code comment that will get lost.

## Testing philosophy

- Every model ships with tests before it's considered implemented, not after.
- Tests are deterministic. No test depends on live network calls, wall-clock
  time, or unseeded randomness.
- Tests demonstrate correctness against known inputs/outputs (ideally taken
  directly from the source research, a textbook worked example, or hand
  computation), not just "the function ran without raising."
- Edge cases are explicit test cases, not comments saying "should probably
  handle this."
- Coverage is a signal, not a goal. A model with 100% coverage and no test
  against a known numerical result has not been validated.

## Architecture rules

- `core/` defines interfaces and orchestration (the `Factor` contract, the
  pipeline, the config schema, the validation framework). It has no knowledge of
  any specific model.
- `data/` is the only place that talks to the outside world (Yahoo Finance, CSV
  files, FRED). Nothing else does I/O against external sources directly.
- `experiments/` owns run tracking and has no knowledge of what a factor
  computes — it only knows how to record that a run happened, with what
  parameters, and what it produced.
- `cli/` is a thin layer over `core/`. It contains no business logic — only
  argument parsing and calls into the library.
- Individual models live outside `core/`, implement the `Factor` interface, and
  are free to be as specific as they need to be. `core/` should never need to
  change to accommodate a new model.

## Validation requirements

Every model must include, before it is considered done:

- At least one test against a known input/output pair from the source material.
- Explicit handling (and a test) for the obvious edge cases: empty input,
  insufficient history for the required window, NaNs in the input series.
- A written statement of assumptions in its `research/<model>/` folder (e.g.,
  "assumes evenly spaced trading-day observations; does not adjust for
  corporate actions").
- Where the calculation has intermediate steps worth inspecting, those
  intermediate values should be inspectable (returned or logged), not buried
  inside a single opaque function.

## Design principles

- Avoid premature optimization. Correctness and clarity come first; benchmark
  before optimizing, and only optimize what the benchmark says is slow.
- Avoid unnecessary abstraction. Don't build a plugin system for three models.
  Build the third abstraction when the third concrete need for it shows up, not
  before.
- Minimal coupling, high cohesion. A change to one model should never require
  touching another model.
- No paid APIs, no cloud dependencies, no GPU requirements. Everything runs on a
  laptop, forever.

## Expected workflow for new work

Every model follows the same pipeline, in order, with no steps skipped:

1. Research — read the source material.
2. Plain-English explanation — write it in `research/<model>/README.md` before
   writing code.
3. Mathematical description — the formal definition, in the same file.
4. Implementation — a `Factor` implementation in `src/modelforge/`.
5. Validation — known-answer tests and edge cases.
6. Testing — the full pytest suite for the module, deterministic.
7. Benchmarking — runtime characteristics recorded, not guessed at.
8. Experiment tracking — at least one tracked run demonstrating the model
   executing end-to-end through the pipeline.
9. Documentation — the model is added to any relevant docs and its
   `research/<model>/README.md` is complete.

## Definition of Done for a new feature

A feature (a new model, a new pipeline capability, a new CLI command) is done
when all of the following are true:

- [ ] Type-hinted, formatted, linted, and type-checked cleanly.
- [ ] Has tests that would fail if the implementation were subtly wrong, not
      just tests that would fail if it crashed.
- [ ] Has documentation explaining why it exists and how it fits the
      architecture.
- [ ] Introduces no new external service, paid API, or cloud dependency.
- [ ] Does not weaken any existing validation, test, or documentation.
- [ ] Reviewed against the non-goals above — it makes the platform more
      correct/testable/explainable, not more "profitable."

If any box is unchecked, the feature is not done, regardless of whether it
"works."
