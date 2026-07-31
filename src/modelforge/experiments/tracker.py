"""Local-file experiment recording.

Writes one JSON file per pipeline run under `experiments/runs/` (git-ignored
— see `.gitignore` and DD-003 in `DESIGN_DECISIONS.md`). See
`docs/experiment-tracking.md` for the field list and the rationale for local
files over a database.

This module has no knowledge of what a factor *computes* — it only knows the
generic shape every run shares (a config, a factor's name, a result series,
a validation outcome, a runtime). See ARCHITECTURE.md.
"""

from __future__ import annotations

import json
import subprocess
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

import modelforge
from modelforge.core.config import RunConfig
from modelforge.core.factor import Factor, FactorResult
from modelforge.core.validation import ValidationReport

DEFAULT_RUNS_DIR = Path("experiments/runs")


@dataclass(frozen=True)
class ExperimentRecord:
    """Everything recorded about one pipeline execution.

    Every field is a JSON-native type (str, float, bool, dict, list, or
    None) so a record round-trips through `json.dumps`/`json.loads` without
    a separate serialization layer — see `to_json` and `load_experiments`.
    """

    run_id: str
    timestamp: str
    model_name: str
    params: dict[str, Any]
    dataset: dict[str, Any]
    framework_version: str
    runtime_seconds: float
    commit_hash: str | None
    commit_dirty: bool | None
    validation_passed: bool
    validation_errors: list[str]
    validation_warnings: list[str]
    output_summary: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def record_experiment(
    config: RunConfig,
    factor: Factor,
    factor_result: FactorResult,
    validation: ValidationReport,
    runtime_seconds: float,
    runs_dir: Path = DEFAULT_RUNS_DIR,
) -> ExperimentRecord:
    """Build a record for one run and write it to `runs_dir`.

    Called from `core/pipeline.py` as the pipeline's last stage — see
    `docs/execution-pipeline.md`. Recording happens regardless of whether
    validation passed: a failed run is itself something worth keeping a
    record of, never silently discarded.
    """
    commit_hash, commit_dirty = _current_commit()

    record = ExperimentRecord(
        run_id=uuid.uuid4().hex,
        timestamp=datetime.now(UTC).isoformat(),
        model_name=config.model_name,
        params=dict(config.params),
        dataset={
            "source": "csv",
            "path": str(config.dataset.path),
            "date_column": config.dataset.date_column,
            "value_column": config.dataset.value_column,
            "date_range_start": (
                config.date_range.start.isoformat() if config.date_range.start else None
            ),
            "date_range_end": config.date_range.end.isoformat() if config.date_range.end else None,
        },
        framework_version=modelforge.__version__,
        runtime_seconds=runtime_seconds,
        commit_hash=commit_hash,
        commit_dirty=commit_dirty,
        validation_passed=validation.passed,
        validation_errors=[f"{issue.check}: {issue.message}" for issue in validation.errors],
        validation_warnings=[f"{issue.check}: {issue.message}" for issue in validation.warnings],
        output_summary=_summarize(factor_result.series),
    )

    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / _filename(record)).write_text(record.to_json())

    return record


def _filename(record: ExperimentRecord) -> str:
    """A filesystem-safe, chronologically-sortable filename: a compact UTC
    timestamp (no colons or periods) followed by the run ID."""
    compact_timestamp = datetime.fromisoformat(record.timestamp).strftime("%Y%m%dT%H%M%S%f")
    return f"{compact_timestamp}_{record.run_id}.json"


def load_experiments(runs_dir: Path = DEFAULT_RUNS_DIR) -> list[ExperimentRecord]:
    """Load every recorded run under `runs_dir`, oldest first.

    Returns an empty list if `runs_dir` doesn't exist yet — no runs have
    been recorded, which isn't an error.
    """
    if not runs_dir.exists():
        return []

    records = [ExperimentRecord(**json.loads(path.read_text())) for path in runs_dir.glob("*.json")]
    return sorted(records, key=lambda record: record.timestamp)


def _summarize(series: pd.Series) -> dict[str, Any]:
    """A compact, JSON-native summary of a result series — not the full
    series itself. See DD-009 in DESIGN_DECISIONS.md for why: this keeps
    records small, diffable, and comparable across runs, which is what
    `docs/experiment-tracking.md` asks for ("trivial to load into a Pandas
    DataFrame for comparison"). Reproducing the full series exactly is
    already covered by re-running the recorded config at the recorded
    commit — see docs/reproducibility.md.
    """
    valid = series.dropna()
    return {
        "n_observations": len(series),
        "n_valid": len(valid),
        "first_valid_index": str(valid.index[0]) if not valid.empty else None,
        "last_valid_index": str(valid.index[-1]) if not valid.empty else None,
        "first_valid_value": float(valid.iloc[0]) if not valid.empty else None,
        "last_valid_value": float(valid.iloc[-1]) if not valid.empty else None,
    }


def _current_commit() -> tuple[str | None, bool | None]:
    """The current git commit hash and whether the working tree has
    uncommitted changes, or `(None, None)` if this isn't running inside a
    git repository or git isn't available.

    Fails soft rather than raising: commit provenance is auxiliary metadata
    about a run, not part of its numerical result, and this repository
    itself won't always be a git checkout (e.g. an extracted source archive)
    — see the "known limitation, stated honestly" pattern in
    docs/reproducibility.md.
    """
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return commit, bool(status.strip())
    except (OSError, subprocess.CalledProcessError):
        return None, None
