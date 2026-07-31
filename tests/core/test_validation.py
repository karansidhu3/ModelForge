"""Tests for `core.validation`: the runtime validation framework.

Uses synthetic, hand-constructed `pd.Series` throughout rather than going
through the CSV loader or the pipeline — these are unit tests of the
validation checks themselves, isolated from every other stage.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from modelforge.core.config import KnownAnswerPoint, ValidationConfig
from modelforge.core.factor import FactorResult
from modelforge.core.validation import validate_result
from tests.conftest import ToyRollingSumFactor


def _dates(n: int) -> pd.DatetimeIndex:
    return pd.date_range("2024-01-01", periods=n, freq="D")


@pytest.fixture
def clean_data() -> pd.Series:
    return pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=_dates(5), name="value")


def test_well_formed_result_passes_with_no_issues(clean_data: pd.Series) -> None:
    factor = ToyRollingSumFactor(window=3)
    result = FactorResult(series=clean_data.rolling(3, min_periods=3).sum())

    report = validate_result(clean_data, result, factor, ValidationConfig())

    assert report.passed
    assert report.issues == []


def test_duplicate_index_labels_are_an_error(clean_data: pd.Series) -> None:
    factor = ToyRollingSumFactor(window=3)
    bad_index = pd.DatetimeIndex([clean_data.index[2], clean_data.index[2], clean_data.index[3]])
    result = FactorResult(series=pd.Series([6.0, 6.0, 9.0], index=bad_index))

    report = validate_result(clean_data, result, factor, ValidationConfig())

    assert not report.passed
    assert any(issue.check == "index_alignment" for issue in report.errors)


def test_labels_not_present_in_input_are_an_error(clean_data: pd.Series) -> None:
    factor = ToyRollingSumFactor(window=3)
    foreign_index = pd.date_range("2030-01-01", periods=2, freq="D")
    result = FactorResult(series=pd.Series([1.0, 2.0], index=foreign_index))

    report = validate_result(clean_data, result, factor, ValidationConfig())

    assert not report.passed
    assert any(issue.check == "index_alignment" for issue in report.errors)


def test_out_of_order_result_index_is_an_error(clean_data: pd.Series) -> None:
    factor = ToyRollingSumFactor(window=3)
    reordered_index = clean_data.index[[2, 1, 3]]
    result = FactorResult(series=pd.Series([6.0, 3.0, 9.0], index=reordered_index))

    report = validate_result(clean_data, result, factor, ValidationConfig())

    assert not report.passed
    assert any(issue.check == "index_alignment" for issue in report.errors)


def test_nan_during_warmup_is_not_flagged(clean_data: pd.Series) -> None:
    factor = ToyRollingSumFactor(window=3)
    series = pd.Series([np.nan, np.nan, 6.0, 9.0, 12.0], index=clean_data.index)
    result = FactorResult(series=series)

    report = validate_result(clean_data, result, factor, ValidationConfig())

    assert report.passed
    assert report.warnings == []


def test_nan_after_warmup_with_clean_input_is_a_warning_not_an_error(clean_data: pd.Series) -> None:
    factor = ToyRollingSumFactor(window=3)
    series = pd.Series([np.nan, np.nan, np.nan, 9.0, 12.0], index=clean_data.index)
    result = FactorResult(series=series)

    report = validate_result(clean_data, result, factor, ValidationConfig())

    assert report.passed  # warnings don't fail the run
    assert len(report.warnings) == 1
    assert report.warnings[0].check == "nan_propagation"


def test_nan_after_warmup_is_not_flagged_when_input_itself_is_nan() -> None:
    factor = ToyRollingSumFactor(window=3)
    data = pd.Series([1.0, 2.0, np.nan, 4.0, 5.0], index=_dates(5))
    series = pd.Series([np.nan, np.nan, np.nan, 9.0, 12.0], index=data.index)
    result = FactorResult(series=series)

    report = validate_result(data, result, factor, ValidationConfig())

    assert report.warnings == []


def test_known_answer_point_within_tolerance_passes(clean_data: pd.Series) -> None:
    factor = ToyRollingSumFactor(window=3)
    series = clean_data.rolling(3, min_periods=3).sum()
    result = FactorResult(series=series)
    config = ValidationConfig(
        known_answer=[KnownAnswerPoint(at=date(2024, 1, 3), expected=6.0, tolerance=1e-9)]
    )

    report = validate_result(clean_data, result, factor, config)

    assert report.passed


def test_known_answer_point_outside_tolerance_is_an_error(clean_data: pd.Series) -> None:
    factor = ToyRollingSumFactor(window=3)
    series = clean_data.rolling(3, min_periods=3).sum()
    result = FactorResult(series=series)
    config = ValidationConfig(
        known_answer=[KnownAnswerPoint(at=date(2024, 1, 3), expected=999.0, tolerance=1e-9)]
    )

    report = validate_result(clean_data, result, factor, config)

    assert not report.passed
    assert any(issue.check == "known_answer" for issue in report.errors)


def test_known_answer_point_missing_from_result_is_an_error(clean_data: pd.Series) -> None:
    factor = ToyRollingSumFactor(window=3)
    series = clean_data.rolling(3, min_periods=3).sum()
    result = FactorResult(series=series)
    config = ValidationConfig(
        known_answer=[KnownAnswerPoint(at=date(2030, 1, 1), expected=6.0, tolerance=1e-9)]
    )

    report = validate_result(clean_data, result, factor, config)

    assert not report.passed


def test_known_answer_point_where_result_is_nan_is_an_error(clean_data: pd.Series) -> None:
    factor = ToyRollingSumFactor(window=3)
    series = clean_data.rolling(3, min_periods=3).sum()
    result = FactorResult(series=series)
    config = ValidationConfig(
        known_answer=[KnownAnswerPoint(at=date(2024, 1, 1), expected=1.0, tolerance=1e-9)]
    )

    report = validate_result(clean_data, result, factor, config)

    assert not report.passed
