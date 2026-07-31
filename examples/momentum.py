"""End-to-end example: load a CSV, run the momentum factor through the
pipeline, inspect the validated result.

Self-contained: generates its own small synthetic price series into a
temporary CSV. Run:

    python examples/momentum.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from modelforge.core.config import DatasetConfig, RunConfig
from modelforge.core.pipeline import run_pipeline
from modelforge.models.momentum import MomentumFactor, MomentumParams

LOOKBACK = 3

# A synthetic, deterministic price series — not real market data.
SAMPLE_PRICES = [
    100.0, 102.0, 101.0, 105.0, 108.0, 104.0, 110.0, 112.0,
    109.0, 115.0, 118.0, 116.0, 120.0, 123.0, 121.0,
]  # fmt: skip


def _write_sample_csv(path: Path) -> None:
    dates = pd.date_range("2024-01-01", periods=len(SAMPLE_PRICES), freq="D")
    pd.DataFrame({"date": dates, "value": SAMPLE_PRICES}).to_csv(path, index=False)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = Path(tmp_dir) / "sample_prices.csv"
        _write_sample_csv(csv_path)

        config = RunConfig(
            model_name="momentum",
            params={"lookback": LOOKBACK},
            dataset=DatasetConfig(path=csv_path),
        )
        factor = MomentumFactor(lookback=LOOKBACK)
        params = MomentumParams(lookback=LOOKBACK)

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
        f"Recorded as experiment {result.experiment.run_id} under "
        f"experiments/runs/. Run `modelforge experiments list` to see every "
        f"tracked run so far."
    )


if __name__ == "__main__":
    main()
