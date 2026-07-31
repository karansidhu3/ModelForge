"""Simple moving average: the average of the last `window` observations.

See `research/moving_average/README.md` for the plain-English explanation,
the mathematical definition, and the documented assumptions this
implementation makes (evenly spaced-or-not observations, no corporate-action
adjustment, NaN-in-window semantics).
"""

from __future__ import annotations

import pandas as pd
from pydantic import Field

from modelforge.core.factor import FactorParams, FactorResult


class MovingAverageParams(FactorParams):
    """`window` is the number of trailing observations averaged at each
    point. Must be positive — a zero or negative window has no meaning for
    this model."""

    window: int = Field(gt=0)


class MovingAverageFactor:
    """Simple moving average over the last `window` observations.

    `window` is fixed at construction (which sets `required_history`); the
    `params` passed to `compute` must declare the same window. This is
    intentionally redundant rather than inferring `required_history` from
    `params` alone: it lets the pipeline and validation framework know a
    factor instance's required history without needing to have already
    called `compute`, and it catches a caller passing mismatched params
    loudly instead of silently computing against the wrong window.
    """

    name = "moving_average"

    def __init__(self, window: int) -> None:
        if window < 1:
            raise ValueError(f"window must be positive, got {window}")
        self.required_history = window

    def compute(self, data: pd.Series, params: FactorParams) -> FactorResult:
        assert isinstance(params, MovingAverageParams)
        if params.window != self.required_history:
            raise ValueError(
                f"{self.name} was constructed with window={self.required_history} "
                f"but received params.window={params.window}"
            )

        series = data.rolling(window=params.window, min_periods=params.window).mean()
        series.name = self.name
        return FactorResult(series=series)

    def describe(self) -> str:
        return (
            f"Simple moving average: the mean of the last {self.required_history} "
            "observations at each point."
        )
