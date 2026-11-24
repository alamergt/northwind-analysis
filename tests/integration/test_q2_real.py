"""Integration tests for Q2 on the real workbook."""

import pytest

from northwind import Config, load_model
from northwind import q2_inventory as q2
from northwind.config import CONTROL_TOTALS as CT
from northwind.metrics import TIER_ORDER

pytestmark = pytest.mark.integration

if not Config().workbook.exists():
    pytest.skip("real workbook not present", allow_module_level=True)


@pytest.fixture(scope="module")
def result():
    config = Config()
    return q2.run(load_model(config), config)


def test_ranks_every_active_product_once(result):
    watch = result.watch_list
    assert len(watch) == CT["active_products"]
    assert list(watch["Rank"]) == list(range(1, CT["active_products"] + 1))
    assert not watch["Discontinued"].any()
    assert sum(result.tier_counts.values()) == CT["active_products"]


def test_ranking_follows_tier_order(result):
    ranks = result.watch_list["Tier"].map({t: i for i, t in enumerate(TIER_ORDER)})
    assert ranks.is_monotonic_increasing


def test_critical_rule_holds(result):
    critical = result.watch_list[result.watch_list["Tier"] == "Critical"]
    assert ((critical["UnitsInStock"] <= 0) | (critical["CoverWithOrders"] < 0.5)).all()


def test_side_tables(result):
    assert len(result.no_reorder_rule) == CT["active_without_reorder_rule"]
    assert (result.discontinued_stock["UnitsInStock"] > 0).all()
    assert len(result.discontinued_stock) == 4


def test_suggested_levels_non_negative(result):
    cols = [c for c in result.watch_list.columns if c.startswith("SuggestedReorder_")]
    assert len(cols) == 3
    assert (result.watch_list[cols] >= 0).all().all()


def test_robustness_meets_plan_threshold(result):
    assert result.robustness["Holds"].all()


def test_shortlist_is_top_ten(result):
    assert list(result.shortlist["Rank"]) == list(range(1, 11))
    assert result.shortlist["ProductID"].tolist() == result.watch_list["ProductID"].head(10).tolist()
    assert "Critical or High" in result.headline


def test_deterministic(result):
    config = Config()
    again = q2.run(load_model(config), config)
    assert again.watch_list.equals(result.watch_list)
