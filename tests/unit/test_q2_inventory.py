"""Unit tests for Q2 restocking, using the synthetic workbook.

Synthetic products (see tests/conftest.py):
  1 Tea:   active, stock 0, 10 on order, reorder level 5; 10 units ordered
           on 1 Apr 1998 (inside the 90-day window).
  2 Fish:  active, stock 50, nothing on order, no reorder rule; 4 units on
           the unshipped order of 1 May 1998.
  3 Juice: discontinued, stock 3; last sold Oct 1997.
"""

import math

import pandas as pd
import pytest

from northwind import Config
from northwind import q2_inventory as q2

MONTH = 30.44 / 90


@pytest.fixture(scope="module")
def result(synthetic_model):
    return q2.run(synthetic_model, Config())


@pytest.fixture(scope="module")
def products(synthetic_model):
    return q2.assess_products(synthetic_model, Config()).set_index("ProductID")


def test_demand_cover_and_tier(products):
    tea, fish = products.loc[1], products.loc[2]
    assert tea["RecentMonthlyDemand"] == pytest.approx(10 * MONTH)
    assert tea["Tier"] == "Critical" and tea["Action"] == "Expedite the open order"
    assert fish["CoverOnHand"] == pytest.approx(50 / (4 * MONTH))
    assert fish["Tier"] == "OK" and fish["Action"] == "No restock needed; set a reorder level"


def test_average_price_falls_back_to_all_orders(products):
    assert products.loc[1, "AvgNetPrice"] == pytest.approx(108 / 10)  # recent sale, 10% discount
    assert products.loc[2, "AvgNetPrice"] == pytest.approx(25.0)
    assert products.loc[3, "AvgNetPrice"] == pytest.approx(8.0)       # no recent sale


def test_revenue_at_risk_and_suggested_levels(products):
    assert products.loc[1, "RevenueAtRisk"] == pytest.approx(10 * MONTH * 10.8)
    assert products.loc[2, "SuggestedReorder_1m"] == math.ceil(4 * MONTH)
    assert products.loc[2, "SuggestedReorder_2m"] == math.ceil(8 * MONTH)


def test_pending_units_and_shortage_flag(products):
    assert products.loc[2, "PendingUnits"] == 4
    assert not products.loc[2, "FlagPossibleShortage"]  # 50 in stock covers the 4 waiting
    assert products.loc[1, "PendingUnits"] == 0


def test_watch_list_excludes_discontinued_and_is_ranked(result):
    watch = result.watch_list
    assert list(watch["ProductID"]) == [1, 2]
    assert list(watch["Rank"]) == [1, 2]
    assert result.tier_counts["Critical"] == 1 and result.tier_counts["OK"] == 1


def test_side_tables(result):
    assert list(result.no_reorder_rule["ProductName"]) == ["Fish"]
    assert list(result.discontinued_stock["ProductName"]) == ["Juice"]
    assert result.discontinued_stock.loc[0, "StockValue"] == pytest.approx(3 * 8.0)


def test_robustness_shape(result):
    assert list(result.robustness["WindowDays"]) == [60, 120]
    assert result.robustness["Holds"].all()


@pytest.mark.parametrize(
    "tier,on_order,no_rule,expected",
    [
        ("Critical", 0, False, "Order now"),
        ("Critical", 5, False, "Expedite the open order"),
        ("High", 0, False, "Order this purchasing cycle"),
        ("Watch", 0, True, "Set a reorder level"),
        ("Watch", 0, False, "Review the reorder level"),
        ("OK", 0, False, "No action needed"),
        ("No recent demand", 0, False, "Review whether to keep stocking"),
    ],
)
def test_restock_actions(tier, on_order, no_rule, expected):
    row = pd.Series({"Tier": tier, "UnitsOnOrder": on_order, "NoReorderRule": no_rule})
    assert q2.restock_action(row) == expected


def test_rank_breaks_ties_by_revenue():
    frame = pd.DataFrame({
        "ProductName": ["a", "b", "c"],
        "TierRank": [1, 0, 1],
        "RevenueAtRisk": [10.0, 1.0, 50.0],
    })
    assert list(q2.rank(frame)["ProductName"]) == ["b", "c", "a"]
