"""Experiment tracking: lightweight, local recording of what a pipeline run
did, with what parameters, against what data, producing what output.

Has no knowledge of what a factor computes — see ARCHITECTURE.md. Local-file
based; see DESIGN_DECISIONS.md (DD-003) for why this isn't a database, at
least initially.

Contents:
    tracker.py     Writes/reads one JSON record per run under experiments/runs/
    benchmark.py   Measures a Factor's actual compute runtime, repeated —
                   "record actual runtime characteristics, don't guess"
                   (CLAUDE.md).
"""
