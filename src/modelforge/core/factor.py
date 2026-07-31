"""The Factor interface: the contract every model implements.

Defines the shape of a computation that takes validated time-series input and
produces a derived series, without knowing anything about where the input
came from or what happens to the output afterward. See
`docs/factor-interface.md` for the full design rationale.

This module does not implement any model. `core/` never depends on a
specific `Factor` implementation — see ARCHITECTURE.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import pandas as pd
from pydantic import BaseModel, ConfigDict


class FactorParams(BaseModel):
    """Base class for a model's parameters.

    Each model defines its own subclass (e.g. `MovingAverageParams` with a
    `window: int` field). Frozen so a `Factor` implementation can never
    mutate the configuration it was given, keeping `compute` pure with
    respect to its inputs.
    """

    model_config = ConfigDict(frozen=True)


@dataclass(frozen=True)
class FactorResult:
    """The output of a `Factor.compute` call.

    `series` is the factor's primary output, indexed by (a subset of) the
    input data's index. `intermediates` holds any inspectable intermediate
    calculations worth exposing (e.g. a z-score's rolling mean and rolling
    standard deviation) — see docs/validation.md on why these should be
    inspectable rather than buried inside a single opaque computation.
    """

    series: pd.Series
    intermediates: dict[str, pd.Series] = field(default_factory=dict)


@runtime_checkable
class Factor(Protocol):
    """A Factor computes a derived series from validated time-series input.

    Implementations must be pure with respect to their declared config: the
    same input series and config always produce the same output. No
    implementation performs I/O — all data arrives already loaded.
    """

    name: str
    """A short, stable identifier used in experiment records and CLI output."""

    required_history: int
    """Minimum number of observations needed before this factor can produce
    its first valid output value (e.g. a 20-day moving average needs 20)."""

    def compute(self, data: pd.Series, params: FactorParams) -> FactorResult:
        """Compute the factor's output over `data`.

        Must not mutate `data`. Must return a result whose index aligns with
        (a subset of) `data`'s index — no silent reindexing.
        """
        ...

    def describe(self) -> str:
        """A short, human-readable description of what this factor computes,
        suitable for CLI help text and generated reports."""
        ...
