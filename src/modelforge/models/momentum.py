"""Momentum: the absolute change in a series over a fixed look-back distance.

See `research/momentum/README.md` for the plain-English explanation, the
mathematical definition, and the documented assumptions (in particular, the
NaN-propagation shape this model has that a rolling-window model doesn't).
"""

from __future__ import annotations

import pandas as pd
from pydantic import Field

from modelforge.core.factor import FactorParams, FactorResult


class MomentumParams(FactorParams):
    """`lookback` is the number of observations back to compare against.
    Must be positive — a zero or negative look-back has no meaning for this
    model."""

    lookback: int = Field(gt=0)


class MomentumFactor:
    """Absolute momentum: `x[t] - x[t - lookback]`.

    `lookback` is fixed at construction (which sets `required_history`); the
    `params` passed to `compute` must declare the same look-back — same
    redundant-by-design shape as `MovingAverageFactor`, for the same reason:
    it lets the pipeline know required history without calling `compute`
    first, and it catches mismatched params loudly.
    """

    name = "momentum"

    def __init__(self, lookback: int) -> None:
        if lookback < 1:
            raise ValueError(f"lookback must be positive, got {lookback}")
        self.required_history = lookback + 1

    def compute(self, data: pd.Series, params: FactorParams) -> FactorResult:
        assert isinstance(params, MomentumParams)
        if params.lookback != self.required_history - 1:
            raise ValueError(
                f"{self.name} was constructed with lookback={self.required_history - 1} "
                f"but received params.lookback={params.lookback}"
            )

        series = data - data.shift(params.lookback)
        series.name = self.name
        return FactorResult(series=series)

    def describe(self) -> str:
        return (
            f"Momentum: the change from {self.required_history - 1} observations ago "
            "to now, at each point."
        )
