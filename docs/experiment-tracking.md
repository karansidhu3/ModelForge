# Experiment Tracking

## Purpose

Every run of a model through the pipeline should be reconstructable later:
what was run, with what parameters, against what data, producing what result,
and how long it took. Without this, "let's compare this run to last week's" is
guesswork.

## What gets recorded per run

- **Run ID** — a unique identifier for the run.
- **Timestamp** — when the run started.
- **Parameters** — the full config used, including model name and all
  parameter values.
- **Dataset** — which dataset was used (source, symbol/series, date range).
- **Model** — which `Factor` implementation and version.
- **Runtime** — wall-clock duration of the run.
- **Commit hash** — the git commit the code was at when the run happened
  (planned; see below).
- **Outputs** — the result produced, or a reference to where it's stored if
  it's large.

## Storage format

Local files, one per run, under `experiments/runs/` (git-ignored — see
`.gitignore`; experiment outputs are regenerable artifacts, not source).
Each run is a single JSON file named by its run ID and timestamp, containing
the fields above. This is intentionally the simplest thing that could work:

- No database to set up or migrate.
- Human-readable and diffable.
- Trivial to load into a Pandas DataFrame for comparison (`pd.read_json` over
  the directory) once there are enough runs to want that.

See `DESIGN_DECISIONS.md`, DD-003, for why this is local files rather than
SQLite from the start, and what would justify moving to SQLite later
(specifically: if querying across hundreds of runs becomes a real bottleneck
in Phase 4's reporting work — not before).

## Commit hash: planned, not yet wired up

The spec calls for recording the commit hash a run was executed at, which
requires the repository to actually be a git repository with commits to
reference. This field is part of the record schema from the start, but its
population is deferred until there's a real git history to read from —
tracked in `ROADMAP.md` Phase 4.

## What this is not

Not a metrics dashboard, not a leaderboard, not an MLOps platform. It's a
paper trail. The goal is "I can find out exactly what produced this number
six months from now," not "I have a UI for comparing hyperparameter sweeps."
If that need materializes, it's a Phase 5+ conversation, not a Phase 1
commitment.
