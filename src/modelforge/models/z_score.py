"""Z-score: how many standard deviations a point is from its own rolling
window's mean.

See `research/z_score/README.md` for the plain-English explanation, the
mathematical definition, and the documented zero-variance behavior.
"""

from __future__ import annotations

import pandas as pd
from pydantic import Field

from modelforge.core.factor import FactorParams, FactorResult


class ZScoreParams(FactorParams):
    """`window` is the size of the trailing window (inclusive of the current
    point) the mean and standard deviation are computed over. Must be
    positive."""

    window: int = Field(gt=0)


class ZScoreFactor:
    """Rolling z-score: `(x[t] - rolling_mean[t]) / rolling_std[t]`.

    `window` is fixed at construction (which sets `required_history`); the
    `params` passed to `compute` must declare the same window — same
    redundant-by-design shape as `MovingAverageFactor`.
    """

    name = "z_score"

    def __init__(self, window: int) -> None:
        if window < 1:
            raise ValueError(f"window must be positive, got {window}")
        self.required_history = window

    def compute(self, data: pd.Series, params: FactorParams) -> FactorResult:
        assert isinstance(params, ZScoreParams)
        if params.window != self.required_history:
            raise ValueError(
                f"{self.name} was constructed with window={self.required_history} "
                f"but received params.window={params.window}"
            )

        rolling = data.rolling(window=params.window, min_periods=params.window)
        rolling_mean = rolling.mean()
        rolling_mean.name = "rolling_mean"
        rolling_std = rolling.std()
        rolling_std.name = "rolling_std"

        # A window with zero variance makes this a genuine 0/0; pandas
        # evaluates that to NaN without raising or warning — see
        # research/z_score/README.md on why that's the correct behavior
        # here, not a case to special-case around.
        series = (data - rolling_mean) / rolling_std
        series.name = self.name

        return FactorResult(
            series=series,
            intermediates={"rolling_mean": rolling_mean, "rolling_std": rolling_std},
        )

    def describe(self) -> str:
        return (
            f"Z-score: how many standard deviations x[t] is from the mean of the "
            f"last {self.required_history} observations, at each point."
        )
