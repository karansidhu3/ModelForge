"""Experiment tracking: lightweight, local recording of what a pipeline run
did, with what parameters, against what data, producing what output.

Has no knowledge of what a factor computes — see ARCHITECTURE.md. Local-file
based; see DESIGN_DECISIONS.md (DD-003) for why this isn't a database, at
least initially. Implementation lands in Phase 4 (see ROADMAP.md).

Planned contents:
    tracker.py   Writes/reads one JSON record per run under experiments/runs/
"""
