"""End-to-end example: load a CSV, run the moving-average factor through the
pipeline, inspect the validated result.

Self-contained: generates its own small synthetic price series into a
temporary CSV rather than depending on a checked-in data file, so running
this script needs no configuration beyond what's here.

Run:
    python examples/moving_average.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from modelforge.core.config import DatasetConfig, RunConfig
from modelforge.core.pipeline import run_pipeline
from modelforge.models.moving_average import MovingAverageFactor, MovingAverageParams

WINDOW = 5

# A synthetic, deterministic price series — not real market data.
SAMPLE_PRICES = [
    100.0, 101.5, 99.0, 102.0, 103.5, 101.0, 104.0, 106.5,
    105.0, 107.0, 108.5, 107.5, 109.0, 110.5, 111.0,
]  # fmt: skip


def _write_sample_csv(path: Path) -> None:
    dates = pd.date_range("2024-01-01", periods=len(SAMPLE_PRICES), freq="D")
    pd.DataFrame({"date": dates, "value": SAMPLE_PRICES}).to_csv(path, index=False)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = Path(tmp_dir) / "sample_prices.csv"
        _write_sample_csv(csv_path)

        config = RunConfig(
            model_name="moving_average",
            params={"window": WINDOW},
            dataset=DatasetConfig(path=csv_path),
        )
        factor = MovingAverageFactor(window=WINDOW)
        params = MovingAverageParams(window=WINDOW)

        result = run_pipeline(config, factor, params)

    print(f"Ran {factor.name}: {factor.describe()}")
    print(f"Loaded {len(result.data)} observations")
    print(f"Runtime: {result.runtime_seconds * 1000:.3f} ms")
    print(f"Validation passed: {result.validation.passed}")
    for issue in result.validation.issues:
        print(f"  [{issue.severity}] {issue.check}: {issue.message}")
    print()
    print(result.factor_result.series.to_string())
    print()
    print(
        "Note: experiment recording is a no-op stub in this phase (see "
        "docs/experiment-tracking.md and ROADMAP.md Phase 4). This script "
        "demonstrates the model running end-to-end through the pipeline."
    )


if __name__ == "__main__":
    main()
