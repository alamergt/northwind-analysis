"""Integration tests for Q3 on the real workbook."""

import pytest

from northwind import Config, load_model
from northwind import q3_logistics as q3
from northwind.config import CONTROL_TOTALS as CT

pytestmark = pytest.mark.integration

if not Config().workbook.exists():
    pytest.skip("real workbook not present", allow_module_level=True)


@pytest.fixture(scope="module")
def result():
    """Run Q3 on the real workbook.

    Args:
        None.

    Returns:
        northwind.q3_logistics.Q3Result: Q3 results, shared by the
        module.
    """
    config = Config()
    return q3.run(load_model(config), config)


def test_overview_counts(result):
    """Check shipped, late and backlog counts against control totals.

    Args:
        result (northwind.q3_logistics.Q3Result): Q3 results for the
            real workbook.

    Returns:
        None.
    """
    o = result.overview
    assert o["ShippedOrders"] == CT["orders_shipped"]
    assert o["LateOrders"] == CT["orders_late"]
    assert result.backlog["Orders"] == CT["orders_unshipped"]


def test_breakdowns_cover_every_shipped_order(result):
    """Check each breakdown covers every shipped and late order.

    Args:
        result (northwind.q3_logistics.Q3Result): Q3 results for the
            real workbook.

    Returns:
        None.
    """
    for name, table in result.breakdowns.items():
        assert table["Orders"].sum() == CT["orders_shipped"], name
        assert table["LateOrders"].sum() == CT["orders_late"], name


def test_opportunities_ranked_and_non_negative(result):
    """Check opportunities are positive and ranked within each type.

    Args:
        result (northwind.q3_logistics.Q3Result): Q3 results for the
            real workbook.

    Returns:
        None.
    """
    opps = result.opportunities
    assert (opps["Size"] > 0).all()
    for _, group in opps.groupby("Type"):
        assert group["Size"].is_monotonic_decreasing
        assert list(group["RankInType"]) == list(range(1, len(group) + 1))


def test_regression_uses_best_carrier_as_baseline(result):
    """Check the regression, if run, covers both models and baselines.

    Checks that each carrier is compared with a different (baseline)
    carrier and that every effect lies inside its interval. It does
    not check that the baseline is the best carrier.

    Args:
        result (northwind.q3_logistics.Q3Result): Q3 results for the
            real workbook.

    Returns:
        None.
    """
    if result.regression_reason is None:
        assert result.regression.empty
        return
    reg = result.regression
    assert set(reg["Model"]) == {"Freight", "Dispatch"}
    assert (reg["Carrier"] != reg["Baseline"]).all()
    assert ((reg["Low95"] <= reg["Effect"]) & (reg["Effect"] <= reg["High95"])).all()


def test_late_by_window_adds_up(result):
    """Check the late-by-window table adds up to control totals.

    Args:
        result (northwind.q3_logistics.Q3Result): Q3 results for the
            real workbook.

    Returns:
        None.
    """
    assert result.late_by_window["LateOrders"].sum() == CT["orders_late"]
    assert result.late_by_window["Orders"].sum() == CT["orders_shipped"]


def test_no_action_recommended_on_unsupported_gaps(result):
    """Check unsupported gaps carry no action and no rate review.

    Args:
        result (northwind.q3_logistics.Q3Result): Q3 results for the
            real workbook.

    Returns:
        None.
    """
    opps = result.opportunities
    unsupported = opps[opps["Confidence"] == "Not supported after adjustment"]
    assert (unsupported["Action"] == q3.NO_ACTION).all()
    assert not unsupported["Action"].str.contains("rate", case=False).any()


def test_robustness_shape(result):
    """Check the robustness table has six rows of both types.

    Args:
        result (northwind.q3_logistics.Q3Result): Q3 results for the
            real workbook.

    Returns:
        None.
    """
    assert len(result.robustness) == 6
    assert set(result.robustness["Type"]) == {"Processing", "Freight"}


def test_deterministic(result):
    """Check a second run gives the same opportunities and regression.

    Args:
        result (northwind.q3_logistics.Q3Result): Q3 results for the
            real workbook.

    Returns:
        None.
    """
    config = Config()
    again = q3.run(load_model(config), config)
    assert again.opportunities.equals(result.opportunities)
    assert again.regression.equals(result.regression)


def test_regression_without_slow_orders_runs_when_triggered(result):
    """Check the regression without slow orders runs when triggered.

    Args:
        result (northwind.q3_logistics.Q3Result): Q3 results for the
            real workbook.

    Returns:
        None.
    """
    if result.regression_reason is None:
        return
    reg = result.regression_without_slow
    assert set(reg["Model"]) == {"Freight", "Dispatch"}
    assert abs(sum(result.slow_share_by_carrier.values())) > 0
