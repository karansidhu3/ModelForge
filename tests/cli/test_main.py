"""Tests for the `modelforge` CLI: argument parsing and table formatting.

Per DD-005, the CLI has no logic of its own beyond formatting — these tests
check that `experiments list` calls into `experiments.tracker` correctly and
renders what it returns, not any independent business logic.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from modelforge.cli.main import app
from modelforge.core.config import DatasetConfig, RunConfig
from modelforge.core.validation import ValidationConfig, validate_result
from modelforge.experiments.tracker import record_experiment
from tests.conftest import ToyRollingSumFactor, ToySumParams

runner = CliRunner()


def _record(tmp_path: Path, runs_dir: Path, window: int) -> None:
    config = RunConfig(
        model_name="toy_rolling_sum",
        params={"window": window},
        dataset=DatasetConfig(path=tmp_path / "data.csv"),
    )
    factor = ToyRollingSumFactor(window=window)
    data = pd.Series([1.0, 2.0, 3.0, 4.0], index=pd.date_range("2024-01-01", periods=4, freq="D"))
    result = factor.compute(data, ToySumParams(window=window))
    validation = validate_result(data, result, factor, ValidationConfig())
    record_experiment(config, factor, result, validation, runtime_seconds=0.01, runs_dir=runs_dir)


def test_reports_no_experiments_for_an_empty_directory(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"

    result = runner.invoke(app, ["experiments", "list", "--runs-dir", str(runs_dir)])

    assert result.exit_code == 0
    assert "No tracked experiments found" in result.stdout


def test_lists_recorded_experiments_as_a_table(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    _record(tmp_path, runs_dir, window=3)
    _record(tmp_path, runs_dir, window=5)

    result = runner.invoke(app, ["experiments", "list", "--runs-dir", str(runs_dir)])

    assert result.exit_code == 0
    assert "toy_rolling_sum" in result.stdout
    assert "{'window': 3}" in result.stdout
    assert "{'window': 5}" in result.stdout
    # header + separator + 2 rows
    assert len(result.stdout.strip().splitlines()) == 4
