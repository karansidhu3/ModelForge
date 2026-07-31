"""Tests for `experiments.tracker`: recording and loading experiment runs."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from modelforge.core.config import DatasetConfig, RunConfig
from modelforge.core.factor import FactorResult
from modelforge.core.validation import ValidationConfig, validate_result
from modelforge.experiments.tracker import load_experiments, record_experiment
from tests.conftest import ToyRollingSumFactor, ToySumParams


def _config(tmp_path: Path, **overrides: object) -> RunConfig:
    defaults: dict[str, object] = {
        "model_name": "toy_rolling_sum",
        "params": {"window": 3},
        "dataset": DatasetConfig(path=tmp_path / "data.csv"),
    }
    defaults.update(overrides)
    return RunConfig(**defaults)  # type: ignore[arg-type]


def _data() -> pd.Series:
    return pd.Series([1.0, 2.0, 3.0, 4.0], index=pd.date_range("2024-01-01", periods=4, freq="D"))


def test_writes_one_json_file_per_run(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    config = _config(tmp_path)
    factor = ToyRollingSumFactor(window=3)
    data = _data()
    result = factor.compute(data, ToySumParams(window=3))
    validation = validate_result(data, result, factor, ValidationConfig())

    record_experiment(config, factor, result, validation, runtime_seconds=0.01, runs_dir=runs_dir)

    files = list(runs_dir.glob("*.json"))
    assert len(files) == 1


def test_record_round_trips_through_disk(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    config = _config(tmp_path, params={"window": 3})
    factor = ToyRollingSumFactor(window=3)
    data = _data()
    result = factor.compute(data, ToySumParams(window=3))
    validation = validate_result(data, result, factor, ValidationConfig())

    written = record_experiment(
        config, factor, result, validation, runtime_seconds=0.01, runs_dir=runs_dir
    )
    (loaded,) = load_experiments(runs_dir)

    assert loaded == written


def test_recorded_file_is_valid_indented_json(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    config = _config(tmp_path)
    factor = ToyRollingSumFactor(window=3)
    data = _data()
    result = factor.compute(data, ToySumParams(window=3))
    validation = validate_result(data, result, factor, ValidationConfig())

    record_experiment(config, factor, result, validation, runtime_seconds=0.01, runs_dir=runs_dir)

    (path,) = runs_dir.glob("*.json")
    text = path.read_text()
    assert "\n" in text  # indented, not a single line
    json.loads(text)  # doesn't raise


def test_records_model_name_and_params(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    config = _config(tmp_path, model_name="toy_rolling_sum", params={"window": 3})
    factor = ToyRollingSumFactor(window=3)
    data = _data()
    result = factor.compute(data, ToySumParams(window=3))
    validation = validate_result(data, result, factor, ValidationConfig())

    record = record_experiment(
        config, factor, result, validation, runtime_seconds=0.01, runs_dir=runs_dir
    )

    assert record.model_name == "toy_rolling_sum"
    assert record.params == {"window": 3}


def test_records_dataset_details(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    config = _config(tmp_path)
    factor = ToyRollingSumFactor(window=3)
    data = _data()
    result = factor.compute(data, ToySumParams(window=3))
    validation = validate_result(data, result, factor, ValidationConfig())

    record = record_experiment(
        config, factor, result, validation, runtime_seconds=0.01, runs_dir=runs_dir
    )

    assert record.dataset["source"] == "csv"
    assert record.dataset["path"] == str(tmp_path / "data.csv")
    assert record.dataset["date_column"] == "date"
    assert record.dataset["value_column"] == "value"


def test_output_summary_reflects_the_result_series(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    config = _config(tmp_path)
    factor = ToyRollingSumFactor(window=3)
    series = pd.Series(
        [np.nan, np.nan, 6.0, 9.0], index=pd.date_range("2024-01-01", periods=4, freq="D")
    )
    result = FactorResult(series=series)
    validation = validate_result(_data(), result, factor, ValidationConfig())

    record = record_experiment(
        config, factor, result, validation, runtime_seconds=0.01, runs_dir=runs_dir
    )

    assert record.output_summary["n_observations"] == 4
    assert record.output_summary["n_valid"] == 2
    assert record.output_summary["first_valid_value"] == 6.0
    assert record.output_summary["last_valid_value"] == 9.0


def test_records_validation_outcome(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    config = _config(tmp_path)
    factor = ToyRollingSumFactor(window=3)
    # A result index containing a label absent from the input data is a
    # guaranteed validation error, regardless of the data's own content.
    foreign_index = pd.date_range("2030-01-01", periods=2, freq="D")
    result = FactorResult(series=pd.Series([1.0, 2.0], index=foreign_index))
    validation = validate_result(_data(), result, factor, ValidationConfig())

    record = record_experiment(
        config, factor, result, validation, runtime_seconds=0.01, runs_dir=runs_dir
    )

    assert record.validation_passed is False
    assert len(record.validation_errors) >= 1
    assert record.validation_warnings == []


def test_commit_hash_is_none_or_a_full_hex_sha(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    config = _config(tmp_path)
    factor = ToyRollingSumFactor(window=3)
    data = _data()
    result = factor.compute(data, ToySumParams(window=3))
    validation = validate_result(data, result, factor, ValidationConfig())

    record = record_experiment(
        config, factor, result, validation, runtime_seconds=0.01, runs_dir=runs_dir
    )

    if record.commit_hash is not None:
        assert len(record.commit_hash) == 40
        assert all(c in "0123456789abcdef" for c in record.commit_hash)
        assert isinstance(record.commit_dirty, bool)
    else:
        assert record.commit_dirty is None


def test_load_experiments_returns_empty_list_for_missing_directory(tmp_path: Path) -> None:
    assert load_experiments(tmp_path / "does_not_exist") == []


def test_load_experiments_sorted_oldest_first(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    config = _config(tmp_path)
    factor = ToyRollingSumFactor(window=3)
    data = _data()
    result = factor.compute(data, ToySumParams(window=3))
    validation = validate_result(data, result, factor, ValidationConfig())

    first = record_experiment(
        config, factor, result, validation, runtime_seconds=0.01, runs_dir=runs_dir
    )
    second = record_experiment(
        config, factor, result, validation, runtime_seconds=0.02, runs_dir=runs_dir
    )

    loaded = load_experiments(runs_dir)
    assert [r.run_id for r in loaded] == [first.run_id, second.run_id]
    assert loaded[0].timestamp <= loaded[1].timestamp


@pytest.mark.parametrize("runtime_seconds", [0.0, 1.5])
def test_runtime_is_recorded_as_given(tmp_path: Path, runtime_seconds: float) -> None:
    runs_dir = tmp_path / "runs"
    config = _config(tmp_path)
    factor = ToyRollingSumFactor(window=3)
    data = _data()
    result = factor.compute(data, ToySumParams(window=3))
    validation = validate_result(data, result, factor, ValidationConfig())

    record = record_experiment(
        config, factor, result, validation, runtime_seconds=runtime_seconds, runs_dir=runs_dir
    )

    assert record.runtime_seconds == runtime_seconds
