# Contributing

This is a personal engineering project, but it holds itself to the standard of
a repository other engineers would need to maintain. These are the rules for
adding anything to it — see `CLAUDE.md` for the full underlying philosophy.

## Adding a new model

Every model follows the same nine-step pipeline, in order. Do not skip a step,
and do not write implementation code before the research and math steps exist
in writing.

1. **Research** — read and understand the source material for the model.
2. **Plain-English explanation** — write it in `research/<model>/README.md`
   before any code exists. If you can't explain it simply, you don't
   understand it well enough to implement it correctly.
3. **Mathematical description** — the formal definition, in the same file.
4. **Implementation** — implement the `Factor` interface
   (see `docs/factor-interface.md`) in its own module. Type-hinted, small
   functions, no logic borrowed from a base class it doesn't need.
5. **Validation** — known-input/known-output test cases (from the source
   material or hand computation), plus explicit edge cases: empty input,
   insufficient window/history, NaNs.
6. **Testing** — the full pytest suite for the model passes, deterministically,
   with no network dependency.
7. **Benchmarking** — record actual runtime characteristics; don't guess.
8. **Experiment tracking** — produce at least one tracked run of the model
   through the full pipeline.
9. **Documentation** — `research/<model>/README.md` is complete, and the model
   is referenced anywhere else it's relevant (e.g. `ROADMAP.md`).

## Pull request / change checklist

Before considering a change finished:

- [ ] `black`, `ruff`, and `mypy` all pass cleanly.
- [ ] New code is fully type-hinted.
- [ ] Tests exist and would fail if the logic were subtly wrong (not just if it
      crashed).
- [ ] No new paid API, cloud dependency, or GPU requirement was introduced.
- [ ] `core/`, `data/`, `experiments/`, and `cli/` were not modified to
      special-case a single model, unless the change is logged in
      `DESIGN_DECISIONS.md` as a genuine interface generalization.
- [ ] Documentation was updated in the same change, not deferred.

This mirrors the Definition of Done in `CLAUDE.md` — that document is the
source of truth if the two ever drift.

## Style

- Python 3.11+, fully typed.
- Small, single-purpose functions. Composition over inheritance.
- Explicit over clever. Optimize for the next reader, not for cleverness.
- Formatting and linting are enforced, not a matter of taste:
  `black .`, `ruff check .`, `mypy src/`.

## What not to add

If you're unsure whether something belongs here, check it against the
non-goals in `CLAUDE.md`: nothing that executes or simulates trades, nothing
aimed at portfolio optimization, no claims of financial performance, no paid
or cloud dependencies. If a change's main justification is "this would make
the models perform better," it's out of scope — this repository optimizes for
correctness and clarity, not returns.
