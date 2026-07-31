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

---

*(Add new entries below this line as decisions are made in later phases.)*
