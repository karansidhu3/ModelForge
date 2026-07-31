"""Tests for `models.mean_reversion`.

See `research/mean_reversion/README.md` for the math (percentage deviation
from a trailing moving average) and how it differs from `models.z_score`.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from modelforge.models.mean_reversion import MeanReversionFactor, MeanReversionParams


def _series(values: list[float], n: int | None = None) -> pd.Series:
    n = n if n is not None else len(values)
    index = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.Series(values, index=index)


def test_known_answer_matches_hand_computed_deviation() -> None:
    # window=3 over [10, 20, 30, 20, 10]:
    #   idx2 (10,20,30): mean=20, dev=(30-20)/20 = 0.5
    #   idx3 (20,30,20): mean=70/3, dev=(20-70/3)/(70/3) = -1/7
    #   idx4 (30,20,10): mean=20, dev=(10-20)/20 = -0.5
    data = _series([10.0, 20.0, 30.0, 20.0, 10.0])
    factor = MeanReversionFactor(window=3)

    result = factor.compute(data, MeanReversionParams(window=3))

    assert math.isnan(result.series.iloc[0])
    assert math.isnan(result.series.iloc[1])
    assert result.series.iloc[2] == pytest.approx(0.5)
    assert result.series.iloc[3] == pytest.approx(-1.0 / 7.0)
    assert result.series.iloc[4] == pytest.approx(-0.5)


def test_exposes_moving_average_as_an_intermediate() -> None:
    data = _series([10.0, 20.0, 30.0])
    factor = MeanReversionFactor(window=3)

    result = factor.compute(data, MeanReversionParams(window=3))

    assert result.intermediates["moving_average"].iloc[2] == pytest.approx(20.0)


def test_empty_input_produces_empty_output() -> None:
    data = pd.Series([], index=pd.DatetimeIndex([]), dtype="float64")
    factor = MeanReversionFactor(window=3)

    result = factor.compute(data, MeanReversionParams(window=3))

    assert result.series.empty


def test_input_shorter_than_window_is_entirely_nan() -> None:
    data = _series([1.0, 2.0])
    factor = MeanReversionFactor(window=5)

    result = factor.compute(data, MeanReversionParams(window=5))

    assert len(result.series) == 2
    assert result.series.isna().all()


def test_constant_series_has_zero_deviation() -> None:
    data = _series([5.0, 5.0, 5.0, 5.0])
    factor = MeanReversionFactor(window=3)

    result = factor.compute(data, MeanReversionParams(window=3))

    assert result.series.iloc[2:].eq(0.0).all()


def test_a_zero_moving_average_produces_infinity_not_an_exception() -> None:
    # window=3 over [-10, 0, 10]: mean=0, so (10-0)/0 = inf.
    data = _series([-10.0, 0.0, 10.0])
    factor = MeanReversionFactor(window=3)

    result = factor.compute(data, MeanReversionParams(window=3))

    assert math.isinf(result.series.iloc[2])


def test_a_nan_propagates_for_exactly_window_consecutive_outputs() -> None:
    data = _series([1.0, 2.0, 3.0, np.nan, 5.0, 6.0, 7.0, 8.0])
    factor = MeanReversionFactor(window=3)

    result = factor.compute(data, MeanReversionParams(window=3))

    assert not math.isnan(result.series.iloc[2])
    assert result.series.iloc[3:6].isna().all()
    assert not math.isnan(result.series.iloc[6])
    assert not math.isnan(result.series.iloc[7])


def test_does_not_mutate_its_input() -> None:
    data = _series([10.0, 20.0, 30.0, 20.0])
    original = data.copy()
    factor = MeanReversionFactor(window=3)

    factor.compute(data, MeanReversionParams(window=3))

    pd.testing.assert_series_equal(data, original)


def test_no_lookahead() -> None:
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    data = pd.Series([10.0, 20.0, 30.0, 20.0, 10.0], index=dates)
    perturbed = pd.Series([10.0, 20.0, 30.0, 20.0, 999.0], index=dates)

    factor = MeanReversionFactor(window=3)
    params = MeanReversionParams(window=3)

    result = factor.compute(data, params)
    perturbed_result = factor.compute(perturbed, params)

    pd.testing.assert_series_equal(result.series.iloc[:4], perturbed_result.series.iloc[:4])


def test_running_twice_is_bit_identical() -> None:
    data = _series([10.0, 20.0, 30.0, 20.0, 10.0])
    factor = MeanReversionFactor(window=3)
    params = MeanReversionParams(window=3)

    first = factor.compute(data, params)
    second = factor.compute(data, params)

    pd.testing.assert_series_equal(first.series, second.series)


def test_rejects_non_positive_window_param() -> None:
    with pytest.raises(ValidationError):
        MeanReversionParams(window=0)


def test_rejects_non_positive_window_at_construction() -> None:
    with pytest.raises(ValueError, match="window must be positive"):
        MeanReversionFactor(window=0)


def test_rejects_params_window_mismatched_with_construction() -> None:
    factor = MeanReversionFactor(window=3)
    data = _series([1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="window=3"):
        factor.compute(data, MeanReversionParams(window=5))


def test_describe_mentions_the_window() -> None:
    factor = MeanReversionFactor(window=20)
    assert "20" in factor.describe()
