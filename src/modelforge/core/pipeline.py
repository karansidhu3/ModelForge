"""The runtime execution pipeline: config -> load data -> run factor ->
validate -> record -> output. See `docs/execution-pipeline.md` for the
design of this path and its failure behavior per stage.

`factor` and its validated `params` are supplied directly by the caller
rather than resolved from `config.model_name` — see DD-008 in
`DESIGN_DECISIONS.md` for why dispatch is direct injection, not a registry.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import pandas as pd

from modelforge.core.config import DateRange, RunConfig
from modelforge.core.factor import Factor, FactorParams, FactorResult
from modelforge.core.validation import ValidationReport, validate_result
from modelforge.data.loaders import load_csv
from modelforge.experiments.tracker import DEFAULT_RUNS_DIR, ExperimentRecord, record_experiment


@dataclass(frozen=True)
class PipelineResult:
    """Everything produced by one pipeline execution, kept together so a
    caller (a test, the CLI, or a person at a REPL) can inspect any stage's
    output without re-running it or re-reading the recorded file."""

    config: RunConfig
    data: pd.Series
    factor_result: FactorResult
    validation: ValidationReport
    runtime_seconds: float
    experiment: ExperimentRecord


def run_pipeline(
    config: RunConfig,
    factor: Factor,
    params: FactorParams,
    experiment_runs_dir: Path = DEFAULT_RUNS_DIR,
) -> PipelineResult:
    """Run one pipeline execution end to end.

    A validation failure does not raise: the pipeline's job is to produce an
    honest, inspectable result, including the case where that result failed
    validation (see docs/execution-pipeline.md, "Failure behavior" — a
    validation failure is recorded, never silently discarded). A caller that
    wants "raise on validation failure" semantics checks
    `result.validation.passed` itself.

    Config errors and data-loading errors do raise, before any factor runs:
    `RunConfig` validates itself at construction (Pydantic), and `load_csv`
    raises on a missing file or malformed dataset.

    `experiment_runs_dir` defaults to `experiments/runs/` (see
    docs/experiment-tracking.md); tests override it to avoid writing into the
    real, git-ignored runs directory.
    """
    start = perf_counter()

    data = load_csv(
        config.dataset.path,
        date_column=config.dataset.date_column,
        value_column=config.dataset.value_column,
    )
    data = _slice_date_range(data, config.date_range)

    factor_result = factor.compute(data, params)
    validation = validate_result(data, factor_result, factor, config.validation)

    runtime_seconds = perf_counter() - start

    experiment = record_experiment(
        config, factor, factor_result, validation, runtime_seconds, runs_dir=experiment_runs_dir
    )

    return PipelineResult(
        config=config,
        data=data,
        factor_result=factor_result,
        validation=validation,
        runtime_seconds=runtime_seconds,
        experiment=experiment,
    )


def _slice_date_range(data: pd.Series, date_range: DateRange) -> pd.Series:
    start = pd.Timestamp(date_range.start) if date_range.start is not None else None
    end = pd.Timestamp(date_range.end) if date_range.end is not None else None
    return data.loc[start:end]
