"""Unit tests for the metric definitions in plan.md section 3."""

import math

import numpy as np
import pandas as pd
import pytest

from northwind import metrics
from northwind.config import DEST_REGIONS, MARKET_GROUPS, Config

S = pd.Series


# --- Regions ---------------------------------------------------------------

def test_region_maps_cover_same_21_countries():
    """Check both region maps cover the same 21 countries.

    Args:
        None.

    Returns:
        None.
    """
    assert len(MARKET_GROUPS) == 21
    assert set(MARKET_GROUPS) == set(DEST_REGIONS)


def test_unknown_country_raises():
    """Check that mapping an unknown country raises ValueError.

    Args:
        None.

    Returns:
        None.
    """
    with pytest.raises(ValueError, match="Atlantis"):
        metrics.map_regions(S(["USA", "Atlantis"]), MARKET_GROUPS)


# --- Revenue ---------------------------------------------------------------

def test_net_and_gross_revenue():
    """Check gross and discounted net revenue per line.

    Args:
        None.

    Returns:
        None.
    """
    price, qty, disc = S([10.0, 20.0]), S([5, 2]), S([0.0, 0.05])
    assert metrics.gross_revenue(price, qty).tolist() == [50.0, 40.0]
    assert metrics.net_revenue(price, qty, disc).tolist() == pytest.approx([50.0, 38.0])


# --- Growth ----------------------------------------------------------------

def test_window_growth():
    """Check window growth, and NaN when prior revenue is zero.

    Args:
        None.

    Returns:
        None.
    """
    assert metrics.window_growth(100, 120) == pytest.approx(0.20)
    assert math.isnan(metrics.window_growth(0, 50))


@pytest.mark.parametrize("r0,o0,r1,o1", [(100, 10, 150, 12), (200, 8, 120, 10), (100, 10, 100, 5)])
def test_decomposition_adds_up_exactly(r0, o0, r1, o1):
    """Check the orders and size effects sum to the revenue change.

    Args:
        r0 (float): Revenue in the earlier window.
        o0 (int): Orders in the earlier window.
        r1 (float): Revenue in the later window.
        o1 (int): Orders in the later window.

    Returns:
        None.
    """
    orders_effect, size_effect = metrics.decompose_change(r0, o0, r1, o1)
    assert orders_effect + size_effect == pytest.approx(r1 - r0)


def test_decomposition_signs():
    """Check that growth from more orders is all orders effect.

    Args:
        None.

    Returns:
        None.
    """
    # Same order value, more orders: all of the change is the order-count effect.
    orders_effect, size_effect = metrics.decompose_change(100, 10, 200, 20)
    assert orders_effect == pytest.approx(100)
    assert size_effect == pytest.approx(0)


def test_account_contributions_sum_to_change():
    """Check account contributions sum to the total change.

    Args:
        None.

    Returns:
        None.
    """
    prior = S({"A": 100.0, "B": 50.0})
    current = S({"A": 80.0, "C": 90.0})
    contrib = metrics.account_contributions(prior, current)
    assert contrib.sum() == pytest.approx(current.sum() - prior.sum())
    assert contrib.to_dict() == {"C": 90.0, "A": -20.0, "B": -50.0}


def test_top_shares():
    """Check top-customer share of revenue and of the increase.

    Args:
        None.

    Returns:
        None.
    """
    assert metrics.top_share(S([60.0, 30.0, 10.0])) == pytest.approx(0.6)
    assert metrics.top_share_of_increase(S([30.0, 10.0, -20.0])) == pytest.approx(1.5)
    assert math.isnan(metrics.top_share_of_increase(S([5.0, -10.0])))


def test_relative_growth_equals_share_change():
    """Check relative growth equals the change in revenue share.

    Args:
        None.

    Returns:
        None.
    """
    # Market +50% while company +20%: share ratio 1.5 / 1.2.
    assert metrics.relative_growth(0.10, 0.10 * 1.5 / 1.2) == pytest.approx(1.5 / 1.2 - 1)
    assert math.isnan(metrics.relative_growth(0.0, 0.2))


@pytest.mark.parametrize(
    "rel,expected",
    [
        (0.15, "Outperforming"),     # exactly at the threshold
        (0.1499, "In line"),
        (-0.0999, "In line"),
        (-0.10, "Underperforming"),  # exactly at the threshold
        (float("nan"), None),
    ],
)
def test_performance_level_edges(rel, expected):
    """Check performance levels at the threshold edges.

    Args:
        rel (float): Relative growth; NaN when there is no data.
        expected (str | None): Expected performance level.

    Returns:
        None.
    """
    assert metrics.performance_level(rel, Config()) == expected


@pytest.mark.parametrize("dep,expected", [(0.50, "Low"), (0.5001, "High"), (0.2, "Low")])
def test_concentration_risk_has_two_levels(dep, expected):
    """Check concentration risk is High only above 50%.

    Args:
        dep (float): Share of revenue from the top customer.
        expected (str): Expected risk level.

    Returns:
        None.
    """
    assert metrics.concentration_risk(dep, Config()) == expected


@pytest.mark.parametrize(
    "dep,expected",
    [(0.45, True), (0.55, True), (0.4499, False), (0.5501, False), (0.50, True), (float("nan"), False)],
)
def test_near_concentration_line_flag(dep, expected):
    """Check the flag for dependence within 5 points of 50%.

    Args:
        dep (float): Share of revenue from the top customer; may be NaN.
        expected (bool): Expected flag.

    Returns:
        None.
    """
    assert metrics.near_concentration_line(dep, Config()) is expected


@pytest.mark.parametrize("share,expected", [(0.60, False), (0.61, True), (float("nan"), False)])
def test_narrow_growth_flag(share, expected):
    """Check the narrow-growth flag is set only above 60%.

    Args:
        share (float): Top customer's share of the increase; may be NaN.
        expected (bool): Expected flag.

    Returns:
        None.
    """
    assert metrics.narrow_growth(share, Config()) is expected


@pytest.mark.parametrize(
    "performance,risk,expected",
    [
        ("Outperforming", "Low", "Invest"),
        ("Outperforming", "High", "Broaden"),
        ("In line", "Low", "Maintain"),
        ("In line", "High", "Protect"),
        ("Underperforming", "Low", "Diagnose"),
        ("Underperforming", "High", "Rescue"),
    ],
)
def test_all_six_actions(performance, risk, expected):
    """Check each performance and risk pair maps to its action.

    Args:
        performance (str): Performance level.
        risk (str): Concentration risk level.
        expected (str): Expected recommended action.

    Returns:
        None.
    """
    assert metrics.recommended_action(performance, risk, 20, 20, Config()) == expected
    assert expected in metrics.ACTION_TEXT


def test_insufficient_data_overrides_action():
    """Check that thin data gives Insufficient data.

    Args:
        None.

    Returns:
        None.
    """
    assert metrics.recommended_action("Outperforming", "Low", 7, 20, Config()) == "Insufficient data"
    assert metrics.recommended_action(None, "Low", 20, 20, Config()) == "Insufficient data"


# --- Demand ----------------------------------------------------------------

def _lines(rows):
    """Build order lines for the demand tests.

    Args:
        rows (list[tuple[int, str, int]]): ProductID, ISO order date and
            quantity for each line.

    Returns:
        pandas.DataFrame: Lines with OrderDate parsed to datetimes.
    """
    return pd.DataFrame(rows, columns=["ProductID", "OrderDate", "Quantity"]).assign(
        OrderDate=lambda d: pd.to_datetime(d["OrderDate"])
    )


def test_recent_window_boundaries():
    """Check the 90-day window keeps both end days and nothing else.

    Args:
        None.

    Returns:
        None.
    """
    cutoff = pd.Timestamp("1998-05-06")
    lines = _lines([
        (1, "1998-02-05", 100),  # one day before the 90-day window: excluded
        (1, "1998-02-06", 9),    # first day of the window: included
        (1, "1998-05-06", 9),    # cutoff day: included
        (1, "1998-05-07", 100),  # after cutoff: excluded
    ])
    demand = metrics.recent_monthly_demand(lines, cutoff, 90, 30.0)
    assert demand[1] == pytest.approx(18 * 30 / 90)


def test_longrun_demand_from_first_sale():
    """Check long-run demand is measured from the first sale.

    Args:
        None.

    Returns:
        None.
    """
    lines = _lines([(1, "1998-04-07", 30), (1, "1998-05-06", 30)])
    demand = metrics.longrun_monthly_demand(lines, pd.Timestamp("1998-05-06"), 30.0)
    assert demand[1] == pytest.approx(60 / 30 * 30)  # 30 days inclusive


def test_variability_counts_zero_months():
    """Check demand variability counts months without sales.

    Args:
        None.

    Returns:
        None.
    """
    lines = _lines([(1, "1998-01-15", 10), (1, "1998-03-15", 10)])
    cv = metrics.demand_variability(lines, "1998-01", "1998-04")
    monthly = np.array([10, 0, 10, 0])
    assert cv[1] == pytest.approx(monthly.std() / monthly.mean())


# --- Inventory -------------------------------------------------------------

def test_zero_demand_gives_no_cover_not_error():
    """Check zero demand gives NaN months of cover, not an error.

    Args:
        None.

    Returns:
        None.
    """
    cover = metrics.months_of_cover(S([10, 10]), S([0.0, 5.0]))
    assert math.isnan(cover[0]) and cover[1] == pytest.approx(2.0)


def _tier(stock, on_order, reorder, demand, cv=0.5):
    """Return the risk tier of one product.

    Args:
        stock (int): Units in stock.
        on_order (int): Units on order.
        reorder (int): Reorder level; 0 means no reorder rule.
        demand (float): Recent monthly demand in units.
        cv (float): Coefficient of variation of monthly demand.

    Returns:
        str: Tier from ``metrics.risk_tier`` with the default config.
    """
    return metrics.risk_tier(S([stock]), S([on_order]), S([reorder]), S([demand]), S([cv]), Config())[0]


@pytest.mark.parametrize(
    "stock,on_order,reorder,demand,cv,expected",
    [
        (5, 0, 0, 0.0, 0.5, "No recent demand"),
        (0, 50, 10, 10.0, 0.5, "Critical"),   # out of stock, even with stock on order
        (2, 2, 0, 10.0, 0.5, "Critical"),     # 0.4 months incl. on order
        (5, 0, 0, 10.0, 0.5, "High"),         # 0.5 months on hand, nothing on order
        (9, 0, 0, 10.0, 0.5, "High"),         # 0.9 months on hand
        (9, 20, 0, 10.0, 0.5, "Watch"),       # on order closes gap; no reorder rule
        (10, 0, 0, 10.0, 0.5, "Watch"),       # exactly 1 month; no rule and < 1.5
        (10, 0, 5, 10.0, 0.5, "OK"),          # exactly 1 month, has a rule, not below it
        (20, 0, 25, 10.0, 0.5, "Watch"),      # below reorder level
        (14, 0, 5, 10.0, 2.0, "Watch"),       # erratic demand and < 1.5 months
        (15, 0, 5, 10.0, 2.0, "OK"),          # exactly 1.5 months
        (30, 0, 5, 10.0, 0.5, "OK"),
    ],
)
def test_risk_tier_rules(stock, on_order, reorder, demand, cv, expected):
    """Check the risk-tier rules at and around each boundary.

    Args:
        stock (int): Units in stock.
        on_order (int): Units on order.
        reorder (int): Reorder level; 0 means no reorder rule.
        demand (float): Recent monthly demand in units.
        cv (float): Coefficient of variation of monthly demand.
        expected (str): Expected tier.

    Returns:
        None.
    """
    assert _tier(stock, on_order, reorder, demand, cv) == expected


# --- Processing time and freight -------------------------------------------

def test_processing_and_lateness():
    """Check processing days, NaN when unshipped, and late flags.

    Args:
        None.

    Returns:
        None.
    """
    order = pd.to_datetime(S(["1998-01-01", "1998-01-01", "1998-01-01"]))
    shipped = pd.to_datetime(S(["1998-01-05", "1998-02-05", None]))
    required = pd.to_datetime(S(["1998-01-29", "1998-01-29", "1998-01-29"]))
    days = metrics.processing_days(order, shipped)
    slack = metrics.slack_days(required, shipped)
    assert days[0] == 4 and days[1] == 35 and math.isnan(days[2])
    assert metrics.is_late(slack).tolist() == [False, True, False]


def test_freight_ratios_handle_zero():
    """Check freight ratios, including NaN for zero units.

    Args:
        None.

    Returns:
        None.
    """
    assert math.isnan(metrics.freight_per_unit(S([10.0]), S([0]))[0])
    assert metrics.freight_share(S([10.0]), S([200.0]))[0] == pytest.approx(0.05)


def test_size_bands_at_edges():
    """Check size bands, with edge values in the lower band.

    Args:
        None.

    Returns:
        None.
    """
    units = S([1, 2, 3, 4, 5, 6, 7, 8, 9])
    edges = metrics.size_band_edges(units)
    bands = metrics.assign_size_band(units, edges)
    assert bands[0] == "Small" and bands[8] == "Very large"
    assert bands[2] == "Small"  # 3 is the 25th-percentile edge: belongs to the lower band
    assert bands.notna().all()


def test_size_band_edges_must_be_distinct():
    """Check that duplicate size-band edges raise ValueError.

    Args:
        None.

    Returns:
        None.
    """
    with pytest.raises(ValueError):
        metrics.size_band_edges(S([5, 5, 5, 5]))


# --- Opportunity -----------------------------------------------------------

def test_excess_never_negative_and_weighted():
    """Check excess over a benchmark is non-negative and weightable.

    Args:
        None.

    Returns:
        None.
    """
    values = S([2.0, 5.0, 8.0, np.nan])
    assert metrics.excess_over_benchmark(values, 5.0) == pytest.approx(3.0)
    assert metrics.excess_over_benchmark(values, 5.0, S([10, 10, 2, 1])) == pytest.approx(6.0)
