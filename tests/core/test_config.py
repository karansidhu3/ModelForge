"""Tests for `core.config`: construction-time validation of `RunConfig` and
its nested models."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from modelforge.core.config import (
    DatasetConfig,
    DateRange,
    KnownAnswerPoint,
    RunConfig,
    ValidationConfig,
)


def _dataset(tmp_path: Path) -> DatasetConfig:
    return DatasetConfig(path=tmp_path / "data.csv")


def test_run_config_accepts_a_well_formed_config(tmp_path: Path) -> None:
    config = RunConfig(
        model_name="toy_rolling_sum", params={"window": 3}, dataset=_dataset(tmp_path)
    )
    assert config.model_name == "toy_rolling_sum"
    assert config.params == {"window": 3}


def test_run_config_rejects_blank_model_name(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        RunConfig(model_name="   ", dataset=_dataset(tmp_path))


def test_date_range_accepts_ordered_bounds() -> None:
    date_range = DateRange(start=date(2024, 1, 1), end=date(2024, 1, 31))
    assert date_range.start == date(2024, 1, 1)


def test_date_range_rejects_start_after_end() -> None:
    with pytest.raises(ValidationError):
        DateRange(start=date(2024, 2, 1), end=date(2024, 1, 1))


def test_date_range_allows_unbounded_sides() -> None:
    date_range = DateRange(start=date(2024, 1, 1))
    assert date_range.end is None


def test_known_answer_point_rejects_non_positive_tolerance() -> None:
    with pytest.raises(ValidationError):
        KnownAnswerPoint(at=date(2024, 1, 3), expected=6.0, tolerance=0.0)


def test_validation_config_defaults_to_no_known_answers() -> None:
    assert ValidationConfig().known_answer == []


def test_run_config_is_frozen(tmp_path: Path) -> None:
    config = RunConfig(model_name="toy_rolling_sum", dataset=_dataset(tmp_path))
    with pytest.raises(ValidationError):
        config.model_name = "something_else"
