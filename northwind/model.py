"""Build the order-line, order and product tables (plan.md section 2.2)."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from northwind import metrics


class ModelError(ValueError):
    """Raised when a join changes row counts or leaves keys unmatched."""


@dataclass
class Model:
    """Joined, analysis-ready tables.

    Attributes:
        order_lines (pandas.DataFrame): One row per product on an order.
        orders (pandas.DataFrame): One row per order.
        products (pandas.DataFrame): One row per product, with demand.
        customers (pandas.DataFrame): One row per customer, with market.
        size_band_edges (numpy.ndarray): Order-size quartile edges.
    """

    order_lines: pd.DataFrame
    orders: pd.DataFrame
    products: pd.DataFrame
    customers: pd.DataFrame
    size_band_edges: np.ndarray


def _join(left, right, on, label, required):
    """Left-join many-to-one and check nothing was lost or left unmatched.

    Args:
        left (pandas.DataFrame): Many side.
        right (pandas.DataFrame): One side; ``on`` must be unique here.
        on (str): Join key.
        label (str): Join name used in error messages.
        required (list[str]): Columns from ``right`` that must be
            filled.

    Returns:
        pandas.DataFrame: Joined table with the same rows as ``left``.

    Raises:
        ModelError: If the row count changes or a required column has
            missing values after the join.
    """
    joined = left.merge(right, on=on, how="left", validate="many_to_one")
    if len(joined) != len(left):
        raise ModelError(f"{label}: row count changed {len(left)} -> {len(joined)}")
    unmatched = joined[required].isna().any(axis=1).sum()
    if unmatched:
        raise ModelError(f"{label}: {unmatched} row(s) without a match")
    return joined


def build_model(tables, config):
    """Join the cleaned sheets into the three analysis tables.

    Args:
        tables (dict[str, pandas.DataFrame]): Output of
            ``northwind.clean.clean_tables``.
        config (northwind.config.Config): Cutoff, windows and region
            maps.

    Returns:
        Model: Order lines, orders, products and customers.

    Raises:
        ModelError: If any join loses rows or leaves keys unmatched.
        ValueError: If a country is missing from a region map.
    """
    customers = tables["Customers"][["CustomerID", "CompanyName", "Country"]].rename(
        columns={"CompanyName": "CustomerName", "Country": "CustomerCountry"}
    )
    customers["Market"] = metrics.map_regions(customers["CustomerCountry"], config.market_groups)

    categories = tables["Categories"][["CategoryID", "CategoryName"]]
    suppliers = tables["Suppliers"][["SupplierID", "CompanyName", "Country"]].rename(
        columns={"CompanyName": "SupplierName", "Country": "SupplierCountry"}
    )
    shippers = tables["Shippers"][["ShipperID", "CompanyName"]].rename(
        columns={"ShipperID": "ShipVia", "CompanyName": "ShipperName"}
    )
    employees = tables["Employees"][["EmployeeID", "FirstName", "LastName"]].copy()
    employees["EmployeeName"] = employees["FirstName"] + " " + employees["LastName"]
    employees = employees[["EmployeeID", "EmployeeName"]]

    product_cols = [
        "ProductID", "ProductName", "SupplierID", "CategoryID",
        "UnitsInStock", "UnitsOnOrder", "ReorderLevel", "Discontinued",
    ]
    products = _join(tables["Product"][product_cols], categories, "CategoryID",
                     "products -> categories", ["CategoryName"])
    products = _join(products, suppliers, "SupplierID",
                     "products -> suppliers", ["SupplierName"])

    # Order lines.
    order_cols = ["OrderID", "CustomerID", "EmployeeID", "OrderDate", "ShippedDate"]
    lines = tables["Orders Details"].copy()
    lines["GrossRevenue"] = metrics.gross_revenue(lines["UnitPrice"], lines["Quantity"])
    lines["NetRevenue"] = metrics.net_revenue(lines["UnitPrice"], lines["Quantity"], lines["Discount"])
    lines = _join(lines, tables["Orders"][order_cols], "OrderID",
                  "order lines -> orders", ["CustomerID"])
    lines = _join(lines, customers, "CustomerID",
                  "order lines -> customers", ["CustomerName"])
    lines = _join(lines, products[["ProductID", "ProductName", "CategoryID", "CategoryName", "SupplierID"]],
                  "ProductID", "order lines -> products", ["ProductName"])
    lines["Quarter"] = metrics.quarter_of(lines["OrderDate"])

    # Orders.
    totals = lines.groupby("OrderID").agg(
        Units=("Quantity", "sum"),
        NetRevenue=("NetRevenue", "sum"),
        GrossRevenue=("GrossRevenue", "sum"),
        Lines=("ProductID", "size"),
    ).reset_index()
    orders = tables["Orders"][[
        "OrderID", "CustomerID", "EmployeeID", "OrderDate", "RequiredDate",
        "ShippedDate", "ShipVia", "Freight", "ShipCountry",
    ]].merge(totals, on="OrderID", how="left", validate="one_to_one")
    orders[["Units", "NetRevenue", "GrossRevenue", "Lines"]] = orders[
        ["Units", "NetRevenue", "GrossRevenue", "Lines"]
    ].fillna(0)
    orders = _join(orders, shippers, "ShipVia", "orders -> shippers", ["ShipperName"])
    orders = _join(orders, customers, "CustomerID", "orders -> customers", ["CustomerName"])
    orders = _join(orders, employees, "EmployeeID", "orders -> employees", ["EmployeeName"])
    orders["DestRegion"] = metrics.map_regions(orders["ShipCountry"], config.dest_regions)
    orders["Quarter"] = metrics.quarter_of(orders["OrderDate"])
    orders["IsShipped"] = orders["ShippedDate"].notna()
    orders["ProcessingDays"] = metrics.processing_days(orders["OrderDate"], orders["ShippedDate"])
    orders["AllowedDays"] = metrics.processing_days(orders["OrderDate"], orders["RequiredDate"])
    orders["SlackDays"] = metrics.slack_days(orders["RequiredDate"], orders["ShippedDate"])
    orders["IsLate"] = metrics.is_late(orders["SlackDays"])
    orders["FreightPerUnit"] = metrics.freight_per_unit(orders["Freight"], orders["Units"])
    orders["FreightShare"] = metrics.freight_share(orders["Freight"], orders["NetRevenue"])
    edges = metrics.size_band_edges(orders["Units"])
    orders["SizeBand"] = metrics.assign_size_band(orders["Units"], edges)

    # Product demand.
    recent = metrics.recent_monthly_demand(
        lines, config.cutoff, config.demand_window_days, config.days_per_month)
    longrun = metrics.longrun_monthly_demand(lines, config.cutoff, config.days_per_month)
    variability = metrics.demand_variability(lines, *config.demand_months)
    products["RecentMonthlyDemand"] = products["ProductID"].map(recent).fillna(0.0)
    products["LongRunMonthlyDemand"] = products["ProductID"].map(longrun).fillna(0.0)
    products["DemandTrendRatio"] = (
        products["RecentMonthlyDemand"]
        / products["LongRunMonthlyDemand"].where(products["LongRunMonthlyDemand"] > 0)
    )
    products["DemandVariability"] = products["ProductID"].map(variability)

    return Model(
        order_lines=lines,
        orders=orders,
        products=products,
        customers=customers,
        size_band_edges=edges,
    )
