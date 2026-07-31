"""End-to-end tests for `core.pipeline.run_pipeline`.

Covers the Phase 2 exit criterion (a hand-written toy `Factor` running
end-to-end through the pipeline against a CSV fixture) and the Phase 4 exit
criterion (running the same model twice with different parameters produces
two comparable, inspectable tracked experiments — see
`test_two_runs_with_different_params_produce_comparable_tracked_experiments`).

Every call passes `experiment_runs_dir=runs_dir` (a `tmp_path` subdirectory)
so tests never write into the real, git-ignored `experiments/runs/`.
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


@pytest.fixture
def runs_dir(tmp_path: Path) -> Path:
    return tmp_path / "runs"


def _config(fixtures_dir: Path, **overrides: object) -> RunConfig:
    defaults: dict[str, object] = {
        "model_name": "toy_rolling_sum",
        "params": {"window": 3},
        "dataset": DatasetConfig(path=fixtures_dir / "clean_series.csv"),
    }
    defaults.update(overrides)
    return RunConfig(**defaults)  # type: ignore[arg-type]


def test_runs_end_to_end_and_produces_a_validated_result(
    fixtures_dir: Path, runs_dir: Path
) -> None:
    config = _config(fixtures_dir)
    factor = ToyRollingSumFactor(window=3)
    params = ToySumParams(window=3)

    result = run_pipeline(config, factor, params, experiment_runs_dir=runs_dir)

    assert result.validation.passed
    assert len(result.data) == 10
    assert result.factor_result.series.loc["2024-01-03"] == 6.0
    assert result.factor_result.series.loc["2024-01-10"] == 27.0
    assert result.runtime_seconds >= 0.0


def test_passes_with_a_matching_known_answer_fixture(fixtures_dir: Path, runs_dir: Path) -> None:
    config = _config(
        fixtures_dir,
        validation=ValidationConfig(
            known_answer=[KnownAnswerPoint(at=date(2024, 1, 3), expected=6.0, tolerance=1e-9)]
        ),
    )
    factor = ToyRollingSumFactor(window=3)
    params = ToySumParams(window=3)

    result = run_pipeline(config, factor, params, experiment_runs_dir=runs_dir)

    assert result.validation.passed


def test_fails_validation_without_raising_on_a_mismatched_known_answer(
    fixtures_dir: Path, runs_dir: Path
) -> None:
    config = _config(
        fixtures_dir,
        validation=ValidationConfig(
            known_answer=[KnownAnswerPoint(at=date(2024, 1, 3), expected=999.0, tolerance=1e-9)]
        ),
    )
    factor = ToyRollingSumFactor(window=3)
    params = ToySumParams(window=3)

    result = run_pipeline(config, factor, params, experiment_runs_dir=runs_dir)

    assert not result.validation.passed
    assert any(issue.check == "known_answer" for issue in result.validation.errors)
    assert result.experiment.validation_passed is False
    assert any("known_answer" in message for message in result.experiment.validation_errors)


def test_date_range_slices_the_loaded_data(fixtures_dir: Path, runs_dir: Path) -> None:
    config = _config(
        fixtures_dir,
        date_range=DateRange(start=date(2024, 1, 3), end=date(2024, 1, 6)),
    )
    factor = ToyRollingSumFactor(window=3)
    params = ToySumParams(window=3)

    result = run_pipeline(config, factor, params, experiment_runs_dir=runs_dir)

    assert len(result.data) == 4
    assert result.data.index.min() == pd.Timestamp("2024-01-03")
    assert result.data.index.max() == pd.Timestamp("2024-01-06")


def test_missing_dataset_file_raises_before_any_factor_runs(tmp_path: Path, runs_dir: Path) -> None:
    config = RunConfig(
        model_name="toy_rolling_sum",
        params={"window": 3},
        dataset=DatasetConfig(path=tmp_path / "does_not_exist.csv"),
    )
    factor = ToyRollingSumFactor(window=3)
    params = ToySumParams(window=3)

    with pytest.raises(FileNotFoundError):
        run_pipeline(config, factor, params, experiment_runs_dir=runs_dir)

    assert not runs_dir.exists()  # nothing recorded — the pipeline never reached that stage


def test_running_the_same_config_twice_is_bit_identical(fixtures_dir: Path, runs_dir: Path) -> None:
    config = _config(fixtures_dir)
    factor = ToyRollingSumFactor(window=3)
    params = ToySumParams(window=3)

    first = run_pipeline(config, factor, params, experiment_runs_dir=runs_dir)
    second = run_pipeline(config, factor, params, experiment_runs_dir=runs_dir)

    pd.testing.assert_series_equal(first.factor_result.series, second.factor_result.series)


def test_run_produces_a_readable_experiment_record_on_disk(
    fixtures_dir: Path, runs_dir: Path
) -> None:
    from modelforge.experiments.tracker import load_experiments

    config = _config(fixtures_dir)
    factor = ToyRollingSumFactor(window=3)
    params = ToySumParams(window=3)

    result = run_pipeline(config, factor, params, experiment_runs_dir=runs_dir)

    recorded = load_experiments(runs_dir)
    assert len(recorded) == 1
    assert recorded[0].run_id == result.experiment.run_id
    assert recorded[0].model_name == "toy_rolling_sum"
    assert recorded[0].params == {"window": 3}


def test_two_runs_with_different_params_produce_comparable_tracked_experiments(
    fixtures_dir: Path, runs_dir: Path
) -> None:
    """Phase 4 exit criterion: running the same model twice with different
    parameters produces two comparable, inspectable tracked experiments."""
    from modelforge.experiments.tracker import load_experiments

    config_a = _config(fixtures_dir, params={"window": 3})
    config_b = _config(fixtures_dir, params={"window": 5})

    run_pipeline(config_a, ToyRollingSumFactor(window=3), ToySumParams(window=3), runs_dir)
    run_pipeline(config_b, ToyRollingSumFactor(window=5), ToySumParams(window=5), runs_dir)

    recorded = load_experiments(runs_dir)
    assert len(recorded) == 2
    assert recorded[0].run_id != recorded[1].run_id
    assert {r.params["window"] for r in recorded} == {3, 5}
    # Same model, same dataset — genuinely comparable, differing only in
    # what a run through this framework is expected to differ on.
    assert {r.model_name for r in recorded} == {"toy_rolling_sum"}
    assert {r.dataset["path"] for r in recorded} == {str(fixtures_dir / "clean_series.csv")}
