"""Tests for `models.moving_average`.

Per `docs/testing-strategy.md` and `docs/validation.md`: a known-answer test
against a hand computation, explicit edge cases (empty input, insufficient
history, NaNs, a constant series), a no-lookahead test, and a determinism
test. See `research/moving_average/README.md` for the math and assumptions
these tests check against.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from modelforge.models.moving_average import MovingAverageFactor, MovingAverageParams


def _series(values: list[float], n: int | None = None) -> pd.Series:
    n = n if n is not None else len(values)
    index = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.Series(values, index=index)


def test_known_answer_matches_hand_computed_sma() -> None:
    # SMA(3) of [10, 11, 12, 13, 14, 15]:
    #   idx0, idx1: undefined (fewer than 3 observations)
    #   idx2: (10+11+12)/3 = 11
    #   idx3: (11+12+13)/3 = 12
    #   idx4: (12+13+14)/3 = 13
    #   idx5: (13+14+15)/3 = 14
    data = _series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    factor = MovingAverageFactor(window=3)

    result = factor.compute(data, MovingAverageParams(window=3))

    assert math.isnan(result.series.iloc[0])
    assert math.isnan(result.series.iloc[1])
    assert result.series.iloc[2] == 11.0
    assert result.series.iloc[3] == 12.0
    assert result.series.iloc[4] == 13.0
    assert result.series.iloc[5] == 14.0


def test_empty_input_produces_empty_output() -> None:
    data = pd.Series([], index=pd.DatetimeIndex([]), dtype="float64")
    factor = MovingAverageFactor(window=3)

    result = factor.compute(data, MovingAverageParams(window=3))

    assert result.series.empty


def test_input_shorter_than_window_is_entirely_nan() -> None:
    data = _series([1.0, 2.0])
    factor = MovingAverageFactor(window=5)

    result = factor.compute(data, MovingAverageParams(window=5))

    assert len(result.series) == 2
    assert result.series.isna().all()


def test_a_single_nan_propagates_exactly_window_minus_one_steps_forward() -> None:
    # window=3, NaN at position 3. A window needs 3 non-null observations,
    # so every window touching position 3 also comes out NaN: positions
    # 3, 4, and 5 (3 total = the NaN's own position + window-1 = 2 more).
    data = _series([1.0, 2.0, 3.0, np.nan, 5.0, 6.0, 7.0, 8.0])
    factor = MovingAverageFactor(window=3)

    result = factor.compute(data, MovingAverageParams(window=3))

    assert result.series.iloc[2] == pytest.approx(2.0)  # (1+2+3)/3
    assert result.series.iloc[3:6].isna().all()
    assert result.series.iloc[6] == pytest.approx(6.0)  # (5+6+7)/3
    assert result.series.iloc[7] == pytest.approx(7.0)  # (6+7+8)/3


def test_constant_series_averages_to_the_constant() -> None:
    data = _series([5.0, 5.0, 5.0, 5.0, 5.0])
    factor = MovingAverageFactor(window=3)

    result = factor.compute(data, MovingAverageParams(window=3))

    assert result.series.iloc[2:].eq(5.0).all()


def test_does_not_mutate_its_input() -> None:
    data = _series([1.0, 2.0, 3.0, 4.0])
    original = data.copy()
    factor = MovingAverageFactor(window=3)

    factor.compute(data, MovingAverageParams(window=3))

    pd.testing.assert_series_equal(data, original)


def test_no_lookahead() -> None:
    """Perturbing data after index t must not change the output at t."""
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=dates)
    perturbed = pd.Series([1.0, 2.0, 3.0, 4.0, 999.0], index=dates)

    factor = MovingAverageFactor(window=3)
    params = MovingAverageParams(window=3)

    result = factor.compute(data, params)
    perturbed_result = factor.compute(perturbed, params)

    pd.testing.assert_series_equal(result.series.iloc[:4], perturbed_result.series.iloc[:4])


def test_running_twice_is_bit_identical() -> None:
    data = _series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    factor = MovingAverageFactor(window=3)
    params = MovingAverageParams(window=3)

    first = factor.compute(data, params)
    second = factor.compute(data, params)

    pd.testing.assert_series_equal(first.series, second.series)


def test_rejects_non_positive_window_param() -> None:
    with pytest.raises(ValidationError):
        MovingAverageParams(window=0)


def test_rejects_non_positive_window_at_construction() -> None:
    with pytest.raises(ValueError, match="window must be positive"):
        MovingAverageFactor(window=0)


def test_rejects_params_window_mismatched_with_construction() -> None:
    factor = MovingAverageFactor(window=3)
    data = _series([1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="window=3"):
        factor.compute(data, MovingAverageParams(window=5))


def test_describe_mentions_the_window() -> None:
    factor = MovingAverageFactor(window=20)
    assert "20" in factor.describe()
