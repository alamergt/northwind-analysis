"""Unit tests for loading and cleaning."""

import pandas as pd
import pytest

from northwind.clean import clean_tables
from northwind.load import SchemaError, file_sha256, load_workbook, validate_schema


def test_missing_sheet_raises(sheets):
    """Check that a missing sheet raises SchemaError naming it.

    Args:
        sheets (dict[str, pandas.DataFrame]): Fresh synthetic sheets.

    Returns:
        None.
    """
    del sheets["Shippers"]
    with pytest.raises(SchemaError, match="Shippers"):
        validate_schema(sheets)


def test_missing_column_raises(sheets):
    """Check that a missing column raises SchemaError naming it.

    Args:
        sheets (dict[str, pandas.DataFrame]): Fresh synthetic sheets.

    Returns:
        None.
    """
    sheets["Orders"] = sheets["Orders"].drop(columns=["Freight"])
    with pytest.raises(SchemaError, match="Freight"):
        validate_schema(sheets)


def test_missing_file_raises(tmp_path):
    """Check that a nonexistent workbook raises FileNotFoundError.

    Args:
        tmp_path (pathlib.Path): Empty per-test folder.

    Returns:
        None.
    """
    with pytest.raises(FileNotFoundError):
        load_workbook(tmp_path / "nope.xlsx")


def test_fingerprint_is_stable(synthetic_workbook):
    """Check that the file SHA-256 is repeatable and 64 characters.

    Args:
        synthetic_workbook (pathlib.Path): Synthetic .xlsx file.

    Returns:
        None.
    """
    assert file_sha256(synthetic_workbook) == file_sha256(synthetic_workbook)
    assert len(file_sha256(synthetic_workbook)) == 64


def test_discounts_rounded_to_two_decimals(sheets):
    """Check that cleaning rounds discounts to two decimals.

    Args:
        sheets (dict[str, pandas.DataFrame]): Fresh synthetic sheets.

    Returns:
        None.
    """
    cleaned = clean_tables(sheets)
    assert cleaned["Orders Details"]["Discount"].tolist() == [0.0, 0.05, 0.1, 0.0, 0.0]


def test_leftover_columns_dropped(sheets):
    """Check that unused columns are dropped and Price is kept.

    Args:
        sheets (dict[str, pandas.DataFrame]): Fresh synthetic sheets.

    Returns:
        None.
    """
    cleaned = clean_tables(sheets)
    for col in ("Cheap", "IsCheap"):
        assert col not in cleaned["Product"].columns
    assert "Picture" not in cleaned["Categories"].columns
    assert "Price" in cleaned["Product"].columns  # kept, but never used for revenue


def test_unshipped_date_stays_missing(sheets):
    """Check that an unshipped order keeps a missing ShippedDate.

    Args:
        sheets (dict[str, pandas.DataFrame]): Fresh synthetic sheets.

    Returns:
        None.
    """
    cleaned = clean_tables(sheets)
    shipped = cleaned["Orders"]["ShippedDate"]
    assert pd.api.types.is_datetime64_any_dtype(shipped)
    assert shipped.isna().sum() == 1


def test_input_not_modified(sheets):
    """Check that cleaning leaves the input sheets unchanged.

    Args:
        sheets (dict[str, pandas.DataFrame]): Fresh synthetic sheets.

    Returns:
        None.
    """
    before = sheets["Orders Details"]["Discount"].copy()
    clean_tables(sheets)
    pd.testing.assert_series_equal(sheets["Orders Details"]["Discount"], before)
