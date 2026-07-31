# Design Decisions

A running log of non-obvious decisions and the trade-offs behind them. Code
comments explain *what*; this file explains *why*, so the reasoning survives
even when the code that prompted it changes. New entries go at the bottom, in
the same format.

---

### DD-001: Composition over inheritance for models

**Decision:** Models implement a single flat `Factor` interface rather than
inheriting from a hierarchy of increasingly specific base classes.

**Why:** A hierarchy (`BaseFactor` → `TimeSeriesFactor` → `RollingWindowFactor`
→ ...) looks elegant with two models and becomes a liability by the fourth, once
one model needs to deviate from an assumption baked into an ancestor class.
A flat interface plus shared, optional utility functions keeps each model's
behavior fully visible in its own file.

**Trade-off accepted:** Some duplication across models (e.g., each may
independently call the same rolling-window helper) in exchange for no model
ever being constrained by inherited behavior it didn't choose.

---

### DD-002: Pydantic for configuration, not raw dicts or YAML-as-dict

**Decision:** Every run is described by a Pydantic model, not a bare
dictionary parsed from YAML.

**Why:** Malformed configuration should fail loudly at load time — wrong type,
missing field, out-of-range parameter — not silently propagate into a
benchmark run and produce a confusing numerical result an hour later.
Pydantic gives that validation for free and makes the config schema
self-documenting.

**Trade-off accepted:** A small amount of upfront ceremony (defining a model
class) for every new config shape, versus the flexibility of a raw dict.

---

### DD-003: Experiment tracking is local files, not a database

**Decision:** Experiment records are written as local files (one per run),
not stored in SQLite or any external database, at least through Phase 4.

**Why:** The stated constraint is zero infrastructure cost and everything
runnable on a laptop. A database is the right answer once query patterns
across hundreds of runs demand it — introducing one before that need is
demonstrated would be exactly the "premature abstraction" this project's
philosophy warns against.

**Trade-off accepted:** No efficient querying across many runs yet. If Phase 4
benchmarking shows this is actually painful, SQLite is the documented fallback
(see `docs/experiment-tracking.md`), not a rewrite.

---

### DD-004: `data/` is the only module permitted to do I/O against external
sources

**Decision:** Yahoo Finance, FRED, and file-system CSV access are isolated
entirely inside `data/`. No other module — including model implementations —
is allowed to reach out to the network or filesystem directly.

**Why:** This is what makes every other layer testable with deterministic,
offline fixtures. It also means "Yahoo Finance changed their API" is a
one-file problem, not a codebase-wide one.

**Trade-off accepted:** An extra indirection layer even for the simplest CSV
read, in exchange for testability everywhere else.

---

### DD-005: CLI is a thin shell over the library, never a place for logic

**Decision:** `cli/` contains argument parsing and calls into `core/` — no
business logic lives there.

**Why:** Logic in a CLI handler is logic that can only be tested by invoking
the CLI, which is slower and more brittle than testing the underlying function
directly. Keeping the CLI thin means the library is usable (and tested)
independent of how it's invoked.

**Trade-off accepted:** None significant — this one's close to free.

---

### DD-006: Validation is a first-class layer in `core/`, not scattered
assertions

**Decision:** A dedicated validation framework sits between "a model produced
a result" and "that result is trusted," rather than relying on ad hoc
assertions inside each model.

**Why:** The project's stated premise is that implementations are assumed
wrong until proven otherwise. A single, consistent validation layer means
every model gets the same baseline checks (shape, NaN handling, known-value
spot checks where configured) rather than whatever a given model's author
remembered to assert.

**Trade-off accepted:** An extra layer to design carefully up front, in
exchange for consistent guarantees across every current and future model.

---

### DD-007: Pandas as the default dataframe library, Polars deferred

**Decision:** Phase 2 and the first models use Pandas. Polars is not ruled
out, but it isn't adopted until there's a concrete performance or ergonomics
reason to.

**Why:** Pandas is the default that every downstream reader (and most
published research code) already assumes. Introducing Polars without a
demonstrated need would be optimizing before benchmarking — which
`CLAUDE.md` explicitly rules out.

**Trade-off accepted:** Slower operations on very large datasets than Polars
would give, which is irrelevant at this project's scale.

---

### DD-008: Factor dispatch is direct injection, not a name-based registry

**Decision:** `core/pipeline.py` receives the `Factor` instance and its
validated `FactorParams` instance directly as arguments from the caller. It
never resolves a model from a string name. `RunConfig` still records
`model_name` and a `params` dict, but purely as descriptive metadata for
reproducibility and experiment tracking — not as something the pipeline
dispatches on.

**Why:** A name → implementation registry (an import-time registration
convention, an entry-points mechanism, or a hardcoded dispatch table) is
exactly the kind of plugin infrastructure `CLAUDE.md` warns against building
before a third concrete need demonstrates it's necessary. Phase 2 has no CLI
and no model beyond a hand-written toy — there is no caller yet that only has
a string and needs to resolve it to a class. Direct injection is the simplest
thing that satisfies the exit criterion (a toy `Factor` running end-to-end
through the pipeline) without inventing a discovery mechanism nothing yet
exercises.

**Trade-off accepted:** When the CLI is built (Phase 2+ per `ARCHITECTURE.md`,
or later), something will need to map a `--model` string to a `Factor` class.
That's deferred to whenever the CLI is actually implemented, at which point
the registry design can be made with a real caller driving the requirements,
rather than guessed at now. Revisit this decision at that point.

**Update (Phase 4):** `cli/main.py` now exists, but only for reporting
(`modelforge experiments list`, reading already-recorded run files) — it
never runs a model, so it still doesn't need to resolve a name to a `Factor`
class. The registry question above remains open, deferred until a `run`
command is actually built.

---

### DD-009: Experiment records store a compact output summary, not the full
result series

**Decision:** `ExperimentRecord.output_summary` holds a handful of scalars
(observation count, valid-value count, first/last valid index and value) —
not the `Factor`'s full output series.

**Why:** `docs/experiment-tracking.md` asks for records that are "trivial to
load into a Pandas DataFrame for comparison" and human-diffable. A full
series nested inside every run's JSON file works against both: it makes each
file's size proportional to the dataset rather than roughly constant, and a
column of nested per-run series doesn't flatten into a comparison table the
way scalar summary stats do. Full-fidelity reproduction of a result doesn't
require persisting it either — `docs/reproducibility.md`'s own definition of
reproducibility is "config plus commit hash, re-run it," not "read the
output back from a log."

**Trade-off accepted:** Inspecting a past run's output in full means
re-running it (cheap, for the model sizes this project deals with — see
`research/moving_average/README.md`'s performance numbers), not just reading
the record. If a future need genuinely requires full-fidelity output
persistence, that's a real design conversation to have then, not something
to build speculatively now.

---

### DD-010: Commit-hash capture fails soft, not loudly

**Decision:** `experiments/tracker.py`'s `_current_commit` returns
`(None, None)` when the code isn't running inside a git repository (or `git`
isn't available), rather than raising and aborting the run.

**Why:** This breaks from this project's general "fail loudly" posture on
purpose. Commit provenance is auxiliary metadata *about* a run, not part of
its numerical result — a missing commit hash doesn't make a run's output
wrong, it just weakens how precisely a future reader can pin down what code
produced it. `docs/reproducibility.md` already has precedent for stating a
limitation honestly rather than pretending it doesn't exist (the Yahoo
Finance non-reproducibility note) or, worse, blocking otherwise-valid work
over it. A source tree extracted from an archive, with no `.git` directory,
should still be able to run the pipeline and get a validated result — it
just won't get a commit hash attached to the experiment record.

**Trade-off accepted:** A run recorded outside a git checkout has strictly
weaker reproducibility provenance (config only, no commit pin). This is
recorded honestly (`commit_hash: null` in the JSON) rather than hidden.

---

*(Add new entries below this line as decisions are made in later phases.)*
