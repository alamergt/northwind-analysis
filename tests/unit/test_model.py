"""Unit tests for the joined model, using the synthetic workbook."""

import math

import pytest

from northwind import Config, build_model, clean_tables
from northwind.model import ModelError
from tests.conftest import SYNTHETIC


def test_row_counts(synthetic_model):
    """Check order-line and order counts against hand values.

    Args:
        synthetic_model (northwind.model.Model): Model of the synthetic
            workbook.

    Returns:
        None.
    """
    assert len(synthetic_model.order_lines) == SYNTHETIC["order_lines"]
    assert len(synthetic_model.orders) == SYNTHETIC["orders"]


def test_revenue_totals_match_hand_calculation(synthetic_model):
    """Check net and gross revenue against the hand calculation.

    Args:
        synthetic_model (northwind.model.Model): Model of the synthetic
            workbook.

    Returns:
        None.
    """
    lines, orders = synthetic_model.order_lines, synthetic_model.orders
    assert lines["NetRevenue"].sum() == pytest.approx(SYNTHETIC["net_revenue"])
    assert lines["GrossRevenue"].sum() == pytest.approx(SYNTHETIC["gross_revenue"])
    assert orders["NetRevenue"].sum() == pytest.approx(SYNTHETIC["net_revenue"])
    assert orders.set_index("OrderID")["NetRevenue"].to_dict() == pytest.approx(
        {1: 88.0, 2: 108.0, 3: 100.0, 4: 40.0})


def test_revenue_uses_line_price_not_list_price(synthetic_model):
    """Check that revenue uses the order-line price, not list price.

    Args:
        synthetic_model (northwind.model.Model): Model of the synthetic
            workbook.

    Returns:
        None.
    """
    # Product 1 has list price 11 but was sold at 10 and 12.
    tea = synthetic_model.order_lines.query("ProductID == 1")
    assert sorted(tea["UnitPrice"]) == [10.0, 12.0]


def test_order_measures(synthetic_model):
    """Check processing days, shipped and late flags, units, freight.

    Args:
        synthetic_model (northwind.model.Model): Model of the synthetic
            workbook.

    Returns:
        None.
    """
    o = synthetic_model.orders.set_index("OrderID")
    assert o.loc[1, "ProcessingDays"] == 5 and o.loc[2, "ProcessingDays"] == 31
    assert math.isnan(o.loc[3, "ProcessingDays"])
    assert o["IsShipped"].sum() == SYNTHETIC["shipped"]
    assert o["IsLate"].sum() == SYNTHETIC["late"] and bool(o.loc[2, "IsLate"])
    assert o.loc[1, "Units"] == 7 and o.loc[1, "FreightPerUnit"] == pytest.approx(10 / 7)


def test_markets_and_regions(synthetic_model):
    """Check market comes from the customer, region from ship country.

    Args:
        synthetic_model (northwind.model.Model): Model of the synthetic
            workbook.

    Returns:
        None.
    """
    o = synthetic_model.orders.set_index("OrderID")
    # Order 4: customer is in the USA (market) but shipped to Canada (destination).
    assert o.loc[4, "Market"] == "USA"
    assert o.loc[4, "DestRegion"] == "North America"
    assert o.loc[1, "DestRegion"] == "Western Europe"


def test_customer_without_orders_kept(synthetic_model):
    """Check that a customer without orders is kept in the model.

    Args:
        synthetic_model (northwind.model.Model): Model of the synthetic
            workbook.

    Returns:
        None.
    """
    assert "CCC" in set(synthetic_model.customers["CustomerID"])
    assert "CCC" not in set(synthetic_model.orders["CustomerID"])


def test_product_demand(synthetic_model):
    """Check recent monthly demand over the 90-day window.

    Args:
        synthetic_model (northwind.model.Model): Model of the synthetic
            workbook.

    Returns:
        None.
    """
    p = synthetic_model.products.set_index("ProductID")
    # Recent window 6 Feb - 6 May 1998: product 1 sold 10 (order 2), product 2 sold 4 (order 3).
    assert p.loc[1, "RecentMonthlyDemand"] == pytest.approx(10 * 30.44 / 90)
    assert p.loc[2, "RecentMonthlyDemand"] == pytest.approx(4 * 30.44 / 90)
    assert p.loc[3, "RecentMonthlyDemand"] == 0


def test_unmatched_key_raises(sheets):
    """Check that an unknown shipper ID raises ModelError.

    Args:
        sheets (dict[str, pandas.DataFrame]): Fresh synthetic sheets.

    Returns:
        None.
    """
    sheets["Orders"].loc[0, "ShipVia"] = 99
    with pytest.raises(ModelError, match="shippers"):
        build_model(clean_tables(sheets), Config())


def test_unmapped_country_raises(sheets):
    """Check that an unmapped customer country raises ValueError.

    Args:
        sheets (dict[str, pandas.DataFrame]): Fresh synthetic sheets.

    Returns:
        None.
    """
    sheets["Customers"].loc[0, "Country"] = "Atlantis"
    with pytest.raises(ValueError, match="Atlantis"):
        build_model(clean_tables(sheets), Config())
