"""Tests for `models.z_score`.

See `research/z_score/README.md` for the math and the documented
zero-variance (0/0 -> NaN) behavior this model deliberately doesn't guard
against.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from modelforge.models.z_score import ZScoreFactor, ZScoreParams


def _series(values: list[float], n: int | None = None) -> pd.Series:
    n = n if n is not None else len(values)
    index = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.Series(values, index=index)


def test_known_answer_matches_hand_computed_z_score_for_an_arithmetic_run() -> None:
    # For any length-3 arithmetic progression [a-d, a, a+d] (d != 0),
    # mean=a and std(ddof=1)=sqrt((d^2+d^2)/2)=|d|, so z at the last point is
    # always exactly (a+d-a)/d = 1.0 — an exact, hand-verifiable identity.
    data = _series([1.0, 2.0, 3.0, 4.0, 5.0])
    factor = ZScoreFactor(window=3)

    result = factor.compute(data, ZScoreParams(window=3))

    assert math.isnan(result.series.iloc[0])
    assert math.isnan(result.series.iloc[1])
    assert result.series.iloc[2] == pytest.approx(1.0)
    assert result.series.iloc[3] == pytest.approx(1.0)
    assert result.series.iloc[4] == pytest.approx(1.0)


def test_known_answer_matches_hand_computed_z_score_for_a_non_uniform_window() -> None:
    # data=[2, 4, 9]: mean=5, variance(ddof=1)=((2-5)^2+(4-5)^2+(9-5)^2)/2
    #   = (9+1+16)/2 = 13, std=sqrt(13). z = (9-5)/sqrt(13) = 4/sqrt(13).
    data = _series([2.0, 4.0, 9.0])
    factor = ZScoreFactor(window=3)

    result = factor.compute(data, ZScoreParams(window=3))

    assert result.series.iloc[2] == pytest.approx(4.0 / math.sqrt(13.0))


def test_exposes_rolling_mean_and_rolling_std_as_intermediates() -> None:
    data = _series([2.0, 4.0, 9.0])
    factor = ZScoreFactor(window=3)

    result = factor.compute(data, ZScoreParams(window=3))

    assert result.intermediates["rolling_mean"].iloc[2] == pytest.approx(5.0)
    assert result.intermediates["rolling_std"].iloc[2] == pytest.approx(math.sqrt(13.0))


def test_empty_input_produces_empty_output() -> None:
    data = pd.Series([], index=pd.DatetimeIndex([]), dtype="float64")
    factor = ZScoreFactor(window=3)

    result = factor.compute(data, ZScoreParams(window=3))

    assert result.series.empty


def test_input_shorter_than_window_is_entirely_nan() -> None:
    data = _series([1.0, 2.0])
    factor = ZScoreFactor(window=5)

    result = factor.compute(data, ZScoreParams(window=5))

    assert len(result.series) == 2
    assert result.series.isna().all()


def test_constant_series_has_zero_variance_and_produces_nan() -> None:
    data = _series([5.0, 5.0, 5.0, 5.0])
    factor = ZScoreFactor(window=3)

    result = factor.compute(data, ZScoreParams(window=3))

    assert result.series.iloc[2:].isna().all()


def test_a_nan_propagates_for_exactly_window_consecutive_outputs() -> None:
    data = _series([1.0, 2.0, 3.0, np.nan, 5.0, 6.0, 7.0, 8.0])
    factor = ZScoreFactor(window=3)

    result = factor.compute(data, ZScoreParams(window=3))

    assert not math.isnan(result.series.iloc[2])
    assert result.series.iloc[3:6].isna().all()
    assert not math.isnan(result.series.iloc[6])
    assert not math.isnan(result.series.iloc[7])


def test_does_not_mutate_its_input() -> None:
    data = _series([1.0, 2.0, 3.0, 4.0])
    original = data.copy()
    factor = ZScoreFactor(window=3)

    factor.compute(data, ZScoreParams(window=3))

    pd.testing.assert_series_equal(data, original)


def test_no_lookahead() -> None:
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=dates)
    perturbed = pd.Series([1.0, 2.0, 3.0, 4.0, 999.0], index=dates)

    factor = ZScoreFactor(window=3)
    params = ZScoreParams(window=3)

    result = factor.compute(data, params)
    perturbed_result = factor.compute(perturbed, params)

    pd.testing.assert_series_equal(result.series.iloc[:4], perturbed_result.series.iloc[:4])


def test_running_twice_is_bit_identical() -> None:
    data = _series([2.0, 4.0, 9.0, 1.0, 6.0])
    factor = ZScoreFactor(window=3)
    params = ZScoreParams(window=3)

    first = factor.compute(data, params)
    second = factor.compute(data, params)

    pd.testing.assert_series_equal(first.series, second.series)


def test_rejects_non_positive_window_param() -> None:
    with pytest.raises(ValidationError):
        ZScoreParams(window=0)


def test_rejects_non_positive_window_at_construction() -> None:
    with pytest.raises(ValueError, match="window must be positive"):
        ZScoreFactor(window=0)


def test_rejects_params_window_mismatched_with_construction() -> None:
    factor = ZScoreFactor(window=3)
    data = _series([1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="window=3"):
        factor.compute(data, ZScoreParams(window=5))


def test_describe_mentions_the_window() -> None:
    factor = ZScoreFactor(window=20)
    assert "20" in factor.describe()
