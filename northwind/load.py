"""Read the Northwind workbook and check it has the expected structure."""

import hashlib
from pathlib import Path

import pandas as pd

EXPECTED_COLUMNS = {
    "Orders Details": ["OrderID", "ProductID", "UnitPrice", "Quantity", "Discount"],
    "Orders": [
        "OrderID", "CustomerID", "EmployeeID", "OrderDate", "RequiredDate",
        "ShippedDate", "ShipVia", "Freight", "ShipCountry",
    ],
    "Customers": ["CustomerID", "CompanyName", "Country"],
    "Product": [
        "ProductID", "ProductName", "SupplierID", "CategoryID",
        "UnitsInStock", "UnitsOnOrder", "ReorderLevel", "Discontinued",
    ],
    "Categories": ["CategoryID", "CategoryName"],
    "Suppliers": ["SupplierID", "CompanyName", "Country"],
    "Shippers": ["ShipperID", "CompanyName"],
    "Employees": ["EmployeeID", "FirstName", "LastName"],
}


class SchemaError(ValueError):
    """Raised when the workbook lacks a required sheet or column."""


def file_sha256(path):
    """Return the SHA-256 fingerprint of a file.

    Args:
        path (str | pathlib.Path): File to fingerprint.

    Returns:
        str: Hex digest of the file contents.
    """
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_schema(sheets):
    """Check that every required sheet and column is present.

    Args:
        sheets (dict[str, pandas.DataFrame]): Sheets keyed by sheet name.

    Returns:
        None.

    Raises:
        SchemaError: If a required sheet or column is missing.
    """
    missing_sheets = [name for name in EXPECTED_COLUMNS if name not in sheets]
    if missing_sheets:
        raise SchemaError(f"Missing sheet(s): {', '.join(missing_sheets)}")
    for name, columns in EXPECTED_COLUMNS.items():
        missing = [col for col in columns if col not in sheets[name].columns]
        if missing:
            raise SchemaError(f"Sheet '{name}' is missing column(s): {', '.join(missing)}")


def load_workbook(path):
    """Read all sheets of the workbook and validate their structure.

    Args:
        path (str | pathlib.Path): Workbook to read.

    Returns:
        dict[str, pandas.DataFrame]: Every sheet, keyed by sheet name.

    Raises:
        FileNotFoundError: If the workbook does not exist.
        SchemaError: If a required sheet or column is missing.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Workbook not found: {path}")
    sheets = pd.read_excel(path, sheet_name=None)
    validate_schema(sheets)
    return sheets
