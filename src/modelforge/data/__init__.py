"""Data loading: the only package in ModelForge permitted to perform I/O
against external sources (CSV files, Yahoo Finance, FRED).

See ARCHITECTURE.md and DESIGN_DECISIONS.md (DD-004) for why external I/O is
isolated here.

Contents:
    loaders.py   CSV loader (implemented). Yahoo Finance and FRED loaders,
                 returning the same validated series format, are not yet
                 implemented — out of scope for Phase 2 (see ROADMAP.md).
"""
