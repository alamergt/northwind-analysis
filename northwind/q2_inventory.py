"""Q2: which active products purchasing should restock first
(plan.md sections 3.3, 3.4 and 4)."""

import math
from dataclasses import dataclass

import pandas as pd

from northwind import metrics

CAVEAT = (
    "This is a priority list, not a forecast. The stock snapshot has no date and is assumed "
    "to be taken at the analysis cutoff (6 May 1998), and there are no supplier lead times, "
    "so the list ranks urgency but can't predict when a product will run out."
)


@dataclass
class Q2Result:
    """Outputs of the Q2 restocking analysis.

    Attributes:
        watch_list (pandas.DataFrame): Every active product, ranked by
            tier and then monthly revenue at stake, with an action
            (appendix).
        shortlist (pandas.DataFrame): The top of the watch list shown on
            the main page.
        headline (str): Catalogue-wide finding stated above the shortlist.
        no_reorder_rule (pandas.DataFrame): Active products with reorder
            level 0, with suggested levels.
        discontinued_stock (pandas.DataFrame): Discontinued products that
            still hold stock.
        robustness (pandas.DataFrame): Critical/High membership under
            other demand windows (plan 8.3).
        tier_counts (dict[str, int]): Active products per tier.
        caveat (str): Statement shown with the Q2 results.
    """

    watch_list: pd.DataFrame
    shortlist: pd.DataFrame
    headline: str
    no_reorder_rule: pd.DataFrame
    discontinued_stock: pd.DataFrame
    robustness: pd.DataFrame
    tier_counts: dict
    caveat: str = CAVEAT


def _reorder_column(lead_time):
    """Return the column name for a suggested reorder level.

    Args:
        lead_time (float): Assumed lead time in months.

    Returns:
        str: e.g. "SuggestedReorder_0.5m".
    """
    return f"SuggestedReorder_{lead_time:g}m"


def average_net_price(lines, config):
    """Return average net price per unit for each product.

    Uses the recent demand window; products with no recent sales fall
    back to their average over all orders.

    Args:
        lines (pandas.DataFrame): Order lines with ProductID, OrderDate,
            Quantity and NetRevenue.
        config (northwind.config.Config): Cutoff and window.

    Returns:
        pandas.Series: Net revenue per unit, indexed by ProductID.
    """
    start = config.cutoff - pd.Timedelta(days=config.demand_window_days - 1)
    day = lines["OrderDate"].dt.normalize()
    recent = lines[(day >= start) & (day <= config.cutoff)]

    def per_unit(frame):
        totals = frame.groupby("ProductID")[["NetRevenue", "Quantity"]].sum()
        return totals["NetRevenue"] / totals["Quantity"]

    return per_unit(recent).combine_first(per_unit(lines))


def pending_units(lines):
    """Return units on orders that have not been shipped, per product.

    Args:
        lines (pandas.DataFrame): Order lines with ProductID, Quantity and
            ShippedDate.

    Returns:
        pandas.Series: Units waiting to ship, indexed by ProductID.
    """
    return lines[lines["ShippedDate"].isna()].groupby("ProductID")["Quantity"].sum()


def restock_action(row):
    """Return the recommended purchasing action for one product.

    Args:
        row (pandas.Series): One row of ``assess_products``.

    Returns:
        str: Action text.
    """
    tier = row["Tier"]
    if tier == "Critical":
        return "Expedite the open order" if row["UnitsOnOrder"] > 0 else "Order now"
    if tier == "High":
        return "Order this purchasing cycle"
    if tier == "Watch":
        if row["NoReorderRule"]:
            return "Set a reorder level"
        return "Review the reorder level"
    if tier == "No recent demand":
        return "Review whether to keep stocking"
    if row["NoReorderRule"]:
        return "No restock needed; set a reorder level"
    return "No action needed"


def assess_products(model, config, window_days=None):
    """Compute demand, stock cover, tier and action for every product.

    Args:
        model (northwind.model.Model): Joined tables.
        config (northwind.config.Config): Windows and thresholds.
        window_days (int | None): Recent-demand window; None uses
            ``config.demand_window_days``.

    Returns:
        pandas.DataFrame: One row per product (active and discontinued).
    """
    p = model.products.copy()
    lines = model.order_lines
    window = window_days or config.demand_window_days
    if window != config.demand_window_days:
        recent = metrics.recent_monthly_demand(lines, config.cutoff, window, config.days_per_month)
        p["RecentMonthlyDemand"] = p["ProductID"].map(recent).fillna(0.0)
        p["DemandTrendRatio"] = (p["RecentMonthlyDemand"]
                                 / p["LongRunMonthlyDemand"].where(p["LongRunMonthlyDemand"] > 0))

    stock, on_order, demand = p["UnitsInStock"], p["UnitsOnOrder"], p["RecentMonthlyDemand"]
    p["CoverOnHand"] = metrics.months_of_cover(stock, demand)
    p["CoverWithOrders"] = metrics.months_of_cover(stock + on_order, demand)
    p["BelowReorderLevel"] = stock < p["ReorderLevel"]
    p["NoReorderRule"] = p["ReorderLevel"] == 0
    p["Accelerating"] = p["DemandTrendRatio"] > config.acceleration_ratio
    p["Tier"] = metrics.risk_tier(stock, on_order, p["ReorderLevel"], demand,
                                  p["DemandVariability"], config)
    p["AvgNetPrice"] = p["ProductID"].map(average_net_price(lines, config))
    p["RevenueAtRisk"] = demand * p["AvgNetPrice"]
    p["PendingUnits"] = p["ProductID"].map(pending_units(lines)).fillna(0).astype(int)
    # A screening flag, not a confirmed backorder: the orders may be unshipped
    # for other reasons, and stock on order may arrive in time.
    p["FlagPossibleShortage"] = (p["PendingUnits"] > 0) & (p["PendingUnits"] > stock)
    for lead_time in config.lead_time_scenarios:
        p[_reorder_column(lead_time)] = (demand * lead_time).apply(math.ceil).astype(int)
    p["Action"] = p.apply(restock_action, axis=1)
    p["TierRank"] = p["Tier"].map({t: i for i, t in enumerate(metrics.TIER_ORDER)})
    return p


def rank(products):
    """Order products by tier, then by monthly revenue at stake.

    Args:
        products (pandas.DataFrame): Output of ``assess_products``.

    Returns:
        pandas.DataFrame: Sorted copy with a 1-based Rank column.
    """
    ranked = products.sort_values(["TierRank", "RevenueAtRisk", "ProductName"],
                                  ascending=[True, False, True]).reset_index(drop=True)
    ranked.insert(0, "Rank", range(1, len(ranked) + 1))
    return ranked


def robustness(model, base, config, windows=(60, 120)):
    """Check whether Critical/High products stay there with other windows.

    Args:
        model (northwind.model.Model): Joined tables.
        base (pandas.DataFrame): Active products from the base run.
        config (northwind.config.Config): Settings.
        windows (tuple[int, ...]): Alternative demand windows in days.

    Returns:
        pandas.DataFrame: One row per window with the number of base
        Critical/High products, how many stay Critical/High, the share,
        whether it holds (share >= 80%), and the products that moved.
    """
    urgent = {"Critical", "High"}
    base_urgent = set(base.loc[base["Tier"].isin(urgent), "ProductID"])
    rows = []
    for window in windows:
        alt = assess_products(model, config, window).set_index("ProductID")
        kept = {pid for pid in base_urgent if alt.loc[pid, "Tier"] in urgent}
        moved = sorted(alt.loc[list(base_urgent - kept), "ProductName"])
        share = len(kept) / len(base_urgent) if base_urgent else float("nan")
        rows.append({"WindowDays": window, "BaseCriticalHigh": len(base_urgent),
                     "StillCriticalHigh": len(kept), "Share": share,
                     "Holds": share >= 0.8, "Moved": "; ".join(moved)})
    return pd.DataFrame(rows)


def headline(active, config):
    """State the catalogue-wide stock finding in one sentence.

    Args:
        active (pandas.DataFrame): Ranked active products.
        config (northwind.config.Config): Cover thresholds.

    Returns:
        str: Headline text.
    """
    urgent = active["Tier"].isin(["Critical", "High"])
    thin = (active["CoverOnHand"] < config.high_cover).sum()
    return (
        f"Stock on hand covers less than a month of recent demand for {thin} of "
        f"{len(active)} active products, and {urgent.sum()} are Critical or High. "
        f"The top {config.shortlist_size} below carry the most revenue at stake; "
        f"the full ranking is in the appendix."
    )


def run(model, config):
    """Run the full Q2 analysis.

    Args:
        model (northwind.model.Model): Joined tables.
        config (northwind.config.Config): Settings.

    Returns:
        Q2Result: All Q2 tables.
    """
    products = assess_products(model, config)
    active = rank(products[~products["Discontinued"]])
    reorder_cols = [_reorder_column(lt) for lt in config.lead_time_scenarios]
    no_rule = active[active["NoReorderRule"]][
        ["Rank", "ProductName", "CategoryName", "Tier", "UnitsInStock", "UnitsOnOrder",
         "RecentMonthlyDemand", "CoverOnHand", *reorder_cols]]
    gone = products[products["Discontinued"] & (products["UnitsInStock"] > 0)].copy()
    gone["StockValue"] = gone["UnitsInStock"] * gone["AvgNetPrice"]
    discontinued = gone[["ProductName", "CategoryName", "UnitsInStock", "UnitsOnOrder",
                         "AvgNetPrice", "StockValue"]].sort_values("StockValue", ascending=False)
    counts = active["Tier"].value_counts()
    return Q2Result(
        watch_list=active,
        shortlist=active.head(config.shortlist_size).reset_index(drop=True),
        headline=headline(active, config),
        no_reorder_rule=no_rule.reset_index(drop=True),
        discontinued_stock=discontinued.reset_index(drop=True),
        robustness=robustness(model, active, config),
        tier_counts={t: int(counts.get(t, 0)) for t in metrics.TIER_ORDER},
    )
