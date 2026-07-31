"""Tests for `data.loaders.load_csv`.

Uses `tests/fixtures/*.csv` for the happy paths (see `docs/testing-strategy.md`
on shared fixture datasets) and `tmp_path`-generated files for the malformed
cases, since those are one-off per test rather than reusable fixtures.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from modelforge.data.loaders import load_csv


def test_loads_a_clean_series(fixtures_dir: Path) -> None:
    series = load_csv(fixtures_dir / "clean_series.csv")

    assert series.dtype == np.float64
    assert series.index.name == "date"
    assert series.name == "value"
    assert len(series) == 10
    assert series.iloc[0] == 1.0
    assert series.iloc[-1] == 10.0


def test_index_is_sorted_ascending(fixtures_dir: Path) -> None:
    series = load_csv(fixtures_dir / "clean_series.csv")
    assert series.index.is_monotonic_increasing


def test_out_of_order_rows_are_sorted_on_load(tmp_path: Path) -> None:
    path = tmp_path / "unsorted.csv"
    path.write_text("date,value\n2024-01-03,3.0\n2024-01-01,1.0\n2024-01-02,2.0\n")

    series = load_csv(path)

    index = pd.DatetimeIndex(series.index)
    assert list(index.strftime("%Y-%m-%d")) == ["2024-01-01", "2024-01-02", "2024-01-03"]
    assert list(series.to_numpy()) == [1.0, 2.0, 3.0]


def test_blank_values_are_preserved_as_nan_not_dropped(fixtures_dir: Path) -> None:
    series = load_csv(fixtures_dir / "with_nan.csv")

    assert len(series) == 10
    assert pd.isna(series.loc["2024-01-05"])
    assert series.loc["2024-01-06"] == 6.0


def test_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_csv(tmp_path / "does_not_exist.csv")


def test_empty_file_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("date,value\n")

    with pytest.raises(ValueError, match="no rows"):
        load_csv(path)


def test_missing_required_column_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "missing_column.csv"
    path.write_text("date,price\n2024-01-01,1.0\n")

    with pytest.raises(ValueError, match="missing required column"):
        load_csv(path)


def test_duplicate_dates_raise_value_error(tmp_path: Path) -> None:
    path = tmp_path / "duplicates.csv"
    path.write_text("date,value\n2024-01-01,1.0\n2024-01-01,2.0\n")

    with pytest.raises(ValueError, match="duplicate dates"):
        load_csv(path)


def test_non_numeric_value_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "non_numeric.csv"
    path.write_text("date,value\n2024-01-01,not_a_number\n")

    with pytest.raises(ValueError, match="non-numeric"):
        load_csv(path)


def test_unparseable_date_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "bad_date.csv"
    path.write_text("date,value\nnot_a_date,1.0\n")

    with pytest.raises(ValueError, match="unparseable"):
        load_csv(path)


def test_respects_custom_column_names(tmp_path: Path) -> None:
    path = tmp_path / "custom.csv"
    path.write_text("day,price\n2024-01-01,1.0\n2024-01-02,2.0\n")

    series = load_csv(path, date_column="day", value_column="price")

    assert series.name == "price"
    assert series.index.name == "day"
