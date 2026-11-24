"""Unit tests for report wording that must follow the data."""

import pandas as pd

from northwind.report import rescue_detail

MOVERS = pd.DataFrame({
    "Market": ["Central", "Central"],
    "CustomerName": ["Big Co", "Small Co"],
    "Change": [14800.0, -8500.0],
    "Direction": ["Gain", "Loss"],
})


def _row(top_change):
    return pd.Series({"Market": "Central", "TopCustomer": "Big Co", "TopCustomerChange": top_change,
                      "Dependence": 0.55})


def test_rescue_when_key_account_grew_points_elsewhere():
    action, sentence = rescue_detail(_row(14800.0), MOVERS)
    assert "isn't the main cause" in sentence and "rose" in sentence
    assert "Small Co fell $8.5K" in sentence
    assert "recover Small Co" in action and "keep Big Co close" in action


def test_rescue_when_key_account_fell_reviews_it():
    action, sentence = rescue_detail(_row(-5000.0), MOVERS)
    assert "fell $5.0K" in sentence and "review" in sentence
    assert action == "Rescue Central: review the Big Co relationship"
