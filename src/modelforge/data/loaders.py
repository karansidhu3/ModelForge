"""CSV loading: turns a CSV file on disk into the common, validated series
format every other module in ModelForge depends on.

This is the first loader implemented (see DD-004 in `DESIGN_DECISIONS.md` and
ROADMAP.md Phase 2) because it requires no network access, and therefore no
mocking, to test deterministically. Yahoo Finance and FRED loaders follow the
same shape later but are out of scope for Phase 2.

Deliberately takes primitive arguments (`path`, column names) rather than a
`core.config.DatasetConfig` object: `data/` sits below `core/` in the layer
diagram in ARCHITECTURE.md and must not depend on it. `core/pipeline.py` is
responsible for unpacking a `RunConfig`'s dataset section into the arguments
this module expects.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_csv(path: Path, date_column: str = "date", value_column: str = "value") -> pd.Series:
    """Load a single time series from a CSV file.

    Returns a `pd.Series` of dtype `float64`, indexed by `date_column`
    (parsed to `datetime64[ns]`) and sorted ascending. Blank cells in
    `value_column` are preserved as `NaN` rather than dropped — whether NaNs
    in the input are acceptable is a `Factor` implementation's decision, not
    the loader's (see docs/factor-interface.md).

    Does not fill gaps in the date index or assume a trading-day calendar:
    the series reflects exactly the rows present in the file, in date order.

    Raises:
        FileNotFoundError: `path` does not exist.
        ValueError: the file has no data rows, is missing `date_column` or
            `value_column`, contains duplicate dates, or `value_column`
            contains a value that cannot be coerced to a float.
    """
    if not path.exists():
        raise FileNotFoundError(f"dataset file not found: {path}")

    frame = pd.read_csv(path)

    if frame.empty:
        raise ValueError(f"dataset at {path} contains no rows")

    missing_columns = {date_column, value_column} - set(frame.columns)
    if missing_columns:
        raise ValueError(
            f"dataset at {path} is missing required column(s): {sorted(missing_columns)} "
            f"(found columns: {list(frame.columns)})"
        )

    try:
        dates = pd.to_datetime(frame[date_column], errors="raise")
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"dataset at {path} has an unparseable value in '{date_column}': {exc}"
        ) from exc

    if dates.duplicated().any():
        duplicates = sorted(dates[dates.duplicated()].dt.date.astype(str).unique())
        raise ValueError(f"dataset at {path} has duplicate dates in '{date_column}': {duplicates}")

    try:
        values = pd.to_numeric(frame[value_column], errors="raise").astype("float64")
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"dataset at {path} has a non-numeric value in '{value_column}': {exc}"
        ) from exc

    series = pd.Series(
        values.to_numpy(), index=pd.Index(dates, name=date_column), name=value_column
    )
    return series.sort_index()
