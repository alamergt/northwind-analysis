"""Metric definitions from plan.md section 3, each coded once."""

import numpy as np
import pandas as pd

SIZE_BAND_LABELS = ("Small", "Medium", "Large", "Very large")

TIER_ORDER = ("Critical", "High", "Watch", "OK", "No recent demand")


# --- Shared helpers -------------------------------------------------------

def map_regions(countries, mapping):
    """Map each country to its group.

    Args:
        countries (pandas.Series): Country names.
        mapping (dict[str, str]): Country to group name.

    Returns:
        pandas.Series: Group name for each country, same index.

    Raises:
        ValueError: If any country is not in ``mapping``.
    """
    unknown = sorted(set(countries.dropna()) - set(mapping))
    if unknown:
        raise ValueError(f"Countries missing from region map: {', '.join(unknown)}")
    return countries.map(mapping)


def quarter_of(dates):
    """Return the calendar quarter of each date.

    Args:
        dates (pandas.Series): Datetimes.

    Returns:
        pandas.Series: Quarterly periods, e.g. ``1997Q4``.
    """
    return dates.dt.to_period("Q")


# --- 3.1 Revenue ----------------------------------------------------------

def gross_revenue(unit_price, quantity):
    """Return revenue before discount for each order line.

    Args:
        unit_price (pandas.Series): Price charged per unit on the line.
        quantity (pandas.Series): Units on the line.

    Returns:
        pandas.Series: ``unit_price * quantity``.
    """
    return unit_price * quantity


def net_revenue(unit_price, quantity, discount):
    """Return revenue after discount for each order line.

    Args:
        unit_price (pandas.Series): Price charged per unit on the line.
        quantity (pandas.Series): Units on the line.
        discount (pandas.Series): Discount as a fraction, 0 to 1.

    Returns:
        pandas.Series: ``unit_price * quantity * (1 - discount)``.
    """
    return unit_price * quantity * (1 - discount)


# --- 3.2 Market growth ----------------------------------------------------

def window_growth(prior, current):
    """Return the relative change between two revenue windows.

    Args:
        prior (float): Revenue in the earlier window.
        current (float): Revenue in the later window.

    Returns:
        float: ``(current - prior) / prior``, or NaN if ``prior`` <= 0.
    """
    if prior <= 0:
        return float("nan")
    return (current - prior) / prior


def decompose_change(rev_prior, orders_prior, rev_current, orders_current):
    """Split a revenue change into order-count and order-size effects.

    Uses a log-mean weight so the two effects add up exactly to
    ``rev_current - rev_prior``.

    Args:
        rev_prior (float): Revenue in the earlier window.
        orders_prior (int): Orders in the earlier window.
        rev_current (float): Revenue in the later window.
        orders_current (int): Orders in the later window.

    Returns:
        tuple[float, float]: Dollar effect of (number of orders, average
        order value); both NaN if any input is zero or negative.
    """
    if min(rev_prior, orders_prior, rev_current, orders_current) <= 0:
        return float("nan"), float("nan")
    if np.isclose(rev_current, rev_prior):
        weight = rev_prior
    else:
        weight = (rev_current - rev_prior) / np.log(rev_current / rev_prior)
    aov_prior = rev_prior / orders_prior
    aov_current = rev_current / orders_current
    orders_effect = weight * np.log(orders_current / orders_prior)
    size_effect = weight * np.log(aov_current / aov_prior)
    return float(orders_effect), float(size_effect)


def account_contributions(rev_prior, rev_current):
    """Return each customer's change in revenue between two windows.

    Args:
        rev_prior (pandas.Series): Revenue per customer, earlier window.
        rev_current (pandas.Series): Revenue per customer, later window.

    Returns:
        pandas.Series: Change per customer (absent = 0), largest first;
        sums to the total change.
    """
    customers = rev_prior.index.union(rev_current.index)
    change = rev_current.reindex(customers, fill_value=0) - rev_prior.reindex(
        customers, fill_value=0
    )
    return change.sort_values(ascending=False)


def top_share(values):
    """Return the largest value's share of the total.

    Args:
        values (pandas.Series): Non-negative amounts, e.g. revenue per
            customer.

    Returns:
        float: ``max / sum``, or NaN if the total is not positive.
    """
    total = values.sum()
    if total <= 0:
        return float("nan")
    return float(values.max() / total)


def top_share_of_increase(contributions):
    """Return the largest account gain as a share of the net increase.

    Args:
        contributions (pandas.Series): Change in revenue per customer.

    Returns:
        float: Largest gain divided by the net change, or NaN if the net
        change is not positive. Can exceed 1 when other accounts fell.
    """
    total = contributions.sum()
    if total <= 0:
        return float("nan")
    return float(contributions.max() / total)


ACTIONS = {
    ("Outperforming", "Low"): "Invest",
    ("Outperforming", "High"): "Broaden",
    ("In line", "Low"): "Maintain",
    ("In line", "High"): "Protect",
    ("Underperforming", "Low"): "Diagnose",
    ("Underperforming", "High"): "Rescue",
}

ACTION_TEXT = {
    "Invest": "consider adding sales coverage and targeting similar accounts",
    "Broaden": "growth looks real but rests on one account; consider protecting it "
               "and developing the next accounts",
    "Maintain": "current coverage looks adequate",
    "Protect": "consider account management focused on the key customer",
    "Diagnose": "losing ground without depending on one customer; review the accounts "
                "that declined, sales coverage, pricing and competition",
    "Rescue": "the market depends on one account and is losing share; check whether that account or "
              "the rest of the market is the cause before acting",
}

INSUFFICIENT = "Insufficient data"


def relative_growth(share_prior, share_current):
    """Return the change in a market's share of company revenue.

    Equals ``(1 + market growth) / (1 + company growth) - 1``.

    Args:
        share_prior (float): Market share in the earlier window.
        share_current (float): Market share in the later window.

    Returns:
        float: ``share_current / share_prior - 1``; NaN if the earlier
        share is not positive.
    """
    if not share_prior > 0:
        return float("nan")
    return share_current / share_prior - 1


def performance_level(rel_growth, config):
    """Classify relative growth as Outperforming, In line or Underperforming.

    Args:
        rel_growth (float): Output of ``relative_growth``.
        config (northwind.config.Config): Performance thresholds.

    Returns:
        str | None: The level, or None if ``rel_growth`` is NaN.
    """
    if pd.isna(rel_growth):
        return None
    if rel_growth >= config.outperform_threshold:
        return "Outperforming"
    if rel_growth <= config.underperform_threshold:
        return "Underperforming"
    return "In line"


def concentration_risk(dependence, config):
    """Classify dependence on the largest customer as High or Low.

    Args:
        dependence (float): Largest customer's share of market revenue.
        config (northwind.config.Config): Concentration threshold.

    Returns:
        str: "High" if dependence exceeds the threshold, else "Low".
    """
    return "High" if dependence > config.concentration_threshold else "Low"


def near_concentration_line(dependence, config):
    """Flag dependence close to the concentration threshold.

    Args:
        dependence (float): Largest customer's share of market revenue.
        config (northwind.config.Config): Threshold and margin.

    Returns:
        bool: True if within the margin of the threshold, inclusive.
    """
    if pd.isna(dependence):
        return False
    gap = abs(dependence - config.concentration_threshold)
    return bool(gap <= config.concentration_flag_margin + 1e-12)


def narrow_growth(top_increase_share, config):
    """Flag growth supplied mostly by one account.

    Args:
        top_increase_share (float): Output of ``top_share_of_increase``;
            NaN when revenue did not increase.
        config (northwind.config.Config): Narrow-growth share.

    Returns:
        bool: True if one account supplied more than the set share.
    """
    return bool(top_increase_share > config.narrow_growth_share) if not pd.isna(top_increase_share) else False


def recommended_action(performance, risk, orders_prior, orders_current, config):
    """Map performance and concentration risk to a recommended action.

    The action is a suggestion for discussion, not a decision.

    Args:
        performance (str | None): Output of ``performance_level``.
        risk (str): Output of ``concentration_risk``.
        orders_prior (int): Orders in the earlier window.
        orders_current (int): Orders in the later window.
        config (northwind.config.Config): Minimum orders per window.

    Returns:
        str: One of the six actions, or "Insufficient data".
    """
    if min(orders_prior, orders_current) < config.min_orders_per_window or performance is None:
        return INSUFFICIENT
    return ACTIONS[(performance, risk)]


# --- 3.3 Demand -----------------------------------------------------------

def recent_monthly_demand(lines, cutoff, window_days, days_per_month):
    """Return units ordered per month over the recent window, per product.

    The window is the ``window_days`` calendar days ending on ``cutoff``,
    both ends included.

    Args:
        lines (pandas.DataFrame): Order lines with ProductID, OrderDate
            and Quantity.
        cutoff (pandas.Timestamp): Last day of the window.
        window_days (int): Window length in days.
        days_per_month (float): Days per month for the conversion.

    Returns:
        pandas.Series: Monthly units indexed by ProductID; products with
        no orders in the window are absent.
    """
    start = cutoff - pd.Timedelta(days=window_days - 1)
    day = lines["OrderDate"].dt.normalize()
    recent = lines[(day >= start) & (day <= cutoff)]
    return recent.groupby("ProductID")["Quantity"].sum() * days_per_month / window_days


def longrun_monthly_demand(lines, cutoff, days_per_month):
    """Return units ordered per month since each product's first sale.

    Args:
        lines (pandas.DataFrame): Order lines with ProductID, OrderDate
            and Quantity.
        cutoff (pandas.Timestamp): End of the period, included.
        days_per_month (float): Days per month for the conversion.

    Returns:
        pandas.Series: Monthly units indexed by ProductID.
    """
    upto = lines[lines["OrderDate"].dt.normalize() <= cutoff]
    grouped = upto.groupby("ProductID")
    days = (cutoff - grouped["OrderDate"].min().dt.normalize()).dt.days + 1
    return grouped["Quantity"].sum() / days * days_per_month


def demand_variability(lines, first_month, last_month):
    """Return the coefficient of variation of monthly units per product.

    Months without sales count as zero. Uses the population standard
    deviation.

    Args:
        lines (pandas.DataFrame): Order lines with ProductID, OrderDate
            and Quantity.
        first_month (str): First full month, e.g. "1996-07".
        last_month (str): Last full month, e.g. "1998-04".

    Returns:
        pandas.Series: Std / mean of monthly units, indexed by ProductID;
        NaN where mean demand is zero.
    """
    months = pd.period_range(first_month, last_month, freq="M")
    month = lines["OrderDate"].dt.to_period("M")
    inside = lines[(month >= months[0]) & (month <= months[-1])]
    monthly = (
        inside.assign(Month=inside["OrderDate"].dt.to_period("M"))
        .groupby(["ProductID", "Month"])["Quantity"].sum()
        .unstack(fill_value=0)
        .reindex(columns=months, fill_value=0)
    )
    mean = monthly.mean(axis=1)
    return (monthly.std(axis=1, ddof=0) / mean).where(mean > 0)


# --- 3.4 Inventory risk ---------------------------------------------------

def months_of_cover(stock, monthly_demand):
    """Return how many months stock lasts at the given demand.

    Args:
        stock (pandas.Series): Units available.
        monthly_demand (pandas.Series): Units demanded per month.

    Returns:
        pandas.Series: ``stock / monthly_demand``; NaN where demand is 0.
    """
    demand = monthly_demand.astype(float)
    return (stock / demand.where(demand > 0)).astype(float)


def risk_tier(stock, on_order, reorder_level, monthly_demand, variability, config):
    """Assign each product a restocking risk tier (plan 3.4).

    Rules are checked in order: no recent demand, Critical, High, Watch;
    everything else is OK.

    Args:
        stock (pandas.Series): Units in stock.
        on_order (pandas.Series): Units on order.
        reorder_level (pandas.Series): Reorder level; 0 means no rule.
        monthly_demand (pandas.Series): Recent monthly demand.
        variability (pandas.Series): Demand coefficient of variation.
        config (northwind.config.Config): Tier thresholds.

    Returns:
        pandas.Series: Tier name for each product, same index.
    """
    cover = months_of_cover(stock, monthly_demand)
    pipeline = months_of_cover(stock + on_order, monthly_demand)
    conditions = [
        ~(monthly_demand > 0),
        (stock <= 0) | (pipeline < config.critical_cover),
        (cover < config.high_cover) & ((on_order <= 0) | (pipeline < config.high_cover)),
        (stock < reorder_level)
        | ((reorder_level <= 0) & (cover < config.watch_cover))
        | ((variability > config.high_variability) & (cover < config.watch_cover)),
    ]
    choices = ["No recent demand", "Critical", "High", "Watch"]
    return pd.Series(np.select(conditions, choices, default="OK"), index=stock.index)


# --- 3.5 Processing time --------------------------------------------------

def processing_days(order_date, shipped_date):
    """Return days from order to dispatch.

    Args:
        order_date (pandas.Series): Order dates.
        shipped_date (pandas.Series): Dispatch dates; NaT if not shipped.

    Returns:
        pandas.Series: Days as floats; NaN for unshipped orders.
    """
    return (shipped_date - order_date).dt.days.astype(float)


def slack_days(required_date, shipped_date):
    """Return days between dispatch and the customer's required date.

    Args:
        required_date (pandas.Series): Required dates.
        shipped_date (pandas.Series): Dispatch dates; NaT if not shipped.

    Returns:
        pandas.Series: Positive = early, negative = late; NaN if unshipped.
    """
    return (required_date - shipped_date).dt.days.astype(float)


def is_late(slack):
    """Flag orders dispatched after the required date.

    Args:
        slack (pandas.Series): Output of ``slack_days``.

    Returns:
        pandas.Series: True where slack < 0; False for unshipped orders.
    """
    return (slack < 0).fillna(False).astype(bool)


# --- 3.6 Freight ----------------------------------------------------------

def freight_per_unit(freight, units):
    """Return freight cost per unit shipped.

    Args:
        freight (pandas.Series): Freight per order.
        units (pandas.Series): Units per order.

    Returns:
        pandas.Series: ``freight / units``; NaN where units is 0.
    """
    return freight / units.where(units > 0)


def freight_share(freight, revenue):
    """Return freight as a share of order net revenue.

    Args:
        freight (pandas.Series): Freight per order.
        revenue (pandas.Series): Net revenue per order.

    Returns:
        pandas.Series: ``freight / revenue``; NaN where revenue is 0.
    """
    return freight / revenue.where(revenue > 0)


def size_band_edges(units):
    """Return quartile edges of order size.

    Args:
        units (pandas.Series): Units per order, all orders.

    Returns:
        numpy.ndarray: Five edges: min, 25th, 50th, 75th percentile, max.

    Raises:
        ValueError: If edges are not strictly increasing.
    """
    edges = np.quantile(units.dropna(), [0, 0.25, 0.5, 0.75, 1.0])
    if np.any(np.diff(edges) <= 0):
        raise ValueError(f"Size band edges are not distinct: {edges}")
    return edges


def assign_size_band(units, edges):
    """Label each order with its size band.

    Bands include their upper edge; the lowest band also includes the
    minimum.

    Args:
        units (pandas.Series): Units per order.
        edges (numpy.ndarray): Output of ``size_band_edges``.

    Returns:
        pandas.Series: Ordered categorical of ``SIZE_BAND_LABELS``.
    """
    return pd.cut(units, bins=edges, labels=list(SIZE_BAND_LABELS), include_lowest=True)


# --- 3.7 Opportunity size -------------------------------------------------

def excess_over_benchmark(values, benchmark, weights=None):
    """Return the total amount by which values exceed a benchmark.

    Values at or below the benchmark contribute zero, never a negative.

    Args:
        values (pandas.Series): Per-order measure, e.g. processing days.
        benchmark (float): Benchmark level.
        weights (pandas.Series | None): Multiplier per order, e.g. units
            for freight per unit; None means 1.

    Returns:
        float: Sum of ``max(0, value - benchmark) * weight``, ignoring NaN.
    """
    excess = (values - benchmark).clip(lower=0)
    if weights is not None:
        excess = excess * weights
    return float(excess.sum(skipna=True))
