"""Q1: rate markets on share change and customer concentration.

Shows how each market performed relative to the company, how much it
depends on one customer, and where sales attention could go
(plan.md section 3.2).
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from northwind import metrics

COMPANY = "All markets"

CAVEAT = (
    "Performance levels are directional. Each market has only about 13 to 42 orders per "
    "six-month window and a few large orders move the totals, so no market's level is "
    "statistically certain (see the uncertainty table in the appendix). The direction of "
    "each market's performance holds in every robustness check."
)


@dataclass
class Q1Result:
    """Outputs of the Q1 market analysis.

    Attributes:
        quarterly (pandas.DataFrame): Revenue, orders, customers and
            share of company revenue per market and quarter.
        scorecard (pandas.DataFrame): One row per market: growth,
            relative growth, drivers, concentration, recommended action
            and flags.
        movers (pandas.DataFrame): Largest gaining and losing accounts
            per market.
        company (dict): Company-wide revenue, orders and growth.
        robustness (pandas.DataFrame): Performance levels under
            alternative definitions (plan 8.3).
        bootstrap (pandas.DataFrame): Relative-growth intervals for
            markets that met a plan 4.4 trigger; empty if none did.
        uncertainty (pandas.DataFrame): Relative-growth intervals for
            every market, for the appendix.
        summaries (dict[str, str]): One plain-language recommendation
            per market.
        caveat (str): Uncertainty statement shown with the Q1 results.
    """

    quarterly: pd.DataFrame
    scorecard: pd.DataFrame
    movers: pd.DataFrame
    company: dict
    robustness: pd.DataFrame
    bootstrap: pd.DataFrame
    uncertainty: pd.DataFrame
    summaries: dict
    windows: pd.DataFrame = None
    window_growth: dict = None
    caveat: str = CAVEAT


# --- Inputs -----------------------------------------------------------------

def prepare_lines(model, config, basis="customer"):
    """Return order lines with the market each one belongs to.

    Args:
        model (northwind.model.Model): Joined tables.
        config (northwind.config.Config): Region maps.
        basis (str): "customer" uses the customer's country; "ship_to"
            uses the order's ship-to country.

    Returns:
        pandas.DataFrame: OrderID, CustomerID, CustomerName, Quarter,
        NetRevenue and Market.

    Raises:
        ValueError: If ``basis`` is not recognised.
    """
    cols = ["OrderID", "CustomerID", "CustomerName", "Quarter", "NetRevenue", "Market"]
    lines = model.order_lines[cols].copy()
    if basis == "ship_to":
        ship_country = lines["OrderID"].map(model.orders.set_index("OrderID")["ShipCountry"])
        lines["Market"] = metrics.map_regions(ship_country, config.market_groups)
    elif basis != "customer":
        raise ValueError(f"Unknown market basis: {basis}")
    return lines


def _in_quarters(lines, quarters):
    """Return the lines whose quarter is in ``quarters``.

    Args:
        lines (pandas.DataFrame): Lines with a Quarter column.
        quarters (Iterable[str]): Quarters such as "1997Q4".

    Returns:
        pandas.DataFrame: Matching lines.
    """
    return lines[lines["Quarter"].astype(str).isin(set(quarters))]


def _full_quarters(config):
    """Return the complete quarters in the analysis period.

    Args:
        config (northwind.config.Config): First and last full quarter.

    Returns:
        list[str]: Quarters in order, e.g. ["1996Q3", ..., "1998Q1"].
    """
    return [str(q) for q in pd.period_range(config.first_full_quarter,
                                            config.last_full_quarter, freq="Q")]


def _latest_four(config):
    """Return the four most recent complete quarters.

    Args:
        config (northwind.config.Config): Last full quarter.

    Returns:
        list[str]: Four quarters ending at ``config.last_full_quarter``.
    """
    return [str(q) for q in pd.period_range(end=config.last_full_quarter, periods=4, freq="Q")]


# --- Tables -----------------------------------------------------------------

def quarterly_table(lines, config):
    """Return revenue, orders, customers and share per market and quarter.

    Args:
        lines (pandas.DataFrame): Output of ``prepare_lines``.
        config (northwind.config.Config): Last full quarter.

    Returns:
        pandas.DataFrame: One row per market and quarter (all quarters,
        zero-filled), with Share of company revenue and IsComplete False
        for the partial last quarter.
    """
    table = lines.groupby(["Market", "Quarter"]).agg(
        Revenue=("NetRevenue", "sum"),
        Orders=("OrderID", "nunique"),
        Customers=("CustomerID", "nunique"),
    )
    quarters = pd.period_range(lines["Quarter"].min(), lines["Quarter"].max(), freq="Q")
    grid = pd.MultiIndex.from_product([sorted(lines["Market"].unique()), quarters],
                                      names=["Market", "Quarter"])
    table = table.reindex(grid, fill_value=0).reset_index()
    company = table.groupby("Quarter")["Revenue"].transform("sum")
    table["Share"] = table["Revenue"] / company.where(company > 0)
    table["IsComplete"] = table["Quarter"] <= pd.Period(config.last_full_quarter, freq="Q")
    return table


def _trend(series):
    """Return a linear trend per period as a share of the average level.

    Args:
        series (pandas.Series): Values in time order; NaN are dropped.

    Returns:
        float: Least-squares slope divided by the mean; NaN if fewer
            than two values or the mean is not positive.
    """
    values = series.dropna().to_numpy(dtype=float)
    if len(values) < 2 or values.mean() <= 0:
        return float("nan")
    slope = np.polyfit(np.arange(len(values)), values, 1)[0]
    return float(slope / values.mean())


def _sign(value):
    """Return -1, 0 or 1; 0 for NaN.

    Args:
        value (float): Number to classify.

    Returns:
        int: Sign of ``value``.
    """
    return 0 if pd.isna(value) else int(np.sign(value))


def scorecard(lines, config, current=None, prior=None):
    """Score every market on relative performance and concentration.

    Company totals are taken from ``lines`` itself, so alternative
    inputs (e.g. a customer removed) are compared with their own company
    total.

    Args:
        lines (pandas.DataFrame): Output of ``prepare_lines``.
        config (northwind.config.Config): Windows and thresholds.
        current (tuple[str, ...] | None): Later window; None uses
            ``config.current_window``.
        prior (tuple[str, ...] | None): Earlier window; None uses
            ``config.prior_window``.

    Returns:
        tuple[pandas.DataFrame, pandas.DataFrame, dict]: The scorecard
        (one row per market), the movers table and company totals.
    """
    current = tuple(current or config.current_window)
    prior = tuple(prior or config.prior_window)
    cur, pri = _in_quarters(lines, current), _in_quarters(lines, prior)
    latest = _in_quarters(lines, _latest_four(config))
    full = _full_quarters(config)
    last_q = pd.Period(config.last_full_quarter, freq="Q")
    year_ago = str(last_q - 4)
    names = lines.drop_duplicates("CustomerID").set_index("CustomerID")["CustomerName"]

    company_r0, company_r1 = float(pri["NetRevenue"].sum()), float(cur["NetRevenue"].sum())
    company = {
        "RevenuePrior": company_r0,
        "RevenueCurrent": company_r1,
        "Growth": metrics.window_growth(company_r0, company_r1),
        "OrdersPrior": pri["OrderID"].nunique(),
        "OrdersCurrent": cur["OrderID"].nunique(),
    }
    company["OrdersEffect"], company["SizeEffect"] = metrics.decompose_change(
        company_r0, company["OrdersPrior"], company_r1, company["OrdersCurrent"])
    quarter_totals = (lines.groupby(lines["Quarter"].astype(str))["NetRevenue"].sum()
                      .reindex(full, fill_value=0))

    rows, movers = [], []
    for market in sorted(lines["Market"].unique()):
        p, c = pri[pri["Market"] == market], cur[cur["Market"] == market]
        r0, r1 = float(p["NetRevenue"].sum()), float(c["NetRevenue"].sum())
        o0, o1 = p["OrderID"].nunique(), c["OrderID"].nunique()
        share0 = r0 / company_r0 if company_r0 > 0 else float("nan")
        share1 = r1 / company_r1 if company_r1 > 0 else float("nan")
        rel = metrics.relative_growth(share0, share1)
        orders_effect, size_effect = metrics.decompose_change(r0, o0, r1, o1)
        contrib = metrics.account_contributions(
            p.groupby("CustomerID")["NetRevenue"].sum(),
            c.groupby("CustomerID")["NetRevenue"].sum(),
        )
        by_customer = latest[latest["Market"] == market].groupby("CustomerID")["NetRevenue"].sum()
        dependence = metrics.top_share(by_customer) if len(by_customer) else float("nan")
        compared = pd.concat([p, c]).groupby("CustomerID")["NetRevenue"].sum()
        dependence_compared = metrics.top_share(compared) if len(compared) else float("nan")
        top_id = by_customer.idxmax() if len(by_customer) else None
        top_change = float(contrib.get(top_id, 0.0)) if top_id is not None else float("nan")
        top_prior = float(p.loc[p["CustomerID"] == top_id, "NetRevenue"].sum()) if top_id is not None else 0.0
        top_increase = metrics.top_share_of_increase(contrib)

        market_lines = lines[lines["Market"] == market]
        quarterly = (market_lines.groupby(market_lines["Quarter"].astype(str))["NetRevenue"].sum()
                     .reindex(full, fill_value=0))
        share_by_q = quarterly / quarter_totals.where(quarter_totals > 0)
        q_rel = metrics.relative_growth(share_by_q[year_ago], share_by_q[str(last_q)])
        share_trend = _trend(share_by_q)
        signs = {_sign(rel), _sign(q_rel), _sign(share_trend)}

        performance = metrics.performance_level(rel, config)
        risk = metrics.concentration_risk(dependence, config)
        rows.append({
            "Market": market,
            "IsFocus": market in config.focus_markets,
            "RevenuePrior": r0,
            "RevenueCurrent": r1,
            "Change": r1 - r0,
            "Growth": metrics.window_growth(r0, r1),
            "SharePrior": share0,
            "ShareCurrent": share1,
            "RelativeGrowth": rel,
            "OrdersPrior": o0,
            "OrdersCurrent": o1,
            "AvgOrderPrior": r0 / o0 if o0 else float("nan"),
            "AvgOrderCurrent": r1 / o1 if o1 else float("nan"),
            "OrdersEffect": orders_effect,
            "SizeEffect": size_effect,
            "QuarterRelativeGrowth": q_rel,
            "ShareTrend": share_trend,
            "Consistent": len(signs) == 1 and 0 not in signs,
            "Customers": int(market_lines["CustomerID"].nunique()),
            "PositiveAccounts": int((contrib > 0).sum()),
            "TopIncreaseShare": top_increase,
            "TopCustomer": names.get(top_id) if top_id is not None else None,
            "TopCustomerChange": top_change,
            "TopCustomerGrowth": top_change / top_prior if top_prior > 0 else float("nan"),
            "Dependence": dependence,
            "DependenceCompared": dependence_compared,
            "Performance": performance,
            "ConcentrationRisk": risk,
            "RecommendedAction": metrics.recommended_action(performance, risk, o0, o1, config),
            "FlagNearConcentrationLine": metrics.near_concentration_line(dependence, config),
            "FlagNarrowGrowth": metrics.narrow_growth(top_increase, config),
        })

        n = config.movers_per_side
        picks = pd.concat([contrib[contrib > 0].head(n), contrib[contrib < 0].tail(n)])
        for customer, change in picks.items():
            movers.append({
                "Market": market,
                "CustomerID": customer,
                "CustomerName": names.get(customer),
                "RevenuePrior": float(p.loc[p["CustomerID"] == customer, "NetRevenue"].sum()),
                "RevenueCurrent": float(c.loc[c["CustomerID"] == customer, "NetRevenue"].sum()),
                "Change": float(change),
                "Direction": "Gain" if change > 0 else "Loss",
            })

    card = pd.DataFrame(rows).sort_values("RelativeGrowth", ascending=False, na_position="last")
    return card.reset_index(drop=True), pd.DataFrame(movers), company


# --- Plan 4.4: conditional bootstrap ----------------------------------------

def needs_bootstrap(row, config):
    """Decide whether a market meets a plan 4.4 trigger.

    Args:
        row (pandas.Series): One scorecard row.
        config (northwind.config.Config): Thresholds and margin.

    Returns:
        str | None: The reason, or None if no trigger is met.
    """
    if row["RecommendedAction"] == metrics.INSUFFICIENT or pd.isna(row["RelativeGrowth"]):
        return None
    gaps = [abs(row["RelativeGrowth"] - config.outperform_threshold),
            abs(row["RelativeGrowth"] - config.underperform_threshold)]
    if min(gaps) <= config.near_threshold_margin:
        return "relative growth near a performance threshold"
    if not row["Consistent"]:
        return "share measures disagree in direction"
    return None


def bootstrap_relative_growth(lines, market, config):
    """Return a bootstrap interval for a market's relative growth.

    All company orders in each window are resampled with replacement and
    the market's share is recomputed, so both the market's and the
    company's uncertainty are reflected.

    Args:
        lines (pandas.DataFrame): Output of ``prepare_lines``.
        market (str): Market to evaluate.
        config (northwind.config.Config): Windows, seed, resamples and
            interval width.

    Returns:
        tuple[float, float]: Lower and upper bounds of the interval.
    """
    rng = np.random.default_rng(config.seed)
    shares = []
    for window in (config.prior_window, config.current_window):
        orders = _in_quarters(lines, window).groupby("OrderID").agg(
            Revenue=("NetRevenue", "sum"), Market=("Market", "first"))
        revenue = orders["Revenue"].to_numpy()
        in_market = (orders["Market"] == market).to_numpy()
        idx = rng.integers(0, len(revenue), (config.bootstrap_resamples, len(revenue)))
        sampled = revenue[idx]
        shares.append((sampled * in_market[idx]).sum(axis=1) / sampled.sum(axis=1))
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = shares[1] / shares[0] - 1
    rel = rel[np.isfinite(rel)]
    tail = (1 - config.bootstrap_interval) / 2
    return float(np.quantile(rel, tail)), float(np.quantile(rel, 1 - tail))


def performance_confidence(card, lines, config):
    """Add PerformanceConfidence and FlagNotConclusive to the scorecard.

    "Clear" means no trigger was met. Otherwise the bootstrap decides:
    "Confirmed" unless the interval straddles a performance threshold,
    in which case "Not conclusive".

    Args:
        card (pandas.DataFrame): Output of ``scorecard``; modified in
            place.
        lines (pandas.DataFrame): Output of ``prepare_lines``.
        config (northwind.config.Config): Thresholds and bootstrap
            settings.

    Returns:
        pandas.DataFrame: One row per triggered market with the reason
        and interval; empty if nothing was triggered.
    """
    confidence, records = [], []
    thresholds = (config.outperform_threshold, config.underperform_threshold)
    for _, row in card.iterrows():
        if row["RecommendedAction"] == metrics.INSUFFICIENT:
            confidence.append("n/a")
            continue
        reason = needs_bootstrap(row, config)
        if reason is None:
            confidence.append("Clear")
            continue
        low, high = bootstrap_relative_growth(lines, row["Market"], config)
        verdict = "Not conclusive" if any(low < t < high for t in thresholds) else "Confirmed"
        confidence.append(verdict)
        records.append({"Market": row["Market"], "Reason": reason,
                        "RelativeGrowth": row["RelativeGrowth"], "Low": low, "High": high,
                        "Performance": row["Performance"], "Verdict": verdict})
    card["PerformanceConfidence"] = confidence
    card["FlagNotConclusive"] = card["PerformanceConfidence"] == "Not conclusive"
    return pd.DataFrame(records, columns=["Market", "Reason", "RelativeGrowth", "Low",
                                          "High", "Performance", "Verdict"])


def uncertainty_table(card, lines, config):
    """Return relative-growth intervals for every market (appendix).

    Args:
        card (pandas.DataFrame): Scorecard.
        lines (pandas.DataFrame): Output of ``prepare_lines``.
        config (northwind.config.Config): Thresholds and bootstrap
            settings.

    Returns:
        pandas.DataFrame: Market, RelativeGrowth, Low, High, Performance
        and CrossesThreshold (True if the interval spans a performance
        threshold).
    """
    thresholds = (config.outperform_threshold, config.underperform_threshold)
    rows = []
    for _, row in card.iterrows():
        if row["RecommendedAction"] == metrics.INSUFFICIENT:
            continue
        low, high = bootstrap_relative_growth(lines, row["Market"], config)
        rows.append({"Market": row["Market"], "RelativeGrowth": row["RelativeGrowth"],
                     "Low": low, "High": high, "Performance": row["Performance"],
                     "CrossesThreshold": any(low < t < high for t in thresholds)})
    return pd.DataFrame(rows)


# --- Plan 8.3: robustness ---------------------------------------------------

def robustness(model, lines, card, config):
    """Recompute performance levels under three alternative definitions.

    Alternatives: ship-to country as the market; the latest quarter vs
    the same quarter a year earlier; each market's largest customer
    removed. A level holds if it is unchanged in at least 2 of 3.

    Args:
        model (northwind.model.Model): Joined tables.
        lines (pandas.DataFrame): Output of ``prepare_lines``.
        card (pandas.DataFrame): Base scorecard.
        config (northwind.config.Config): Windows and thresholds.

    Returns:
        pandas.DataFrame: Base and alternative performance levels per
        market, the number of agreements and a Holds flag.
    """
    last_q = pd.Period(config.last_full_quarter, freq="Q")
    ship, _, _ = scorecard(prepare_lines(model, config, "ship_to"), config)
    quarter, _, _ = scorecard(lines, config, current=(str(last_q),), prior=(str(last_q - 4),))
    latest = _in_quarters(lines, _latest_four(config))
    top = latest.groupby(["Market", "CustomerID"])["NetRevenue"].sum().groupby(level=0).idxmax()
    drop = lines.set_index(["Market", "CustomerID"]).index.isin(list(top))
    no_top, _, _ = scorecard(lines[~drop], config)

    table = card[["Market", "IsFocus", "Performance"]].rename(columns={"Performance": "Base"})
    alts = {"ShipTo": ship, "LatestQuarter": quarter, "NoTopCustomer": no_top}
    for name, alt in alts.items():
        table = table.merge(alt[["Market", "Performance"]].rename(columns={"Performance": name}),
                            on="Market", how="left")
    table["Agreements"] = sum((table[a] == table["Base"]).astype(int) for a in alts)
    table["Holds"] = table["Agreements"] >= 2
    return table


def window_check(lines, config):
    """Check whether each market's share moved the same way in other periods.

    Compares the base two-quarter windows with the latest quarter
    against the same quarter a year earlier, and with the quarter before
    that against its year-earlier quarter (added after the independent
    review).

    Args:
        lines (pandas.DataFrame): Output of ``prepare_lines``.
        config (northwind.config.Config): Windows.

    Returns:
        tuple[pandas.DataFrame, dict]: Relative growth per market under
        each comparison with a SameDirection flag, and company growth
        per comparison.
    """
    last = pd.Period(config.last_full_quarter, freq="Q")
    pairs = {
        "Base (2 quarters)": (None, None),
        f"{last} vs {last - 4}": ((str(last - 4),), (str(last),)),
        f"{last - 1} vs {last - 5}": ((str(last - 5),), (str(last - 1),)),
    }
    table, company = {}, {}
    for name, (prior, current) in pairs.items():
        card, _, comp = scorecard(lines, config, current=current, prior=prior)
        table[name] = card.set_index("Market")["RelativeGrowth"]
        company[name] = comp["Growth"]
    out = pd.DataFrame(table)
    out["SameDirection"] = np.sign(out).nunique(axis=1).eq(1) & out.ne(0).all(axis=1)
    return out.reset_index(), company


# --- Summary text -----------------------------------------------------------

def _money(value):
    """Format dollars compactly, e.g. $12.3K.

    Args:
        value (float): Amount in dollars.

    Returns:
        str: Formatted amount.
    """
    return f"${value / 1000:,.1f}K"


def flag_list(row):
    """Return the warning flags raised for one market.

    Args:
        row (pandas.Series): One scorecard row with confidence added.

    Returns:
        list[str]: Flag descriptions; empty if none.
    """
    flags = []
    if row["FlagNearConcentrationLine"]:
        flags.append(f"near the 50% concentration line ({row['Dependence']:.0%})")
    if row["FlagNarrowGrowth"]:
        if row["TopIncreaseShare"] > 1:
            flags.append("narrow growth (one account's gain was larger than the market's whole "
                         "net increase, because other accounts declined)")
        else:
            flags.append(f"narrow growth ({row['TopIncreaseShare']:.0%} of the increase from one account)")
    if row.get("FlagNotConclusive", False):
        flags.append("performance level not conclusive")
    return flags


def summarise(card, movers, company):
    """Write one plain-language recommendation per market.

    Args:
        card (pandas.DataFrame): Scorecard with confidence added.
        movers (pandas.DataFrame): Movers table.
        company (dict): Company totals from ``scorecard``.

    Returns:
        dict[str, str]: Text keyed by market.
    """
    out = {}
    for _, r in card.iterrows():
        if r["RecommendedAction"] == metrics.INSUFFICIENT:
            out[r["Market"]] = (f"{r['Market']}: too few orders to judge "
                                f"({r['OrdersPrior']} then {r['OrdersCurrent']}).")
            continue
        m = movers[movers["Market"] == r["Market"]]
        lead = m.loc[m["Change"].abs().idxmax()] if len(m) else None
        mover = (f" Biggest account change: {lead['CustomerName']} "
                 f"({'+' if lead['Change'] > 0 else '−'}{_money(abs(lead['Change']))})."
                 if lead is not None else "")
        flags = flag_list(r)
        out[r["Market"]] = (
            f"{r['Market']}: revenue {r['Growth']:+.0%} vs the company's {company['Growth']:+.0%}, "
            f"so its share moved from {r['SharePrior']:.1%} to {r['ShareCurrent']:.1%} "
            f"({r['Performance'].lower()}). {r['TopCustomer']} holds {r['Dependence']:.0%} of the "
            f"market ({r['ConcentrationRisk'].lower()} concentration).{mover} "
            f"Suggested focus: {r['RecommendedAction']}: "
            f"{metrics.ACTION_TEXT[r['RecommendedAction']]}."
            + (f" Flags: {'; '.join(flags)}." if flags else "")
        )
    return out


# --- Entry point ------------------------------------------------------------

def run(model, config):
    """Run the full Q1 analysis.

    Args:
        model (northwind.model.Model): Joined tables.
        config (northwind.config.Config): Settings.

    Returns:
        Q1Result: All Q1 tables and summaries.
    """
    lines = prepare_lines(model, config)
    card, movers, company = scorecard(lines, config)
    boot = performance_confidence(card, lines, config)
    windows, window_growth_ = window_check(lines, config)
    return Q1Result(
        windows=windows,
        window_growth=window_growth_,
        quarterly=quarterly_table(lines, config),
        scorecard=card,
        movers=movers,
        company=company,
        robustness=robustness(model, lines, card, config),
        bootstrap=boot,
        uncertainty=uncertainty_table(card, lines, config),
        summaries=summarise(card, movers, company),
    )
