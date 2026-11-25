"""Integration tests for Q1 on the real workbook."""

import pytest

from northwind import Config, load_model
from northwind import q1_markets as q1
from northwind.metrics import ACTIONS

pytestmark = pytest.mark.integration

if not Config().workbook.exists():
    pytest.skip("real workbook not present", allow_module_level=True)

ALLOWED_ACTIONS = set(ACTIONS.values()) | {"Insufficient data"}
CONFIDENCE = {"Clear", "Confirmed", "Not conclusive", "n/a"}


@pytest.fixture(scope="module")
def result():
    """Run Q1 on the real workbook.

    Args:
        None.

    Returns:
        northwind.q1_markets.Q1Result: Q1 results, shared by the module.
    """
    config = Config()
    return q1.run(load_model(config), config)


def test_ten_markets_four_focus(result):
    """Check there are ten markets and the four expected focus ones.

    Args:
        result (northwind.q1_markets.Q1Result): Q1 results for the real
            workbook.

    Returns:
        None.
    """
    card = result.scorecard
    assert len(card) == 10
    assert set(card.loc[card["IsFocus"], "Market"]) == {"USA", "Germany", "Brazil", "France"}


def test_markets_add_up_to_company(result):
    """Check market revenue, orders and shares add up to the company.

    Args:
        result (northwind.q1_markets.Q1Result): Q1 results for the real
            workbook.

    Returns:
        None.
    """
    card, company = result.scorecard, result.company
    assert card["RevenuePrior"].sum() == pytest.approx(company["RevenuePrior"])
    assert card["RevenueCurrent"].sum() == pytest.approx(company["RevenueCurrent"])
    assert card["OrdersCurrent"].sum() == company["OrdersCurrent"]
    assert card["SharePrior"].sum() == pytest.approx(1.0)
    assert card["ShareCurrent"].sum() == pytest.approx(1.0)


def test_relative_growth_formula(result):
    """Check relative growth against its formula for every market.

    Args:
        result (northwind.q1_markets.Q1Result): Q1 results for the real
            workbook.

    Returns:
        None.
    """
    card, g = result.scorecard, result.company["Growth"]
    assert card["RelativeGrowth"].to_numpy() == pytest.approx(((1 + card["Growth"]) / (1 + g) - 1).to_numpy())


def test_decomposition_adds_up_for_every_market(result):
    """Check the orders and size effects sum to each market's change.

    Args:
        result (northwind.q1_markets.Q1Result): Q1 results for the real
            workbook.

    Returns:
        None.
    """
    card = result.scorecard
    assert (card["OrdersEffect"] + card["SizeEffect"]).to_numpy() == pytest.approx(card["Change"].to_numpy())


def test_quarterly_table_matches_total_revenue(result):
    """Check the quarterly table sums to total net revenue.

    Args:
        result (northwind.q1_markets.Q1Result): Q1 results for the real
            workbook.

    Returns:
        None.
    """
    model = load_model()
    assert result.quarterly["Revenue"].sum() == pytest.approx(model.order_lines["NetRevenue"].sum())


def test_actions_and_confidence_valid(result):
    """Check action, confidence and risk use only allowed values.

    Args:
        result (northwind.q1_markets.Q1Result): Q1 results for the real
            workbook.

    Returns:
        None.
    """
    card = result.scorecard
    assert set(card["RecommendedAction"]) <= ALLOWED_ACTIONS
    assert set(card["PerformanceConfidence"]) <= CONFIDENCE
    assert set(card["ConcentrationRisk"]) <= {"High", "Low"}


def test_near_line_flag_matches_definition(result):
    """Check the near-line flag matches its 45-55% definition.

    Args:
        result (northwind.q1_markets.Q1Result): Q1 results for the real
            workbook.

    Returns:
        None.
    """
    card = result.scorecard
    expected = (card["Dependence"] - 0.5).abs() <= 0.05
    assert card["FlagNearConcentrationLine"].tolist() == expected.tolist()


def test_bootstrap_only_where_triggered(result):
    """Check only triggered markets get a bootstrap confidence label.

    Args:
        result (northwind.q1_markets.Q1Result): Q1 results for the real
            workbook.

    Returns:
        None.
    """
    triggered = set(result.bootstrap["Market"])
    card = result.scorecard.set_index("Market")
    assert all(card.loc[m, "PerformanceConfidence"] in ("Confirmed", "Not conclusive") for m in triggered)
    assert all(card.loc[m, "PerformanceConfidence"] in ("Clear", "n/a") for m in set(card.index) - triggered)


def test_run_is_deterministic(result):
    """Check a second run gives the same scorecard and bootstrap.

    Args:
        result (northwind.q1_markets.Q1Result): Q1 results for the real
            workbook.

    Returns:
        None.
    """
    config = Config()
    again = q1.run(load_model(config), config)
    assert again.bootstrap.equals(result.bootstrap)
    assert again.scorecard.equals(result.scorecard)


def test_uncertainty_covers_every_market_and_brackets_estimate(result):
    """Check every market has a likely range around its estimate.

    Args:
        result (northwind.q1_markets.Q1Result): Q1 results for the real
            workbook.

    Returns:
        None.
    """
    u = result.uncertainty
    assert set(u["Market"]) == set(result.scorecard["Market"])
    assert ((u["Low"] <= u["RelativeGrowth"]) & (u["RelativeGrowth"] <= u["High"])).all()
    assert "directional" in result.caveat


def test_every_market_has_a_summary(result):
    """Check every market has a summary.

    Args:
        result (northwind.q1_markets.Q1Result): Q1 results for the real
            workbook.

    Returns:
        None.
    """
    assert set(result.summaries) == set(result.scorecard["Market"])


def test_window_check_covers_every_market(result):
    """Check the window check covers every market and matches the base.

    Args:
        result (northwind.q1_markets.Q1Result): Q1 results for the real
            workbook.

    Returns:
        None.
    """
    w = result.windows
    assert set(w["Market"]) == set(result.scorecard["Market"])
    assert len(result.window_growth) == 3
    base = w.set_index("Market").iloc[:, 0]
    card = result.scorecard.set_index("Market")["RelativeGrowth"]
    assert base.loc[card.index].to_numpy() == pytest.approx(card.to_numpy())
