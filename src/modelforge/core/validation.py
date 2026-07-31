"""The runtime validation framework.

Sits between "a model produced a result" and "that result is trusted." Runs
as part of every pipeline execution, against whatever data was actually
loaded for that run — this is deliberately separate from unit tests, which
validate the *code* once at development time. See `docs/validation.md` and
DD-006 in `DESIGN_DECISIONS.md` for why this is a shared layer rather than
assertions scattered inside each model.

What this checks:
    - Structural correctness: the result's index is a genuine (non-reordered,
      non-duplicated) subset of the input's index — catching silent
      reindexing.
    - NaN propagation: a heuristic flag (not a hard failure) for NaN values
      appearing after a factor's `required_history` has been satisfied, where
      the corresponding input point was itself not NaN.
    - Known-answer spot checks: where `RunConfig.validation.known_answer`
      specifies expected values, the result is checked against them
      numerically, within tolerance.

What this does not check: whether a result is *good* in a financial sense.
See the non-goals in `CLAUDE.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from modelforge.core.config import KnownAnswerPoint, ValidationConfig
from modelforge.core.factor import Factor, FactorResult

Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class ValidationIssue:
    """A single finding from the validation framework."""

    check: str
    severity: Severity
    message: str


@dataclass(frozen=True)
class ValidationReport:
    """The outcome of validating one `FactorResult` against its input data.

    `passed` reflects only `error`-severity issues. `warning`-severity issues
    are surfaced but do not fail the run — see the module docstring for which
    checks use which severity and why.
    """

    issues: list[ValidationIssue]

    @property
    def passed(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]


def validate_result(
    data: pd.Series, result: FactorResult, factor: Factor, config: ValidationConfig
) -> ValidationReport:
    """Validate a `Factor`'s output against the data it was computed from."""
    issues = list(_check_index_alignment(data, result.series))

    if not any(issue.severity == "error" for issue in issues):
        issues.extend(_check_nan_propagation(data, result.series, factor.required_history))

    issues.extend(_check_known_answers(result.series, config.known_answer))

    return ValidationReport(issues=issues)


def _check_index_alignment(data: pd.Series, result_series: pd.Series) -> list[ValidationIssue]:
    """The result's index must be a subset of the input's index, in the same
    relative order, with no duplicates — i.e. no silent reindexing."""
    if result_series.index.has_duplicates:
        return [
            ValidationIssue("index_alignment", "error", "result index contains duplicate labels")
        ]

    positions = data.index.get_indexer(result_series.index)
    if (positions == -1).any():
        unknown = list(result_series.index[positions == -1])
        return [
            ValidationIssue(
                "index_alignment",
                "error",
                f"result index contains labels not present in input data: {_sample(unknown)}",
            )
        ]

    if len(positions) > 1 and not (positions[1:] > positions[:-1]).all():
        return [
            ValidationIssue(
                "index_alignment",
                "error",
                "result index is not a strictly increasing subsequence of the input index",
            )
        ]

    return []


def _check_nan_propagation(
    data: pd.Series, result_series: pd.Series, required_history: int
) -> list[ValidationIssue]:
    """Flag (as a warning) NaN values appearing after `required_history` has
    been satisfied, where the corresponding input point was itself clean.

    This is a lightweight heuristic, not exhaustive window-aware NaN
    propagation checking: it only looks at the input value at the same
    index, not every value inside whatever window the factor actually used.
    A model-specific known-answer test is the rigorous check; this is a
    baseline sanity check that runs on every execution regardless of what
    fixtures a given run's config provides.
    """
    if required_history < 1 or result_series.empty:
        return []

    data_positions = data.index.get_indexer(result_series.index)
    warm_up_complete = data_positions >= (required_history - 1)
    result_is_nan = result_series.isna().to_numpy()
    input_is_clean = ~data.iloc[data_positions].isna().to_numpy()

    unexpected = warm_up_complete & result_is_nan & input_is_clean
    if not unexpected.any():
        return []

    offending = list(result_series.index[unexpected])
    return [
        ValidationIssue(
            "nan_propagation",
            "warning",
            f"result contains NaN after required_history ({required_history}) observations "
            f"were available, at indices where the corresponding input was not NaN: "
            f"{_sample(offending)}",
        )
    ]


def _check_known_answers(
    result_series: pd.Series, known_answer: list[KnownAnswerPoint]
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for point in known_answer:
        timestamp = pd.Timestamp(point.at)
        if timestamp not in result_series.index:
            issues.append(
                ValidationIssue(
                    "known_answer",
                    "error",
                    f"known-answer point at {point.at} not found in result index",
                )
            )
            continue

        actual = result_series.loc[timestamp]
        if pd.isna(actual):
            issues.append(
                ValidationIssue(
                    "known_answer",
                    "error",
                    f"known-answer point at {point.at}: result is NaN, expected {point.expected}",
                )
            )
            continue

        if abs(float(actual) - point.expected) > point.tolerance:
            issues.append(
                ValidationIssue(
                    "known_answer",
                    "error",
                    f"known-answer point at {point.at}: expected {point.expected}, got "
                    f"{float(actual)} (tolerance {point.tolerance})",
                )
            )

    return issues


def _sample(labels: list[object], limit: int = 5) -> str:
    shown = [str(label) for label in labels[:limit]]
    suffix = "..." if len(labels) > limit else ""
    return f"{shown}{suffix}"
