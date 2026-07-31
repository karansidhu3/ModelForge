"""Mean reversion: the percentage gap between a series and its own trailing
moving average.

See `research/mean_reversion/README.md` for the plain-English explanation,
the mathematical definition, how this differs from `models/z_score.py`, and
why this computes its own rolling mean rather than depending on
`MovingAverageFactor`.
"""

from __future__ import annotations

import pandas as pd
from pydantic import Field

from modelforge.core.factor import FactorParams, FactorResult


class MeanReversionParams(FactorParams):
    """`window` is the size of the trailing window the moving average is
    computed over. Must be positive."""

    window: int = Field(gt=0)


class MeanReversionFactor:
    """Percentage deviation from a trailing moving average:
    `(x[t] - MA[t]) / MA[t]`.

    `window` is fixed at construction (which sets `required_history`); the
    `params` passed to `compute` must declare the same window — same
    redundant-by-design shape as `MovingAverageFactor`.
    """

    name = "mean_reversion"

    def __init__(self, window: int) -> None:
        if window < 1:
            raise ValueError(f"window must be positive, got {window}")
        self.required_history = window

    def compute(self, data: pd.Series, params: FactorParams) -> FactorResult:
        assert isinstance(params, MeanReversionParams)
        if params.window != self.required_history:
            raise ValueError(
                f"{self.name} was constructed with window={self.required_history} "
                f"but received params.window={params.window}"
            )

        moving_average = data.rolling(window=params.window, min_periods=params.window).mean()
        moving_average.name = "moving_average"

        series = (data - moving_average) / moving_average
        series.name = self.name

        return FactorResult(series=series, intermediates={"moving_average": moving_average})

    def describe(self) -> str:
        return (
            f"Mean reversion: the percentage gap between x[t] and the mean of the "
            f"last {self.required_history} observations, at each point."
        )
