"""The runtime execution pipeline: config -> load data -> run factor ->
validate -> record -> output. See `docs/execution-pipeline.md` for the
design of this path and its failure behavior per stage.

`factor` and its validated `params` are supplied directly by the caller
rather than resolved from `config.model_name` — see DD-008 in
`DESIGN_DECISIONS.md` for why dispatch is direct injection, not a registry.
Experiment recording is a no-op stub in Phase 2; real tracking (writing a
JSON record per run, per `docs/experiment-tracking.md`) is Phase 4 scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import pandas as pd

from modelforge.core.config import DateRange, RunConfig
from modelforge.core.factor import Factor, FactorParams, FactorResult
from modelforge.core.validation import ValidationReport, validate_result
from modelforge.data.loaders import load_csv


@dataclass(frozen=True)
class PipelineResult:
    """Everything produced by one pipeline execution, kept together so a
    caller (a test, a future CLI command, or the experiment tracker) can
    inspect any stage's output without re-running it."""

    config: RunConfig
    data: pd.Series
    factor_result: FactorResult
    validation: ValidationReport
    runtime_seconds: float


def run_pipeline(config: RunConfig, factor: Factor, params: FactorParams) -> PipelineResult:
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

    _record_experiment(config, factor, validation, runtime_seconds)

    return PipelineResult(
        config=config,
        data=data,
        factor_result=factor_result,
        validation=validation,
        runtime_seconds=runtime_seconds,
    )


def _slice_date_range(data: pd.Series, date_range: DateRange) -> pd.Series:
    start = pd.Timestamp(date_range.start) if date_range.start is not None else None
    end = pd.Timestamp(date_range.end) if date_range.end is not None else None
    return data.loc[start:end]


def _record_experiment(
    config: RunConfig, factor: Factor, validation: ValidationReport, runtime_seconds: float
) -> None:
    """No-op placeholder for `experiments/` run recording. Real tracking
    (see docs/experiment-tracking.md) is Phase 4 scope per ROADMAP.md; this
    stub exists so the pipeline's stage order matches the documented design
    now, without inventing a storage format ahead of when it's needed."""
    return None
