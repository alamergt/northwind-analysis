"""Shared fixtures: a small made-up workbook with known answers."""

import pandas as pd
import pytest

from northwind import Config, build_model, clean_tables, load_workbook

# Expected values for the synthetic workbook, worked out by hand:
#   order 1: 10*5 + 20*2*(1-0.05) = 50 + 38 = 88 net, 90 gross, 7 units
#   order 2: 12*10*(1-0.10)       = 108 net, 120 gross, 10 units (late)
#   order 3: 25*4                 = 100 net, 100 gross, 4 units (unshipped)
#   order 4: 8*5                  = 40 net, 40 gross, 5 units
SYNTHETIC = {
    "net_revenue": 336.0,
    "gross_revenue": 350.0,
    "orders": 4,
    "order_lines": 5,
    "shipped": 3,
    "late": 1,
}


def synthetic_sheets():
    """Return the eight sheets of a tiny Northwind-shaped workbook.

    Args:
        None.

    Returns:
        dict[str, pandas.DataFrame]: Sheets keyed by sheet name.
    """
    ts = pd.Timestamp
    return {
        "Categories": pd.DataFrame({
            "CategoryID": [1, 2], "CategoryName": ["Beverages", "Seafood"],
            "Description": ["d1", "d2"], "Picture": [None, None],
        }),
        "Customers": pd.DataFrame({
            "CustomerID": ["AAA", "BBB", "CCC"],
            "CompanyName": ["Alpha GmbH", "Beta Inc", "Gamma SA"],
            "Country": ["Germany", "USA", "France"],
        }),
        "Employees": pd.DataFrame({
            "EmployeeID": [1, 2], "FirstName": ["Ann", "Bo"], "LastName": ["Lee", "Ng"],
        }),
        "Orders Details": pd.DataFrame({
            "OrderID": [1, 1, 2, 3, 4],
            "ProductID": [1, 2, 1, 2, 3],
            "UnitPrice": [10.0, 20.0, 12.0, 25.0, 8.0],
            "Quantity": [5, 2, 10, 4, 5],
            "Discount": [0.0, 0.0499999, 0.1000001, 0.0, 0.0],
        }),
        "Orders": pd.DataFrame({
            "OrderID": [1, 2, 3, 4],
            "CustomerID": ["AAA", "AAA", "BBB", "BBB"],
            "EmployeeID": [1, 2, 1, 2],
            "OrderDate": [ts("1997-01-10"), ts("1998-04-01"), ts("1998-05-01"), ts("1997-10-15")],
            "RequiredDate": [ts("1997-02-07"), ts("1998-04-29"), ts("1998-05-29"), ts("1997-11-12")],
            "ShippedDate": [ts("1997-01-15"), ts("1998-05-02"), pd.NaT, ts("1997-10-20")],
            "ShipVia": [1, 2, 3, 1],
            "Freight": [10.0, 30.0, 5.0, 20.0],
            "ShipCountry": ["Germany", "Germany", "USA", "Canada"],
        }),
        "Shippers": pd.DataFrame({
            "ShipperID": [1, 2, 3], "CompanyName": ["Fast", "Mid", "Slow"],
        }),
        "Product": pd.DataFrame({
            "ProductID": [1, 2, 3],
            "ProductName": ["Tea", "Fish", "Juice"],
            "SupplierID": [1, 1, 2],
            "CategoryID": [1, 2, 1],
            "Price": [11.0, 22.0, 9.0],
            "Cheap": ["f", "f", "t"],
            "UnitsInStock": [0, 50, 3],
            "UnitsOnOrder": [10, 0, 0],
            "ReorderLevel": [5, 0, 10],
            "Discontinued": [False, False, True],
            "IsCheap": [False, False, True],
        }),
        "Suppliers": pd.DataFrame({
            "SupplierID": [1, 2], "CompanyName": ["Sup One", "Sup Two"],
            "Country": ["UK", "Japan"],
        }),
    }


@pytest.fixture
def sheets():
    """Fresh copy of the synthetic sheets for each test."""
    return synthetic_sheets()


@pytest.fixture(scope="session")
def synthetic_workbook(tmp_path_factory):
    """Path to the synthetic sheets written as a real .xlsx file."""
    path = tmp_path_factory.mktemp("data") / "synthetic.xlsx"
    with pd.ExcelWriter(path) as writer:
        for name, frame in synthetic_sheets().items():
            frame.to_excel(writer, sheet_name=name, index=False)
    return path


@pytest.fixture(scope="session")
def synthetic_model(synthetic_workbook):
    """Model built from the synthetic workbook through the full pipeline."""
    config = Config(cutoff=pd.Timestamp("1998-05-06"))
    return build_model(clean_tables(load_workbook(synthetic_workbook)), config)


@pytest.fixture
def config():
    """Default configuration."""
    return Config()
