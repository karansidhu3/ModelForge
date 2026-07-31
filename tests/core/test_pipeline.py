"""End-to-end tests for `core.pipeline.run_pipeline`.

This is the exit criterion from `ROADMAP.md` Phase 2: a hand-written toy
`Factor` (`ToyRollingSumFactor`, defined in `tests/conftest.py`) running
through the full pipeline against a CSV fixture and producing a validated
result.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from modelforge.core.config import (
    DatasetConfig,
    DateRange,
    KnownAnswerPoint,
    RunConfig,
    ValidationConfig,
)
from modelforge.core.pipeline import run_pipeline
from tests.conftest import ToyRollingSumFactor, ToySumParams


def _config(fixtures_dir: Path, **overrides: object) -> RunConfig:
    defaults: dict[str, object] = {
        "model_name": "toy_rolling_sum",
        "params": {"window": 3},
        "dataset": DatasetConfig(path=fixtures_dir / "clean_series.csv"),
    }
    defaults.update(overrides)
    return RunConfig(**defaults)  # type: ignore[arg-type]


def test_runs_end_to_end_and_produces_a_validated_result(fixtures_dir: Path) -> None:
    config = _config(fixtures_dir)
    factor = ToyRollingSumFactor(window=3)
    params = ToySumParams(window=3)

    result = run_pipeline(config, factor, params)

    assert result.validation.passed
    assert len(result.data) == 10
    assert result.factor_result.series.loc["2024-01-03"] == 6.0
    assert result.factor_result.series.loc["2024-01-10"] == 27.0
    assert result.runtime_seconds >= 0.0


def test_passes_with_a_matching_known_answer_fixture(fixtures_dir: Path) -> None:
    config = _config(
        fixtures_dir,
        validation=ValidationConfig(
            known_answer=[KnownAnswerPoint(at=date(2024, 1, 3), expected=6.0, tolerance=1e-9)]
        ),
    )
    factor = ToyRollingSumFactor(window=3)
    params = ToySumParams(window=3)

    result = run_pipeline(config, factor, params)

    assert result.validation.passed


def test_fails_validation_without_raising_on_a_mismatched_known_answer(fixtures_dir: Path) -> None:
    config = _config(
        fixtures_dir,
        validation=ValidationConfig(
            known_answer=[KnownAnswerPoint(at=date(2024, 1, 3), expected=999.0, tolerance=1e-9)]
        ),
    )
    factor = ToyRollingSumFactor(window=3)
    params = ToySumParams(window=3)

    result = run_pipeline(config, factor, params)

    assert not result.validation.passed
    assert any(issue.check == "known_answer" for issue in result.validation.errors)


def test_date_range_slices_the_loaded_data(fixtures_dir: Path) -> None:
    config = _config(
        fixtures_dir,
        date_range=DateRange(start=date(2024, 1, 3), end=date(2024, 1, 6)),
    )
    factor = ToyRollingSumFactor(window=3)
    params = ToySumParams(window=3)

    result = run_pipeline(config, factor, params)

    assert len(result.data) == 4
    assert result.data.index.min() == pd.Timestamp("2024-01-03")
    assert result.data.index.max() == pd.Timestamp("2024-01-06")


def test_missing_dataset_file_raises_before_any_factor_runs(tmp_path: Path) -> None:
    config = RunConfig(
        model_name="toy_rolling_sum",
        params={"window": 3},
        dataset=DatasetConfig(path=tmp_path / "does_not_exist.csv"),
    )
    factor = ToyRollingSumFactor(window=3)
    params = ToySumParams(window=3)

    with pytest.raises(FileNotFoundError):
        run_pipeline(config, factor, params)


def test_running_the_same_config_twice_is_bit_identical(fixtures_dir: Path) -> None:
    config = _config(fixtures_dir)
    factor = ToyRollingSumFactor(window=3)
    params = ToySumParams(window=3)

    first = run_pipeline(config, factor, params)
    second = run_pipeline(config, factor, params)

    pd.testing.assert_series_equal(first.factor_result.series, second.factor_result.series)
