"""Tests for `experiments.benchmark`.

Timing tests can't assert exact wall-clock values deterministically, so
these check structural properties instead: call counts, bounds, and
validation — not "how fast," which is inherently non-deterministic.
"""

from __future__ import annotations

import pandas as pd
import pytest

from modelforge.core.factor import FactorParams, FactorResult
from modelforge.experiments.benchmark import benchmark_factor
from tests.conftest import ToyRollingSumFactor, ToySumParams


class _CountingFactor:
    name = "counting"
    required_history = 1

    def __init__(self) -> None:
        self.call_count = 0

    def compute(self, data: pd.Series, params: FactorParams) -> FactorResult:
        self.call_count += 1
        return FactorResult(series=data.copy())

    def describe(self) -> str:
        return "Counts how many times compute() was called."


def _data(n: int = 50) -> pd.Series:
    return pd.Series(range(n), index=pd.date_range("2024-01-01", periods=n, freq="D"), dtype=float)


def test_calls_compute_exactly_repeats_times() -> None:
    factor = _CountingFactor()
    benchmark_factor(factor, ToySumParams(window=1), _data(), repeats=7)
    assert factor.call_count == 7


def test_result_bounds_are_consistent() -> None:
    factor = ToyRollingSumFactor(window=3)
    result = benchmark_factor(factor, ToySumParams(window=3), _data(), repeats=5)

    assert result.min_seconds <= result.mean_seconds <= result.max_seconds
    assert result.min_seconds <= result.median_seconds <= result.max_seconds
    assert result.min_seconds >= 0.0


def test_records_factor_name_and_observation_count() -> None:
    factor = ToyRollingSumFactor(window=3)
    data = _data(123)

    result = benchmark_factor(factor, ToySumParams(window=3), data, repeats=3)

    assert result.factor_name == "toy_rolling_sum"
    assert result.n_observations == 123
    assert result.repeats == 3


def test_rejects_non_positive_repeats() -> None:
    factor = ToyRollingSumFactor(window=3)
    with pytest.raises(ValueError, match="repeats must be positive"):
        benchmark_factor(factor, ToySumParams(window=3), _data(), repeats=0)
