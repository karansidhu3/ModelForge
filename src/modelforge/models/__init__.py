"""Concrete `Factor` implementations.

Each model is a self-contained module implementing `core.factor.Factor` — it
knows nothing about the pipeline, the CLI, or experiment tracking, and
`core/` knows nothing about any module in this package. See ARCHITECTURE.md
("Model packages — concrete Factor implementations") for why that boundary
holds in both directions.

Every model here follows the same workflow before it lands: research and math
first, written up in `research/<model>/README.md`, then implementation, then
validation and tests. See CONTRIBUTING.md.

Contents:
    moving_average.py   The simple moving average (Phase 3's first model).
"""
