"""A small, reusable benchmarking harness for `Factor` implementations.

Replaces ad hoc, one-off timing scripts (e.g. hand-run snippets pasted into a
`research/<model>/README.md`) with a single function every model can use.
See CLAUDE.md: "benchmark before optimizing, and only optimize what the
benchmark says is slow" — this exists so "record actual runtime
characteristics" means running the same measurement code for every model,
not re-deriving ad hoc timing logic each time.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median
from time import perf_counter

import pandas as pd

from modelforge.core.factor import Factor, FactorParams


@dataclass(frozen=True)
class BenchmarkResult:
    """Timing statistics from repeatedly calling `factor.compute` against
    the same input. `repeats` independent measurements rather than one, so a
    single slow outlier (e.g. a GC pause) doesn't stand in for "the"
    runtime."""

    factor_name: str
    n_observations: int
    repeats: int
    min_seconds: float
    mean_seconds: float
    median_seconds: float
    max_seconds: float


def benchmark_factor(
    factor: Factor, params: FactorParams, data: pd.Series, repeats: int = 5
) -> BenchmarkResult:
    """Measure `factor.compute(data, params)`'s wall-clock runtime, repeated
    `repeats` times."""
    if repeats < 1:
        raise ValueError(f"repeats must be positive, got {repeats}")

    timings: list[float] = []
    for _ in range(repeats):
        start = perf_counter()
        factor.compute(data, params)
        timings.append(perf_counter() - start)

    return BenchmarkResult(
        factor_name=factor.name,
        n_observations=len(data),
        repeats=repeats,
        min_seconds=min(timings),
        mean_seconds=mean(timings),
        median_seconds=median(timings),
        max_seconds=max(timings),
    )
