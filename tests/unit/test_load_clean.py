"""Unit tests for loading and cleaning."""

import pandas as pd
import pytest

from northwind.clean import clean_tables
from northwind.load import SchemaError, file_sha256, load_workbook, validate_schema


def test_missing_sheet_raises(sheets):
    del sheets["Shippers"]
    with pytest.raises(SchemaError, match="Shippers"):
        validate_schema(sheets)


def test_missing_column_raises(sheets):
    sheets["Orders"] = sheets["Orders"].drop(columns=["Freight"])
    with pytest.raises(SchemaError, match="Freight"):
        validate_schema(sheets)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_workbook(tmp_path / "nope.xlsx")


def test_fingerprint_is_stable(synthetic_workbook):
    assert file_sha256(synthetic_workbook) == file_sha256(synthetic_workbook)
    assert len(file_sha256(synthetic_workbook)) == 64


def test_discounts_rounded_to_two_decimals(sheets):
    cleaned = clean_tables(sheets)
    assert cleaned["Orders Details"]["Discount"].tolist() == [0.0, 0.05, 0.1, 0.0, 0.0]


def test_leftover_columns_dropped(sheets):
    cleaned = clean_tables(sheets)
    for col in ("Cheap", "IsCheap"):
        assert col not in cleaned["Product"].columns
    assert "Picture" not in cleaned["Categories"].columns
    assert "Price" in cleaned["Product"].columns  # kept, but never used for revenue


def test_unshipped_date_stays_missing(sheets):
    cleaned = clean_tables(sheets)
    shipped = cleaned["Orders"]["ShippedDate"]
    assert pd.api.types.is_datetime64_any_dtype(shipped)
    assert shipped.isna().sum() == 1


def test_input_not_modified(sheets):
    before = sheets["Orders Details"]["Discount"].copy()
    clean_tables(sheets)
    pd.testing.assert_series_equal(sheets["Orders Details"]["Discount"], before)
