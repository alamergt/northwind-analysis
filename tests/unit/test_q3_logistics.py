"""Unit tests for the Q3 logistics analysis."""

import numpy as np
import pandas as pd
import pytest

from northwind import Config
from northwind import q3_logistics as q3


def _orders(groups):
    """Build shipped orders in one size band from {group: [days, ...]}."""
    rows, oid = [], 0
    for group, values in groups.items():
        for days in values:
            oid += 1
            rows.append({"OrderID": oid, "Grp": group, "SizeBand": "Small",
                         "ProcessingDays": float(days), "FreightPerUnit": float(days),
                         "Units": 2})
    return pd.DataFrame(rows)


@pytest.fixture
def orders():
    # A: ten orders at 5 days. B: eight at 5 days and two at 15 days.
    return _orders({"A": [5] * 10, "B": [5] * 8 + [15] * 2})


def test_gap_against_best_group(orders):
    gaps = q3.group_gaps(orders, "Grp", "ProcessingDays", Config()).set_index("Group")
    # Benchmark = median 5 (A and B tie; A is first). B's excess = 2 x 10 = 20 days.
    assert gaps.loc["B", "ExcessTotal"] == pytest.approx(20)
    assert gaps.loc["B", "Opportunity"] == pytest.approx(20)
    assert gaps.loc["A", "Opportunity"] == 0
    assert gaps.loc["B", "OpportunityPerOrder"] == pytest.approx(2)


def test_gap_is_weighted(orders):
    gaps = q3.group_gaps(orders, "Grp", "FreightPerUnit", Config(), weight_col="Units").set_index("Group")
    assert gaps.loc["B", "Opportunity"] == pytest.approx(40)  # 2 units per order


def test_best_group_needs_enough_orders():
    # C is fastest but has only 3 orders, so it can't be the benchmark.
    frame = _orders({"A": [6] * 10, "B": [8] * 10, "C": [1] * 3})
    gaps = q3.group_gaps(frame, "Grp", "ProcessingDays", Config()).set_index("Group")
    assert "Small: A" in gaps.loc["B", "Benchmarks"]
    assert gaps.loc["B", "Opportunity"] == pytest.approx(10 * 2)


def test_overall_benchmark_and_bad_option(orders):
    gaps = q3.group_gaps(orders, "Grp", "ProcessingDays", Config(), benchmark="overall")
    assert set(gaps["Group"]) == {"A", "B"}
    with pytest.raises(ValueError):
        q3.group_gaps(orders, "Grp", "ProcessingDays", Config(), benchmark="worst")


def test_ols_hc1_recovers_exact_line():
    x = pd.Series(np.arange(10, dtype=float))
    design = pd.DataFrame({"Intercept": 1.0, "x": x})
    fit = q3.ols_hc1((2 + 3 * x).to_numpy(), design)
    assert fit.loc["Intercept", "Estimate"] == pytest.approx(2)
    assert fit.loc["x", "Estimate"] == pytest.approx(3)
    assert fit["StdError"].to_numpy() == pytest.approx([0, 0], abs=1e-9)


def test_adjustment_marks_carriers():
    opps = pd.DataFrame({
        "Type": ["Processing", "Freight", "Processing"],
        "Dimension": ["Carrier", "Carrier", "Employee"],
        "Group": ["Slow Co", "Slow Co", "Ann"],
        "Confidence": ["Clear"] * 3,
        "Action": ["review dispatch", "review rates", "review handling"],
    })
    regression = pd.DataFrame({
        "Model": ["Dispatch", "Freight"], "Carrier": ["Slow Co", "Slow Co"],
        "Effect": [1.5, 0.05], "Material": [True, False],
    })
    out = q3.apply_adjustment(opps, regression)
    assert list(out["Confidence"]) == ["Supported after adjustment",
                                       "Not supported after adjustment", "Clear"]
    # An unsupported gap must never keep a recommendation to act on it.
    assert list(out["Action"]) == ["review dispatch", q3.NO_ACTION, "review handling"]


def test_deadline_priority():
    frame = pd.DataFrame({
        "AllowedDays": [14, 14, 28, 28, 28],
        "ProcessingDays": [9.0, 9.0, 5.0, 5.0, 30.0],
        "IsLate": [False, False, False, False, True],
        "IsSlow": [False, False, False, False, True],
    })
    result = q3.deadline_priority(frame)
    assert result["ShortWindowPrioritised"] is False
    assert result["LateThatAreSlow"] == 1.0
    assert result["MedianDaysByWindow"] == {14: 9.0, 28: 5.0}


def test_backlog_and_consolidation(synthetic_model):
    config = Config()
    backlog = q3.backlog(synthetic_model, config)
    assert backlog["Orders"] == 1 and backlog["RevenueHeld"] == pytest.approx(100)
    assert backlog["OldestAgeDays"] == 5  # ordered 1 May, cutoff 6 May
    frame = pd.DataFrame({
        "SizeBand": ["Small", "Small", "Large"],
        "FreightShare": [0.50, 0.05, 0.50],   # only the first is a small, high-share order
        "Freight": [20.0, 5.0, 975.0],
    })
    cons = q3.consolidation(frame, config)
    assert cons["Orders"] == 1 and cons["Freight"] == pytest.approx(20)
    assert cons["ShareOfAllFreight"] == pytest.approx(0.02) and cons["Material"]


def test_late_by_window(synthetic_model):
    shipped = q3.shipped_orders(synthetic_model, Config())
    table = q3.late_by_window(shipped).set_index("AllowedDays")
    assert table.loc[28.0, "Orders"] == 3 and table.loc[28.0, "LateOrders"] == 1
