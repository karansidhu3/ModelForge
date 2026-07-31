"""Volatility: the rolling standard deviation of a series' simple returns.

See `research/volatility/README.md` for the plain-English explanation, the
mathematical definition, and the documented assumptions (simple vs. log
returns, not annualized, strictly-positive-input assumption).
"""

from __future__ import annotations

import pandas as pd
from pydantic import Field

from modelforge.core.factor import FactorParams, FactorResult


class VolatilityParams(FactorParams):
    """`window` is the number of trailing returns the standard deviation is
    computed over. Must be positive."""

    window: int = Field(gt=0)


class VolatilityFactor:
    """Rolling standard deviation (sample, ddof=1) of simple returns over
    the last `window` returns.

    `window` is fixed at construction (which sets `required_history`); the
    `params` passed to `compute` must declare the same window — same
    redundant-by-design shape as `MovingAverageFactor`.
    """

    name = "volatility"

    def __init__(self, window: int) -> None:
        if window < 1:
            raise ValueError(f"window must be positive, got {window}")
        self.required_history = window + 1

    def compute(self, data: pd.Series, params: FactorParams) -> FactorResult:
        assert isinstance(params, VolatilityParams)
        if params.window != self.required_history - 1:
            raise ValueError(
                f"{self.name} was constructed with window={self.required_history - 1} "
                f"but received params.window={params.window}"
            )

        returns = data.pct_change()
        returns.name = "returns"
        volatility = returns.rolling(window=params.window, min_periods=params.window).std()
        volatility.name = self.name
        return FactorResult(series=volatility, intermediates={"returns": returns})

    def describe(self) -> str:
        return (
            f"Volatility: the standard deviation of the last {self.required_history - 1} "
            "returns, at each point."
        )
