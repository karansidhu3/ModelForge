"""Core orchestration: the Factor interface, run configuration, the execution
pipeline, and the validation framework.

This package has no knowledge of any specific model — see ARCHITECTURE.md for
why that boundary is enforced.

Contents:
    config.py      Pydantic run-configuration schema
    factor.py      The `Factor` interface (see docs/factor-interface.md)
    pipeline.py    Config -> load data -> run factor -> validate -> record
    validation.py  The runtime validation framework (see docs/validation.md)

Experiment recording (the last pipeline stage) is a no-op stub here; real
tracking is Phase 4 scope (see ROADMAP.md).
"""
