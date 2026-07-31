"""Tests for `core.factor`: the `Factor` Protocol, `FactorParams`, and
`FactorResult`.

`Factor` itself has no implementation to test directly (it's a Protocol) —
these tests check that a conforming implementation is recognized structurally
and that the supporting types behave as the contract in
docs/factor-interface.md requires (params are immutable, results carry the
series and any intermediates).
"""

from __future__ import annotations

import pandas as pd
import pytest
from pydantic import ValidationError

from modelforge.core.factor import Factor, FactorResult
from tests.conftest import ToyRollingSumFactor, ToySumParams


def test_conforming_implementation_satisfies_the_factor_protocol() -> None:
    factor = ToyRollingSumFactor(window=3)
    assert isinstance(factor, Factor)


def test_factor_params_are_frozen() -> None:
    params = ToySumParams(window=3)
    with pytest.raises(ValidationError):
        params.window = 5


def test_factor_result_holds_series_and_defaults_to_no_intermediates() -> None:
    series = pd.Series([1.0, 2.0], index=pd.to_datetime(["2024-01-01", "2024-01-02"]))
    result = FactorResult(series=series)
    assert result.intermediates == {}
    pd.testing.assert_series_equal(result.series, series)


def test_factor_result_can_carry_inspectable_intermediates() -> None:
    series = pd.Series([1.0, 2.0], index=pd.to_datetime(["2024-01-01", "2024-01-02"]))
    mean = pd.Series([1.0, 1.5], index=series.index)
    result = FactorResult(series=series, intermediates={"rolling_mean": mean})
    pd.testing.assert_series_equal(result.intermediates["rolling_mean"], mean)


def test_toy_factor_computes_the_expected_rolling_sum() -> None:
    data = pd.Series(
        [1.0, 2.0, 3.0, 4.0],
        index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]),
    )
    factor = ToyRollingSumFactor(window=3)
    result = factor.compute(data, ToySumParams(window=3))

    assert result.series.iloc[0] != result.series.iloc[0]  # NaN != NaN
    assert result.series.iloc[1] != result.series.iloc[1]
    assert result.series.iloc[2] == 6.0  # 1 + 2 + 3
    assert result.series.iloc[3] == 9.0  # 2 + 3 + 4


def test_toy_factor_does_not_mutate_its_input() -> None:
    data = pd.Series(
        [1.0, 2.0, 3.0], index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
    )
    original = data.copy()
    factor = ToyRollingSumFactor(window=3)
    factor.compute(data, ToySumParams(window=3))
    pd.testing.assert_series_equal(data, original)


def test_toy_factor_has_no_lookahead() -> None:
    """Perturbing data after index t must not change the output at t."""
    dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"])
    data = pd.Series([1.0, 2.0, 3.0, 4.0], index=dates)
    perturbed = pd.Series([1.0, 2.0, 3.0, 999.0], index=dates)

    factor = ToyRollingSumFactor(window=3)
    params = ToySumParams(window=3)

    result = factor.compute(data, params)
    perturbed_result = factor.compute(perturbed, params)

    assert result.series.iloc[2] == perturbed_result.series.iloc[2]
