"""Tests for `models.volatility`.

See `research/volatility/README.md` for the math (simple returns, then
rolling sample standard deviation) and assumptions.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from modelforge.models.volatility import VolatilityFactor, VolatilityParams


def _series(values: list[float], n: int | None = None) -> pd.Series:
    n = n if n is not None else len(values)
    index = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.Series(values, index=index)


def test_known_answer_matches_hand_computed_volatility() -> None:
    # Prices growing by 10%, 20%, then 30%: returns = [NaN, 0.1, 0.2, 0.3].
    # Sample std (ddof=1) of [0.1, 0.2, 0.3]: mean=0.2, deviations
    # [-0.1, 0, 0.1], sum of squares 0.02, variance 0.02/2 = 0.01, std = 0.1.
    data = _series([100.0, 110.0, 132.0, 171.6])
    factor = VolatilityFactor(window=3)

    result = factor.compute(data, VolatilityParams(window=3))

    assert math.isnan(result.series.iloc[0])
    assert math.isnan(result.series.iloc[1])
    assert math.isnan(result.series.iloc[2])
    assert result.series.iloc[3] == pytest.approx(0.1)


def test_exposes_returns_as_an_intermediate() -> None:
    data = _series([100.0, 110.0, 132.0, 171.6])
    factor = VolatilityFactor(window=3)

    result = factor.compute(data, VolatilityParams(window=3))

    returns = result.intermediates["returns"]
    assert math.isnan(returns.iloc[0])
    assert returns.iloc[1] == pytest.approx(0.1)
    assert returns.iloc[2] == pytest.approx(0.2)
    assert returns.iloc[3] == pytest.approx(0.3)


def test_empty_input_produces_empty_output() -> None:
    data = pd.Series([], index=pd.DatetimeIndex([]), dtype="float64")
    factor = VolatilityFactor(window=3)

    result = factor.compute(data, VolatilityParams(window=3))

    assert result.series.empty


def test_input_shorter_than_required_history_is_entirely_nan() -> None:
    data = _series([1.0, 2.0])
    factor = VolatilityFactor(window=5)

    result = factor.compute(data, VolatilityParams(window=5))

    assert len(result.series) == 2
    assert result.series.isna().all()


def test_constant_series_has_zero_volatility() -> None:
    data = _series([100.0, 100.0, 100.0, 100.0])
    factor = VolatilityFactor(window=3)

    result = factor.compute(data, VolatilityParams(window=3))

    assert result.series.iloc[3] == 0.0


def test_nan_in_input_invalidates_two_returns_and_recovers_after_the_window_ages_out() -> None:
    data = _series([1.0, 2.0, 3.0, np.nan, 5.0, 6.0, 7.0, 8.0, 9.0])
    factor = VolatilityFactor(window=3)

    result = factor.compute(data, VolatilityParams(window=3))

    # Every window touching either corrupted return (idx3 or idx4) is NaN.
    assert result.series.iloc[2:7].isna().all()
    # Once the window no longer includes idx3 or idx4, it recovers.
    assert not math.isnan(result.series.iloc[7])
    assert not math.isnan(result.series.iloc[8])


def test_does_not_mutate_its_input() -> None:
    data = _series([100.0, 110.0, 105.0, 115.0])
    original = data.copy()
    factor = VolatilityFactor(window=3)

    factor.compute(data, VolatilityParams(window=3))

    pd.testing.assert_series_equal(data, original)


def test_no_lookahead() -> None:
    dates = pd.date_range("2024-01-01", periods=6, freq="D")
    data = pd.Series([100.0, 105.0, 102.0, 108.0, 110.0, 107.0], index=dates)
    perturbed = pd.Series([100.0, 105.0, 102.0, 108.0, 110.0, 999.0], index=dates)

    factor = VolatilityFactor(window=3)
    params = VolatilityParams(window=3)

    result = factor.compute(data, params)
    perturbed_result = factor.compute(perturbed, params)

    pd.testing.assert_series_equal(result.series.iloc[:5], perturbed_result.series.iloc[:5])


def test_running_twice_is_bit_identical() -> None:
    data = _series([100.0, 110.0, 105.0, 115.0, 120.0])
    factor = VolatilityFactor(window=3)
    params = VolatilityParams(window=3)

    first = factor.compute(data, params)
    second = factor.compute(data, params)

    pd.testing.assert_series_equal(first.series, second.series)


def test_rejects_non_positive_window_param() -> None:
    with pytest.raises(ValidationError):
        VolatilityParams(window=0)


def test_rejects_non_positive_window_at_construction() -> None:
    with pytest.raises(ValueError, match="window must be positive"):
        VolatilityFactor(window=0)


def test_rejects_params_window_mismatched_with_construction() -> None:
    factor = VolatilityFactor(window=3)
    data = _series([1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="window=3"):
        factor.compute(data, VolatilityParams(window=5))


def test_describe_mentions_the_window() -> None:
    factor = VolatilityFactor(window=20)
    assert "20" in factor.describe()
