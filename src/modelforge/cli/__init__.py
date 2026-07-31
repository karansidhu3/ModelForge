"""Command-line interface: a thin Typer-based shell over `core` and
`experiments`.

Contains argument parsing and output formatting only — no business logic.
See ARCHITECTURE.md and DESIGN_DECISIONS.md (DD-005).

Contents:
    main.py   Typer `app`, exposed as the `modelforge` console script.
              Currently one command group: `experiments list`, summarizing
              tracked runs (see docs/experiment-tracking.md). There is no
              `run` command yet — running a model is direct Python/pytest
              today (see examples/); a CLI `run` command needs a way to
              resolve a model name to a `Factor` implementation, which DD-008
              deliberately deferred until a real caller needs it.
"""
