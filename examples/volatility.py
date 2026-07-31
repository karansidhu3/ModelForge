"""End-to-end example: load a CSV, run the volatility factor through the
pipeline, inspect the validated result (including the returns intermediate).

Self-contained: generates its own small synthetic price series into a
temporary CSV. Run:

    python examples/volatility.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from modelforge.core.config import DatasetConfig, RunConfig
from modelforge.core.pipeline import run_pipeline
from modelforge.models.volatility import VolatilityFactor, VolatilityParams

WINDOW = 5

# A synthetic, deterministic price series — not real market data.
SAMPLE_PRICES = [
    100.0, 103.0, 98.0, 105.0, 110.0, 101.0, 108.0, 115.0,
    107.0, 112.0, 120.0, 114.0, 122.0, 128.0, 119.0,
]  # fmt: skip


def _write_sample_csv(path: Path) -> None:
    dates = pd.date_range("2024-01-01", periods=len(SAMPLE_PRICES), freq="D")
    pd.DataFrame({"date": dates, "value": SAMPLE_PRICES}).to_csv(path, index=False)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = Path(tmp_dir) / "sample_prices.csv"
        _write_sample_csv(csv_path)

        config = RunConfig(
            model_name="volatility",
            params={"window": WINDOW},
            dataset=DatasetConfig(path=csv_path),
        )
        factor = VolatilityFactor(window=WINDOW)
        params = VolatilityParams(window=WINDOW)

        result = run_pipeline(config, factor, params)

    print(f"Ran {factor.name}: {factor.describe()}")
    print(f"Loaded {len(result.data)} observations")
    print(f"Runtime: {result.runtime_seconds * 1000:.3f} ms")
    print(f"Validation passed: {result.validation.passed}")
    for issue in result.validation.issues:
        print(f"  [{issue.severity}] {issue.check}: {issue.message}")
    print()
    print("Returns (intermediate):")
    print(result.factor_result.intermediates["returns"].to_string())
    print()
    print("Volatility:")
    print(result.factor_result.series.to_string())
    print()
    print(
        f"Recorded as experiment {result.experiment.run_id} under "
        f"experiments/runs/. Run `modelforge experiments list` to see every "
        f"tracked run so far."
    )


if __name__ == "__main__":
    main()
