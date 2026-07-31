"""Pydantic run-configuration schema.

Every pipeline execution is fully described by a `RunConfig`: which dataset
to load, what date range to slice it to, and what to check the result
against. Validation happens at construction time — a malformed config raises
immediately, before any data is loaded or any model runs. See
`docs/reproducibility.md` for why config-driven execution is the basis of
reproducibility here, and DD-008 in `DESIGN_DECISIONS.md` for why this schema
records `model_name` and `params` as descriptive metadata only, rather than
using them to dispatch to a `Factor` implementation.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class DatasetConfig(BaseModel):
    """Identifies which dataset a run reads from.

    Only describes *what* to load, not *how* — the loader in `data/` is
    responsible for turning this into a validated series. Existence of
    `path` is checked at load time, not here: a missing file is a
    data-loading failure, not a config-shape failure (see
    `docs/execution-pipeline.md` on failure behavior per stage).
    """

    model_config = ConfigDict(frozen=True)

    path: Path
    date_column: str = "date"
    value_column: str = "value"


class DateRange(BaseModel):
    """An optional, inclusive date window to slice the loaded series to.

    `None` on either bound means unbounded in that direction.
    """

    model_config = ConfigDict(frozen=True)

    start: date | None = None
    end: date | None = None

    @model_validator(mode="after")
    def _check_bounds_ordered(self) -> DateRange:
        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError(
                f"date_range.start ({self.start}) is after date_range.end ({self.end})"
            )
        return self


class KnownAnswerPoint(BaseModel):
    """A single point the validation framework spot-checks a run's output
    against, taken from source material or an independent hand computation.

    See `docs/validation.md` on why this check exists at the pipeline layer
    in addition to (not instead of) known-answer unit tests.
    """

    model_config = ConfigDict(frozen=True)

    at: date
    expected: float
    tolerance: float = 1e-9

    @model_validator(mode="after")
    def _check_tolerance_positive(self) -> KnownAnswerPoint:
        if self.tolerance <= 0:
            raise ValueError(f"tolerance must be positive, got {self.tolerance}")
        return self


class ValidationConfig(BaseModel):
    """Configuration for the runtime validation framework (`core/validation.py`).

    `known_answer` is optional: a run without known-answer points still gets
    the baseline structural checks (index alignment, NaN propagation) — see
    `docs/validation.md`.
    """

    model_config = ConfigDict(frozen=True)

    known_answer: list[KnownAnswerPoint] = []


class RunConfig(BaseModel):
    """Fully describes one pipeline execution.

    `model_name` and `params` are recorded here for reproducibility and
    experiment tracking — a saved `RunConfig` plus a commit hash should be
    enough to know what was run and with what parameters. They are not used
    by the pipeline to look up a `Factor` implementation: the caller passes
    the `Factor` and its validated `FactorParams` directly (DD-008). Keeping
    a copy of the parameter values here means the experiment record doesn't
    depend on the `Factor` instance still existing or being importable later.
    """

    model_config = ConfigDict(frozen=True)

    model_name: str
    params: dict[str, Any] = {}
    dataset: DatasetConfig
    date_range: DateRange = DateRange()
    validation: ValidationConfig = ValidationConfig()

    @model_validator(mode="after")
    def _check_model_name_not_blank(self) -> RunConfig:
        if not self.model_name.strip():
            raise ValueError("model_name must not be blank")
        return self
