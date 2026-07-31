"""Shared pytest fixtures for the ModelForge test suite.

Includes `ToyRollingSumFactor`: a minimal, hand-computable `Factor`
implementation used only to exercise the Phase 2 pipeline end-to-end. It is
deliberately not a real model — real models (moving average, etc.) start in
Phase 3 per ROADMAP.md and go through the full research-first workflow in
CONTRIBUTING.md. This toy factor's "math" is simple enough to hand-verify
directly in test assertions.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from modelforge.core.factor import FactorParams, FactorResult

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class ToySumParams(FactorParams):
    """Parameters for `ToyRollingSumFactor`."""

    window: int


class ToyRollingSumFactor:
    """Rolling sum of the last `window` observations.

    Conforms to `core.factor.Factor` structurally (duck-typed, checked via
    `isinstance` against the `runtime_checkable` Protocol in
    `test_factor.py`). NaN-in-window semantics follow `pandas.Series.rolling`
    directly: a window containing a NaN only produces NaN once fewer than
    `window` non-null observations remain in it.
    """

    name = "toy_rolling_sum"

    def __init__(self, window: int) -> None:
        self.required_history = window

    def compute(self, data: pd.Series, params: FactorParams) -> FactorResult:
        assert isinstance(params, ToySumParams)
        series = data.rolling(window=params.window, min_periods=params.window).sum()
        series.name = "toy_rolling_sum"
        return FactorResult(series=series)

    def describe(self) -> str:
        return "Rolling sum of the last `window` observations (toy factor, pipeline tests only)."


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR
