"""Unit tests for the Q1 market analysis on hand-built order lines."""

import pandas as pd
import pytest

from northwind import q1_markets as q1
from northwind.config import Config

# Company totals for the fixture: prior 1,000 + 1,000 + 200 = 2,200;
# current 1,800 + 600 + 200 = 2,600 (+18.2%).
COMPANY_PRIOR, COMPANY_CURRENT = 2200, 2600


def _make_lines():
    """Build order lines for three markets with known answers.

    Up:   prior 10 orders x $100 = $1,000; current 12 x $150 = $1,800,
          split evenly between C1 and C2 (dependence exactly 50%).
    Down: prior 10 x $100 = $1,000 from C3; current C3 4 x $100 + C4 4 x
          $50 = $600 (C3 holds 2/3 of the latest four quarters).
    Tiny: 2 orders in each window, too few to judge.
    """
    rows, order_id = [], 0

    def add(market, customer, quarter, n, revenue):
        nonlocal order_id
        for _ in range(n):
            order_id += 1
            rows.append((order_id, customer, f"Name {customer}", pd.Period(quarter, "Q"), revenue, market))

    add("Up", "C1", "1996Q4", 5, 100)
    add("Up", "C2", "1997Q1", 5, 100)
    add("Up", "C1", "1997Q4", 6, 150)
    add("Up", "C2", "1998Q1", 6, 150)
    add("Up", "C1", "1998Q2", 1, 999)  # partial quarter: outside every window
    add("Down", "C3", "1996Q4", 5, 100)
    add("Down", "C3", "1997Q1", 5, 100)
    add("Down", "C3", "1997Q4", 4, 100)
    add("Down", "C4", "1998Q1", 4, 50)
    add("Tiny", "C5", "1997Q1", 2, 100)
    add("Tiny", "C5", "1998Q1", 2, 100)
    return pd.DataFrame(rows, columns=["OrderID", "CustomerID", "CustomerName",
                                       "Quarter", "NetRevenue", "Market"])


@pytest.fixture
def lines():
    return _make_lines()


@pytest.fixture
def scored(lines):
    card, movers, company = q1.scorecard(lines, Config())
    return card.set_index("Market"), movers, company


def test_company_totals(scored):
    _, _, company = scored
    assert company["RevenuePrior"] == pytest.approx(COMPANY_PRIOR)
    assert company["RevenueCurrent"] == pytest.approx(COMPANY_CURRENT)
    assert company["Growth"] == pytest.approx(COMPANY_CURRENT / COMPANY_PRIOR - 1)


def test_relative_growth_and_shares(scored):
    card, _, _ = scored
    assert card.loc["Up", "Growth"] == pytest.approx(0.8)
    assert card.loc["Up", "SharePrior"] == pytest.approx(1000 / COMPANY_PRIOR)
    assert card.loc["Up", "RelativeGrowth"] == pytest.approx(1.8 / (COMPANY_CURRENT / COMPANY_PRIOR) - 1)
    assert card["SharePrior"].sum() == pytest.approx(1.0)
    assert card["ShareCurrent"].sum() == pytest.approx(1.0)


def test_actions_and_flags(scored):
    card, _, _ = scored
    up, down = card.loc["Up"], card.loc["Down"]
    assert (up["Performance"], up["ConcentrationRisk"], up["RecommendedAction"]) == (
        "Outperforming", "Low", "Invest")
    assert bool(up["FlagNearConcentrationLine"])  # exactly 50%: Low, but flagged
    assert not bool(up["FlagNarrowGrowth"])       # increase split 50/50
    assert (down["Performance"], down["ConcentrationRisk"], down["RecommendedAction"]) == (
        "Underperforming", "High", "Rescue")
    assert card.loc["Tiny", "RecommendedAction"] == "Insufficient data"


def test_partial_quarter_excluded(scored):
    card, _, _ = scored
    assert card.loc["Up", "RevenueCurrent"] == pytest.approx(1800)


def test_decomposition_adds_up(scored):
    card, _, _ = scored
    for market in ("Up", "Down"):
        row = card.loc[market]
        assert row["OrdersEffect"] + row["SizeEffect"] == pytest.approx(row["Change"])


def test_dependence(scored):
    card, _, _ = scored
    assert card.loc["Up", "Dependence"] == pytest.approx(0.5)
    assert card.loc["Down", "Dependence"] == pytest.approx(400 / 600)


def test_movers_sum_and_direction(scored):
    _, movers, _ = scored
    down = movers[movers["Market"] == "Down"].set_index("CustomerID")
    assert down.loc["C3", "Change"] == pytest.approx(-600)
    assert down.loc["C4", "Change"] == pytest.approx(200)
    assert down["Change"].sum() == pytest.approx(-400)
    assert (movers.loc[movers["Direction"] == "Gain", "Change"] > 0).all()
    assert (movers.loc[movers["Direction"] == "Loss", "Change"] < 0).all()


def test_consistency_flag(scored):
    card, _, _ = scored
    assert bool(card.loc["Up", "Consistent"])


def test_quarterly_table(lines):
    table = q1.quarterly_table(lines, Config())
    tiny = table[table["Market"] == "Tiny"]
    assert len(tiny) == table["Quarter"].nunique()
    partial = table[table["Quarter"] == pd.Period("1998Q2", "Q")]
    assert not partial["IsComplete"].any()
    assert table["Revenue"].sum() == pytest.approx(lines["NetRevenue"].sum())
    # Quarters with no revenue at all have no shares (NaN), so skip them.
    shares = table.groupby("Quarter")["Share"].sum(min_count=1).dropna()
    assert shares.to_numpy() == pytest.approx([1.0] * len(shares))


@pytest.mark.parametrize(
    "rel,consistent,expected",
    [
        (0.50, True, None),
        (0.19, True, "relative growth near a performance threshold"),
        (-0.06, True, "relative growth near a performance threshold"),
        (0.50, False, "share measures disagree in direction"),
    ],
)
def test_bootstrap_triggers(rel, consistent, expected):
    row = pd.Series({"RecommendedAction": "Invest", "RelativeGrowth": rel, "Consistent": consistent})
    assert q1.needs_bootstrap(row, Config()) == expected


def test_bootstrap_is_reproducible_and_brackets_estimate(lines, scored):
    card, _, _ = scored
    config = Config()
    first = q1.bootstrap_relative_growth(lines, "Down", config)
    assert first == q1.bootstrap_relative_growth(lines, "Down", config)
    assert first[0] <= card.loc["Down", "RelativeGrowth"] <= first[1]


def test_clear_levels_skip_bootstrap(lines):
    config = Config()
    card, _, _ = q1.scorecard(lines, config)
    boot = q1.performance_confidence(card, lines, config)
    conf = card.set_index("Market")["PerformanceConfidence"]
    assert conf["Tiny"] == "n/a"
    assert set(boot["Market"]) == {m for m, v in conf.items() if v in ("Confirmed", "Not conclusive")}


def test_summary_is_worded_as_recommendation(lines):
    config = Config()
    card, movers, company = q1.scorecard(lines, config)
    q1.performance_confidence(card, lines, config)
    text = q1.summarise(card, movers, company)
    assert "Suggested focus: Invest" in text["Up"]
    assert "near the 50% concentration line" in text["Up"]
    assert "too few orders" in text["Tiny"]


def test_unknown_basis_raises(synthetic_model):
    with pytest.raises(ValueError, match="basis"):
        q1.prepare_lines(synthetic_model, Config(), basis="planet")
