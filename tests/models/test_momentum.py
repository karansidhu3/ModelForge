"""Tests for `models.momentum`.

See `research/momentum/README.md` for the math and the documented
NaN-propagation shape (two isolated invalidated points, not a range) this
model has, in contrast to a rolling-window model like moving average.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from modelforge.core.config import ValidationConfig
from modelforge.core.validation import validate_result
from modelforge.models.momentum import MomentumFactor, MomentumParams


def _series(values: list[float], n: int | None = None) -> pd.Series:
    n = n if n is not None else len(values)
    index = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.Series(values, index=index)


def test_known_answer_matches_hand_computed_momentum() -> None:
    # M(lookback=2) of [10, 12, 15, 11, 14, 18, 20]:
    #   idx0, idx1: undefined
    #   idx2: 15 - 10 = 5
    #   idx3: 11 - 12 = -1
    #   idx4: 14 - 15 = -1
    #   idx5: 18 - 11 = 7
    #   idx6: 20 - 14 = 6
    data = _series([10.0, 12.0, 15.0, 11.0, 14.0, 18.0, 20.0])
    factor = MomentumFactor(lookback=2)

    result = factor.compute(data, MomentumParams(lookback=2))

    assert math.isnan(result.series.iloc[0])
    assert math.isnan(result.series.iloc[1])
    assert result.series.iloc[2] == 5.0
    assert result.series.iloc[3] == -1.0
    assert result.series.iloc[4] == -1.0
    assert result.series.iloc[5] == 7.0
    assert result.series.iloc[6] == 6.0


def test_empty_input_produces_empty_output() -> None:
    data = pd.Series([], index=pd.DatetimeIndex([]), dtype="float64")
    factor = MomentumFactor(lookback=2)

    result = factor.compute(data, MomentumParams(lookback=2))

    assert result.series.empty


def test_input_shorter_than_required_history_is_entirely_nan() -> None:
    data = _series([1.0, 2.0])
    factor = MomentumFactor(lookback=5)

    result = factor.compute(data, MomentumParams(lookback=5))

    assert len(result.series) == 2
    assert result.series.isna().all()


def test_a_nan_invalidates_exactly_two_isolated_output_points() -> None:
    # lookback=3, NaN at position 3.
    #   idx3: x3 - x0 = NaN - 1        -> NaN (own position missing)
    #   idx6: x6 - x3 = 7 - NaN        -> NaN (lookback reference missing)
    # idx4 and idx5 are unaffected, unlike a rolling window's contiguous
    # propagation.
    data = _series([1.0, 2.0, 3.0, np.nan, 5.0, 6.0, 7.0, 8.0])
    factor = MomentumFactor(lookback=3)

    result = factor.compute(data, MomentumParams(lookback=3))

    assert math.isnan(result.series.iloc[3])
    assert result.series.iloc[4] == pytest.approx(3.0)  # 5 - 2
    assert result.series.iloc[5] == pytest.approx(3.0)  # 6 - 3
    assert math.isnan(result.series.iloc[6])
    assert result.series.iloc[7] == pytest.approx(3.0)  # 8 - 5


def test_nan_propagation_at_the_lookback_offset_triggers_a_benign_validation_warning() -> None:
    """See research/momentum/README.md: the validation heuristic only checks
    same-index input, so it flags the lookback-side NaN even though it's
    expected, not a defect."""
    data = _series([1.0, 2.0, 3.0, np.nan, 5.0, 6.0, 7.0, 8.0])
    factor = MomentumFactor(lookback=3)
    result = factor.compute(data, MomentumParams(lookback=3))

    report = validate_result(data, result, factor, ValidationConfig())

    assert report.passed  # a warning, not an error
    assert len(report.warnings) == 1
    assert report.warnings[0].check == "nan_propagation"


def test_does_not_mutate_its_input() -> None:
    data = _series([1.0, 2.0, 3.0, 4.0])
    original = data.copy()
    factor = MomentumFactor(lookback=2)

    factor.compute(data, MomentumParams(lookback=2))

    pd.testing.assert_series_equal(data, original)


def test_no_lookahead() -> None:
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=dates)
    perturbed = pd.Series([1.0, 2.0, 3.0, 4.0, 999.0], index=dates)

    factor = MomentumFactor(lookback=2)
    params = MomentumParams(lookback=2)

    result = factor.compute(data, params)
    perturbed_result = factor.compute(perturbed, params)

    pd.testing.assert_series_equal(result.series.iloc[:4], perturbed_result.series.iloc[:4])


def test_running_twice_is_bit_identical() -> None:
    data = _series([10.0, 12.0, 15.0, 11.0, 14.0])
    factor = MomentumFactor(lookback=2)
    params = MomentumParams(lookback=2)

    first = factor.compute(data, params)
    second = factor.compute(data, params)

    pd.testing.assert_series_equal(first.series, second.series)


def test_rejects_non_positive_lookback_param() -> None:
    with pytest.raises(ValidationError):
        MomentumParams(lookback=0)


def test_rejects_non_positive_lookback_at_construction() -> None:
    with pytest.raises(ValueError, match="lookback must be positive"):
        MomentumFactor(lookback=0)


def test_rejects_params_lookback_mismatched_with_construction() -> None:
    factor = MomentumFactor(lookback=2)
    data = _series([1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="lookback=2"):
        factor.compute(data, MomentumParams(lookback=5))


def test_describe_mentions_the_lookback() -> None:
    factor = MomentumFactor(lookback=10)
    assert "10" in factor.describe()
