"""Command-line interface: a thin Typer-based shell over `core`.

Contains argument parsing only — no business logic. See ARCHITECTURE.md and
DESIGN_DECISIONS.md (DD-005). Implementation lands in Phase 2 (see
ROADMAP.md).

Planned contents:
    main.py   Typer `app`, exposed as the `modelforge` console script
"""
