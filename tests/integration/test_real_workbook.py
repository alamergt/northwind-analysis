"""Integration tests: the model must reproduce known totals of the real workbook."""

import pytest

from northwind import Config, load_model
from northwind.config import CONTROL_TOTALS as CT
from northwind.load import file_sha256

pytestmark = pytest.mark.integration

if not Config().workbook.exists():
    pytest.skip("real workbook not present", allow_module_level=True)


@pytest.fixture(scope="module")
def model():
    return load_model()


def test_join_row_counts(model):
    assert len(model.order_lines) == CT["order_lines"]
    assert len(model.orders) == CT["orders"]
    assert len(model.products) == CT["products"]


def test_no_missing_keys_after_joins(model):
    key_cols = {
        "order_lines": ["OrderID", "CustomerID", "CustomerName", "ProductName", "CategoryName", "Market"],
        "orders": ["CustomerName", "ShipperName", "EmployeeName", "DestRegion", "SizeBand"],
        "products": ["CategoryName", "SupplierName"],
    }
    for table, cols in key_cols.items():
        assert getattr(model, table)[cols].notna().all().all(), table


def test_revenue_control_totals(model):
    assert round(model.order_lines["NetRevenue"].sum()) == CT["net_revenue"]
    assert round(model.order_lines["GrossRevenue"].sum()) == CT["gross_revenue"]
    assert model.orders["NetRevenue"].sum() == pytest.approx(model.order_lines["NetRevenue"].sum())


def test_order_control_totals(model):
    o = model.orders
    assert o["IsShipped"].sum() == CT["orders_shipped"]
    assert (~o["IsShipped"]).sum() == CT["orders_unshipped"]
    assert o["IsLate"].sum() == CT["orders_late"]
    assert o["CustomerID"].nunique() == CT["customers_with_orders"]
    assert o["ProcessingDays"].notna().sum() == CT["orders_shipped"]


def test_product_control_totals(model):
    active = model.products[~model.products["Discontinued"]]
    assert len(active) == CT["active_products"]
    assert (active["ReorderLevel"] == 0).sum() == CT["active_without_reorder_rule"]


def test_markets_sum_to_total(model):
    by_market = model.order_lines.groupby("Market")["NetRevenue"].sum()
    assert by_market.sum() == pytest.approx(model.order_lines["NetRevenue"].sum())
    assert set(by_market.index) >= {"USA", "Germany", "Brazil", "France"}


def test_every_order_in_a_size_band(model):
    assert model.orders["SizeBand"].notna().all()
    assert model.orders["SizeBand"].nunique() == 4


def test_allowed_windows_are_standard(model):
    assert set(model.orders["AllowedDays"].unique()) <= {14.0, 28.0, 42.0}


def test_input_not_modified(model):
    path = Config().workbook
    before = file_sha256(path)
    load_model()
    assert file_sha256(path) == before
