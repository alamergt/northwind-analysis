"""Assemble the self-contained HTML report (plan.md section 5)."""

import html
import importlib.metadata
import json
import math
import sys
from datetime import datetime, timezone

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

from northwind import metrics
from northwind.config import ROOT

LIBRARIES = ("pandas", "numpy", "openpyxl", "matplotlib", "jinja2")


# --- Formatting ---------------------------------------------------------------

def pct(value, signed=False, digits=0):
    """Format a fraction as a percentage.

    Args:
        value (float): Fraction, e.g. 0.25.
        signed (bool): Show a leading + for positive values.
        digits (int): Decimal places.

    Returns:
        str: e.g. "+25%", or an em dash for missing values.
    """
    if pd.isna(value):
        return "—"
    text = f"{value:+.{digits}%}" if signed else f"{value:.{digits}%}"
    return text.replace("-", "−")


def money(value, digits=1):
    """Format dollars compactly.

    Args:
        value (float): Amount in dollars.
        digits (int): Decimals for thousands.

    Returns:
        str: e.g. "$25.9K", "$950", "−$10.5K".
    """
    if pd.isna(value):
        return "—"
    sign = "−" if value < 0 else ""
    value = abs(value)
    return f"{sign}${value / 1000:,.{digits}f}K" if value >= 1000 else f"{sign}${value:,.0f}"


def num(value, digits=0):
    """Format a number with thousands separators.

    Args:
        value (float): Number.
        digits (int): Decimal places.

    Returns:
        str: Formatted number, or an em dash for missing values.
    """
    return "—" if pd.isna(value) else f"{value:,.{digits}f}".replace("-", "−")


def table(frame, columns):
    """Build table data for the template.

    Args:
        frame (pandas.DataFrame): Source rows.
        columns (list[tuple[str, str, Callable | None, bool]]): Header,
            source column, formatter (None = str) and whether the column
            is numeric (right-aligned).

    Returns:
        dict: ``headers`` (list of (text, numeric)) and ``rows`` (list
            of lists of (text, numeric)).
    """
    rows = []
    for _, record in frame.iterrows():
        rows.append([((fmt or str)(record[col]), numeric) for _, col, fmt, numeric in columns])
    return {"headers": [(h, numeric) for h, _, _, numeric in columns], "rows": rows}


def join_names(names):
    """Join names as plain English: "A", "A and B", "A, B and C".

    Args:
        names (list[str]): Names.

    Returns:
        str: Joined text.
    """
    names = list(names)
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


# --- Question sections --------------------------------------------------------

def q1_section(q1, charts):
    """Build the Q1 section context.

    Args:
        q1 (northwind.q1_markets.Q1Result): Q1 results.
        charts (dict[str, str]): Rendered charts.

    Returns:
        dict: Template context for Q1.
    """
    card = q1.scorecard
    gained = card.loc[card["Performance"] == "Outperforming", "Market"].tolist()
    lost = card.loc[card["Performance"] == "Underperforming", "Market"].tolist()
    verbs = {"Invest": "invest in", "Broaden": "broaden", "Protect": "protect", "Rescue": "rescue",
             "Diagnose": "diagnose"}
    focus = []
    for action, verb in verbs.items():
        markets = card.loc[card["RecommendedAction"] == action, "Market"].tolist()
        if markets:
            focus.append(f"<strong>{verb}</strong> {html.escape(join_names(markets))}")
    answer = (
        f"Company revenue grew {pct(q1.company['Growth'], True)} year on year, mostly from more orders. "
        f"{join_names(gained)} grew faster than the company and gained share; "
        f"{join_names(lost)} lost share. Suggested focus: {'; '.join(focus)}. "
        "Markets not listed are in line with the company and look adequately covered."
    )

    def flags(row):
        """Return the flag labels for one market, or a dash.

        Args:
            row (pandas.Series): Scorecard row.

        Returns:
            str: Flags joined by semicolons, or "—".
        """
        return "; ".join(q1_flag_text(row)) or "—"

    # After the independent review: a market's share direction is only called
    # "clear" when it is the same in all three period comparisons, and actions
    # for the other markets are marked tentative.
    win = q1.windows.set_index("Market")
    steady = win["SameDirection"]
    clear_gain = [m for m in gained if steady.get(m, False)]
    clear_loss = [m for m in lost if steady.get(m, False)]
    flip = [m for m in gained + lost if not steady.get(m, False)]
    growths = list(q1.window_growth.values())
    key = (f"Revenue grew {pct(q1.company['Growth'], True)} (between {pct(min(growths), True)} and "
           f"{pct(max(growths), True)} depending on the quarters compared). "
           + (f"{join_names(clear_gain)} clearly gained share" if clear_gain else "")
           + (f"; {join_names(clear_loss)} clearly lost it" if clear_loss else "")
           + (f". {join_names(flip)} change direction depending on the quarters compared." if flip else "."))
    broaden = card[card["RecommendedAction"] == "Broaden"]
    losses = q1.movers[q1.movers["Market"].isin(clear_loss) & (q1.movers["Direction"] == "Loss")]
    top_losses = losses.nsmallest(3, "Change")
    meaning = (
        (f"{join_names([f'{r.Market} ({r.TopCustomer})' for r in broaden.itertuples()])} rely on one "
         f"customer for about half their revenue "
         f"({join_names([f'{pct(min(r.Dependence, r.DependenceCompared))}–{pct(max(r.Dependence, r.DependenceCompared))}' for r in broaden.itertuples()])}"
         " depending on the period), so their concentration risk is borderline. " if len(broaden) else "")
        + (f"The clearest losses trace to single accounts: "
           f"{join_names([f'{r.CustomerName} ({money(r.Change)})' for r in top_losses.itertuples()])}."
           if len(top_losses) else "")
    )

    def tentative(market):
        """Say whether a market's action should be marked tentative.

        Args:
            market (str): Market name.

        Returns:
            bool: True if its share direction changes between period
            comparisons or its performance level isn't conclusive.
        """
        row = card.set_index("Market").loc[market]
        # The concentration label is itself uncertain when the two ways of
        # measuring dependence fall on opposite sides of the 50% line.
        line = 0.5
        straddles = (min(row["Dependence"], row["DependenceCompared"]) <= line
                     < max(row["Dependence"], row["DependenceCompared"]))
        hinges = row["RecommendedAction"] in ("Broaden", "Protect", "Rescue") and straddles
        return ((not steady.get(market, False)) or bool(row.get("FlagNotConclusive", False))
                or hinges)

    order = ["Diagnose", "Rescue", "Broaden", "Invest"]
    actions = []
    for action in order:
        for r in card[card["RecommendedAction"] == action].itertuples():
            text = market_action(card.set_index("Market").loc[r.Market], q1.movers)
            lost = q1.movers[(q1.movers["Market"] == r.Market) & (q1.movers["Direction"] == "Loss")]
            actions.append({"text": text, "market": r.Market,
                            "status": "Tentative" if tentative(r.Market) else "Confirmed",
                            "weight": float(-lost["Change"].min()) if not lost.empty else 0.0})
    actions.sort(key=lambda a: (a["status"] != "Confirmed", -a["weight"]))

    rows = card.assign(Flags=card.apply(flags, axis=1),
                       ShareMove=card.apply(lambda r: f"{pct(r['SharePrior'], digits=1)} → "
                                                      f"{pct(r['ShareCurrent'], digits=1)}", axis=1))
    return {
        "answer": key,
        "main_chart": charts["q1_main"],
        "support_chart": charts["q1_support"],
        "table": table(rows, [
            ("Market", "Market", None, False),
            ("Growth", "Growth", lambda v: pct(v, True), True),
            ("Share of company revenue", "ShareMove", None, True),
            ("Relative to company", "RelativeGrowth", lambda v: pct(v, True), True),
            ("Performance", "Performance", None, False),
            ("Largest customer", "Dependence", pct, True),
            ("Concentration", "ConcentrationRisk", None, False),
            ("Suggested focus", "RecommendedAction", None, False),
            ("Flags", "Flags", None, False),
        ]),
        "caveat": q1.caveat,
        "company": q1.company,
        "interpretation": q1_interpretation(q1),
        "key": key,
        "meaning": meaning,
        "actions": actions,
        "clear_gain": clear_gain,
        "clear_loss": clear_loss,
        "top_losses": [(r.CustomerName, r.Change, r.Market) for r in top_losses.itertuples()],
    }


def market_action(row, movers):
    """Write one specific action for a market: who to contact and why.

    Args:
        row (pandas.Series): Scorecard row (Market may be the index
            name).
        movers (pandas.DataFrame): Q1 movers table.

    Returns:
        str: Action naming the first account and the next step.
    """
    market = row.get("Market", row.name)
    m = movers[movers["Market"] == market]
    loss = m[m["Direction"] == "Loss"].sort_values("Change")
    gain = m[(m["Direction"] == "Gain") & (m["CustomerName"] != row["TopCustomer"])]
    gain = gain.sort_values("Change", ascending=False)
    action = row["RecommendedAction"]
    if action in ("Diagnose", "Rescue") and not loss.empty:
        first = loss.iloc[0]
        keep = (f"; keep {row['TopCustomer']} close" if action == "Rescue" else "")
        return (f"{market}: call {first['CustomerName']} (revenue {money(first['Change'])}) "
                f"to find out why orders fell{keep}")
    if action == "Broaden":
        nxt = join_names(gain["CustomerName"].head(2).tolist())
        return (f"{market}: keep {row['TopCustomer']} close and grow "
                + (f"{nxt}" if nxt else "other accounts")
                + " so less depends on one buyer")
    if action == "Invest":
        top = m[m["Direction"] == "Gain"].sort_values("Change", ascending=False)
        lead = top.iloc[0]["CustomerName"] if not top.empty else "the leading accounts"
        return (f"{market}: confirm {lead}'s orders will continue, then add "
                "sales coverage")
    return f"{market}: {metrics_text(action)}"


def metrics_text(action):
    """Return the generic description of an action.

    Args:
        action (str): Action name.

    Returns:
        str: Description from the metrics module.
    """
    return metrics.ACTION_TEXT.get(action, action.lower())


def rescue_detail(row, movers, company_growth=None):
    """Explain a Rescue market from the data rather than assuming the cause.

    A Rescue market is losing share and depends on one customer. Whether
    that customer is the problem depends on its own revenue change.

    Args:
        row (pandas.Series): Scorecard row for the market (Market may be
            the index name).
        movers (pandas.DataFrame): Q1 movers table.
        company_growth (float | None): Company growth, to say whether
            the key account itself kept pace.

    Returns:
        tuple[str, str]: Short action for the summary, and an
        interpretation sentence.
    """
    market = row.get("Market", row.name)
    top, change, dep = row["TopCustomer"], row["TopCustomerChange"], row["Dependence"]
    growth = row.get("TopCustomerGrowth", float("nan"))
    losses = movers[(movers["Market"] == market) & (movers["Direction"] == "Loss")]
    worst = losses.loc[losses["Change"].idxmin()] if not losses.empty else None
    if change > 0:
        pace = ""
        if not pd.isna(growth):
            pace = f" ({pct(growth, True)}"
            if company_growth is not None and growth < company_growth:
                pace += f", a little below the company's {pct(company_growth, True)}"
            pace += ")"
        sentence = (f"{top} holds {pct(dep)} of the market and its revenue rose {money(change)}{pace}, so it "
                    "isn't the main cause: the rest of the market grew more slowly than the company"
                    + (f" and {worst['CustomerName']} fell {money(abs(worst['Change']))}" if worst is not None
                       else "")
                    + f". Keep {top} close and work on the rest of the market.")
        action = (f"Rescue {market}: keep {top} close"
                  + (f", recover {worst['CustomerName']}" if worst is not None else "")
                  + " and widen the customer base")
    else:
        sentence = (f"{top} holds {pct(dep)} of the market and its revenue fell {money(abs(change))}, so a "
                    "review of that relationship comes first.")
        action = f"Rescue {market}: review the {top} relationship"
    return action, sentence


def q1_interpretation(q1):
    """Turn the Q1 results into business implications, one per market group.

    Args:
        q1 (northwind.q1_markets.Q1Result): Q1 results.

    Returns:
        list[str]: Interpretation bullets (plain text).
    """
    card, movers = q1.scorecard.set_index("Market"), q1.movers
    same = q1.windows.set_index("Market")["SameDirection"].to_dict()

    def biggest(market, direction):
        """Return the account with the largest change in one direction.

        Args:
            market (str): Market name.
            direction (str): "Gain" or "Loss".

        Returns:
            str | None: "Name ($change)", or None if there is none.
        """
        m = movers[(movers["Market"] == market) & (movers["Direction"] == direction)]
        if m.empty:
            return None
        row = m.loc[m["Change"].abs().idxmax()]
        return f"{row['CustomerName']} ({money(row['Change'])})"

    def share(market):
        """Return a market's share of revenue before and after.

        Args:
            market (str): Market name.

        Returns:
            str: e.g. "10.6% → 19.7%".
        """
        r = card.loc[market]
        return f"{pct(r['SharePrior'], digits=1)} → {pct(r['ShareCurrent'], digits=1)}"

    out = []
    for market, r in card.iterrows():
        action = r["RecommendedAction"]
        if action == "Broaden":
            out.append(f"{market} (broaden): share rose {share(market)}, but {r['TopCustomer']} holds "
                       f"{pct(r['Dependence'])} of the market over the last four quarters "
                       f"({pct(r['DependenceCompared'])} over the compared periods), right at the 50% line. "
                       "Protecting that relationship and developing the next accounts would keep the growth "
                       "from resting on one buyer.")
        elif action == "Invest":
            note = ""
            if r["FlagNarrowGrowth"]:
                note = (f" Much of the increase came from {biggest(market, 'Gain')}, so it's worth confirming "
                        "that growth is repeatable before adding sales capacity.")
            out.append(f"{market} (invest): share rose {share(market)} without heavy dependence on one "
                       f"customer (largest {pct(r['Dependence'])})." + note)
        elif action == "Rescue":
            out.append(f"{market} (rescue): share fell {share(market)}. " + rescue_detail(r, movers, q1.company["Growth"])[1])
        elif action == "Diagnose":
            lost = biggest(market, "Loss")
            out.append(f"{market} (diagnose): share fell {share(market)}."
                       + (f" The largest single drop was {lost}, so an account-recovery conversation is a "
                          "cheaper first step than new coverage." if lost else ""))
        if action in ("Broaden", "Invest", "Rescue", "Diagnose") and not same.get(market, True):
            out[-1] += (" Tentative: this market's share moved the other way in at least one other "
                        "period comparison (see the appendix).")
        elif action in ("Broaden", "Invest", "Rescue", "Diagnose") and r.get("FlagNotConclusive", False):
            out[-1] += " Tentative: the bootstrap check marks this market's performance level as not conclusive."
    steady = [m for m, r in card.iterrows() if r["RecommendedAction"] in ("Maintain", "Protect")]
    near = [f"{m} ({pct(card.loc[m, 'Dependence'])})" for m in steady if card.loc[m, "FlagNearConcentrationLine"]]
    if steady:
        out.append(f"{join_names(steady)} are keeping pace with the company; no change in coverage is suggested"
                   + (f", but watch {join_names(near)}, whose largest customer is close to the 50% line."
                      if near else "."))
    out.append("Order counts per market are small, so these are directional recommendations to test with the "
               "sales team, not a basis for moving people on their own.")
    return out


def shortfall_range(short):
    """Return the top products' shortfall to one month of demand.

    Args:
        short (pandas.DataFrame): Q2 shortlist.

    Returns:
        tuple[float, float]: Shortfall using long-run demand and using
        recent (90-day) demand. Recent demand is the early-1998 peak, so
        it gives the upper figure.
    """
    available = short["UnitsInStock"] + short["UnitsOnOrder"]
    longrun = (short["LongRunMonthlyDemand"] - available).clip(lower=0).sum()
    recent = (short["RecentMonthlyDemand"] - available).clip(lower=0).sum()
    return float(min(longrun, recent)), float(max(longrun, recent))


def q2_interpretation(q2, config):
    """Turn the Q2 results into business implications.

    Args:
        q2 (northwind.q2_inventory.Q2Result): Q2 results.
        config (northwind.config.Config): Settings.

    Returns:
        list[str]: Interpretation bullets (plain text).
    """
    watch, short = q2.watch_list, q2.shortlist
    shortfall = (short["RecentMonthlyDemand"] - short["UnitsInStock"] - short["UnitsOnOrder"]).clip(lower=0).sum()
    no_rule = q2.no_reorder_rule
    urgent_no_rule = int(no_rule["Tier"].isin(["Critical", "High"]).sum())
    backorders = int(watch["FlagPossibleShortage"].sum())
    trend = watch["DemandTrendRatio"].median()
    return [
        f"This is a replenishment problem across the catalogue, not a few exceptions: recent demand runs "
        f"{pct(trend - 1)} above each product's long-run rate (median), and reorder levels haven't kept up. "
        "Reorder levels would need to rise, not just this round of orders.",
        f"The top {len(short)} products need roughly {num(shortfall_range(short)[0])}–{num(shortfall_range(short)[1])} "
        "more units to cover one month of demand: the lower figure uses long-run demand, the higher uses the last "
        "90 days, which is the early-1998 peak. Purchasing could size these orders between the two.",
        f"{len(no_rule)} active products have no reorder level at all ({urgent_no_rule} of them Critical or High). "
        "Setting one, using the suggested levels in the appendix, prevents these from being missed again.",
        f"{backorders} products have more units on unshipped orders than in stock. These are possible "
        "shortages, not confirmed backorders: the orders may be unshipped for other reasons, and stock on "
        "order may arrive in time. Purchasing could check them before customers are told anything.",
        f"{len(q2.discontinued_stock)} discontinued products still hold about "
        f"{money(q2.discontinued_stock['StockValue'].sum())} of stock that could be sold off.",
    ]


def wilson(k, n, z=1.96):
    """Return the Wilson 95% interval for a proportion.

    Args:
        k (int): Successes.
        n (int): Trials.
        z (float): Normal quantile.

    Returns:
        tuple[float, float]: Lower and upper bounds.
    """
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / (1 + z * z / n)
    return centre - half, centre + half


def q3_facts(q3):
    """Collect the Q3 figures the page text is built from.

    Wording follows the independent review: typical times are given as a
    range, the slow-tail share of late orders is not used (it is close
    to automatic for 28-day orders), carrier differences are described
    as more very slow orders, and freight comparisons as inconclusive.

    Args:
        q3 (northwind.q3_logistics.Q3Result): Q3 results.

    Returns:
        dict: Figures and phrases for the Q3 text.
    """
    d, o = q3.deadlines, q3.overview
    late = q3.late_by_window.set_index("AllowedDays")
    short = d["ShortestWindow"]
    common = int(q3.late_by_window.sort_values("Orders").iloc[-1]["AllowedDays"])
    medians = pd.concat([q3.breakdowns[k]["MedianDays"] for k in ("Carrier", "Destination", "SizeBand")])
    low, high = wilson(int(late.loc[short, "LateOrders"]), int(late.loc[short, "Orders"]))
    slow = q3.slow_share_by_carrier or {}
    best = min(slow, key=slow.get) if slow else None
    worse = sorted((c for c in slow if c != best), key=slow.get, reverse=True)
    reg = q3.regression
    freight = reg[reg["Model"] == "Freight"] if not reg.empty else reg
    no_slow = q3.regression_without_slow
    gap_survives = bool(no_slow is not None and not no_slow.empty
                        and no_slow.loc[no_slow["Model"] == "Dispatch", "Material"].any())
    return {
        "short": short, "common": common,
        "median_low": medians.min(), "median_high": medians.max(),
        "median_short": d["MedianDaysByWindow"][short], "median_common": d["MedianDaysByWindow"][common],
        "late_short": late.loc[short, "LateShare"], "late_common": late.loc[common, "LateShare"],
        "late_short_n": int(late.loc[short, "LateOrders"]), "late_total": o["LateOrders"],
        "late_low": low, "late_high": high,
        "slow": slow, "best": best, "worse": worse, "gap_survives": gap_survives,
        "freight_material": bool((not freight.empty) and freight["Material"].any()),
        "freight_range": ((freight["Low95"].min(), freight["High95"].max()) if not freight.empty else None),
        "slow_cutoff": o["SlowCutoffDays"], "slow_orders": o["SlowOrders"],
    }


def q3_interpretation(q3):
    """Turn the Q3 results into business implications.

    Args:
        q3 (northwind.q3_logistics.Q3Result): Q3 results.

    Returns:
        list[str]: Interpretation bullets (plain text).
    """
    f, b = q3_facts(q3), q3.backlog
    out = [
        f"Typical dispatch takes {f['median_low']:.0f}–{f['median_high']:.0f} days for every carrier, region and "
        f"order size. The problem is a small number of very slow orders ({f['slow_orders']} took more than "
        f"{f['slow_cutoff']:.0f} days), not slow processing in general.",
        f"Orders with a {f['short']}-day deadline are not processed any faster (median {f['median_short']:g} days, "
        f"against {f['median_common']:g} for {f['common']}-day orders), so {pct(f['late_short'])} of them go out late "
        f"(likely range {pct(f['late_low'])}–{pct(f['late_high'])}; {f['late_short_n']} of the {f['late_total']} "
        "late dispatches). Sorting the dispatch queue by required date is a low-cost change aimed at these.",
    ]
    if f["worse"]:
        out.append(
            f"{join_names(f['worse'])} shipments are more often among the very slow orders "
            f"({join_names([pct(f['slow'][c]) for c in f['worse']])} of their orders, against "
            f"{pct(f['slow'][f['best']])} for {f['best']}). "
            + ("Their typical dispatch time is the same once those orders are set aside. "
               if not f["gap_survives"] else "")
            + "The data doesn't show why: it could be pickup schedules or which orders are assigned to which carrier.")
    procs = q3.opportunities[(q3.opportunities["Type"] == "Processing")
                             & (q3.opportunities["Dimension"] == "Employee")].head(2)
    if not procs.empty:
        emp = q3.breakdowns["Employee"].sort_values("SlowShare", ascending=False).iloc[0]
        out.append(f"Among employees, orders handled by {join_names(procs['Group'].tolist())} add the most lost "
                   f"order-days (they handle many orders), and {emp['EmployeeName']}'s orders are most often slow "
                   f"({pct(emp['SlowShare'])} of them). A look at how those orders reach the warehouse could help.")
    out.append(f"{b['Orders']} orders ({money(b['RevenueHeld'])}) placed in the last four weeks hadn't shipped by "
               "the cutoff; none is past its required date, so this looks like normal work in progress.")
    if not f["freight_material"]:
        lo, hi = f["freight_range"] if f["freight_range"] else (float("nan"), float("nan"))
        out.append("Carrier freight comparisons are inconclusive once order size and destination are taken into "
                   f"account (differences anywhere from {pct(lo, True)} to {pct(hi, True)}), so this data doesn't "
                   "support renegotiating or switching carriers on cost.")
    return out


def q1_flag_text(row):
    """Return short flag labels for one Q1 market.

    Args:
        row (pandas.Series): Scorecard row.

    Returns:
        list[str]: Flag labels.
    """
    out = []
    if row["FlagNearConcentrationLine"]:
        out.append("near 50% line")
    if row["FlagNarrowGrowth"]:
        out.append("narrow growth")
    if row.get("FlagNotConclusive", False):
        out.append("not conclusive")
    return out


def q2_section(q2, charts, config):
    """Build the Q2 section context.

    Args:
        q2 (northwind.q2_inventory.Q2Result): Q2 results.
        charts (dict[str, str]): Rendered charts.
        config (northwind.config.Config): Settings.

    Returns:
        dict: Template context for Q2.
    """
    short = q2.shortlist
    shortfall = (short["RecentMonthlyDemand"] - short["UnitsInStock"] - short["UnitsOnOrder"]).clip(lower=0).sum()
    order_now = short.loc[short["Action"] == "Order now", "ProductName"].head(3).tolist()
    answer = (f"{q2.headline} Purchasing could start with {join_names(order_now)}. "
              f"{int(short['FlagPossibleShortage'].sum())} of the top {len(short)} have more units on unshipped "
              "orders than in stock: possible shortages to verify.")
    return {
        "answer": answer,
        "main_chart": charts["q2_main"],
        "support_chart": charts["q2_support"],
        "table": table(short, [
            ("#", "Rank", None, True),
            ("Product", "ProductName", None, False),
            ("Tier", "Tier", None, False),
            ("In stock", "UnitsInStock", num, True),
            ("On order", "UnitsOnOrder", num, True),
            ("Demand / month", "RecentMonthlyDemand", num, True),
            ("Months on hand", "CoverOnHand", lambda v: num(v, 2), True),
            ("At stake / month", "RevenueAtRisk", money, True),
            ("Possible shortage (verify)", "FlagPossibleShortage", lambda v: "Yes" if v else "—", False),
            ("Suggested action", "Action", None, False),
        ]),
        "caveat": q2.caveat,
        "tier_counts": q2.tier_counts,
        "interpretation": q2_interpretation(q2, config),
        "key": q2.headline.split(" The top")[0][:-1] + ", assuming the undated stock count reflects 6 May 1998.",
        "meaning": (f"Recent demand runs {pct(q2.watch_list['DemandTrendRatio'].median() - 1)} above long-run "
                    "rates (median product) and reorder levels haven't kept up: this is a catalogue-wide "
                    "replenishment gap, not a few exceptions."),
        "actions": [
            {"text": f"Order the top {config.buy_list_size} products this week, in the quantities "
                     "listed below the chart", "status": "Confirmed"},
            {"text": f"Set reorder levels for the {len(q2.no_reorder_rule)} active products "
                     "without one, using the suggested levels in the appendix", "status": "Confirmed"},
            {"text": f"Check the {int(q2.watch_list['FlagPossibleShortage'].sum())} products where "
                     "unshipped orders exceed stock, starting with "
                     + join_names(q2.watch_list.loc[q2.watch_list["FlagPossibleShortage"], "ProductName"]
                                  .head(2).tolist()),
             "status": "To verify"},
        ],
        "buy_list": table(buy_list(short, config.buy_list_size), [
            ("#", "Rank", None, True),
            ("Product", "ProductName", None, False),
            ("In stock", "UnitsInStock", num, True),
            ("On order", "UnitsOnOrder", num, True),
            ("Sold per month (recent)", "RecentMonthlyDemand", num, True),
            ("Order now (units)", "OrderRange", None, True),
            ("Revenue at stake / month", "RevenueAtRisk", money, True),
        ]),
    }


def buy_list(short, size):
    """Return the top products with how many units to order.

    The order range runs from the units needed to cover one month at
    long-run demand to the units needed at recent (peak) demand.

    Args:
        short (pandas.DataFrame): Q2 shortlist, in rank order.
        size (int): Number of products to list.

    Returns:
        pandas.DataFrame: Top rows with an OrderRange column.
    """
    top = short.head(size).copy()
    available = top["UnitsInStock"] + top["UnitsOnOrder"]
    low = (top["LongRunMonthlyDemand"] - available).clip(lower=0).apply(math.ceil)
    high = (top["RecentMonthlyDemand"] - available).clip(lower=0).apply(math.ceil)
    top["OrderRange"] = [f"{min(a, b):,}–{max(a, b):,}" if a != b else f"{a:,}"
                         for a, b in zip(low, high)]
    return top


def q3_actions(q3, f):
    """Write the Q3 actions, each naming what to look at first.

    Args:
        q3 (northwind.q3_logistics.Q3Result): Q3 results.
        f (dict): Output of ``q3_facts``.

    Returns:
        list[dict]: Actions with text and status.
    """
    out = [{"text": "Sort the daily dispatch queue by required date, so "
                    f"{f['short']}-day orders go first", "status": "Confirmed"}]
    if f["worse"]:
        carriers = q3.breakdowns["Carrier"].set_index("ShipperName")
        first = f["worse"][0]
        n = int(carriers.loc[first, "SlowOrders"])
        out.append({"text": f"Pull the {n} {first} orders that waited over {f['slow_cutoff']:.0f} days "
                            "and compare when each was ready with when it was collected",
                    "status": "To verify"})
    return out


def q3_section(q3, charts):
    """Build the Q3 section context.

    Args:
        q3 (northwind.q3_logistics.Q3Result): Q3 results.
        charts (dict[str, str]): Rendered charts.

    Returns:
        dict: Template context for Q3.
    """
    o, b = q3.overview, q3.backlog
    f = q3_facts(q3)
    answer = None  # set below from the key finding
    opps = q3.opportunities
    shown = pd.concat([opps[opps["Type"] == "Processing"].head(6), opps[opps["Type"] == "Freight"]])
    shown = shown.assign(
        SizeText=[f"{num(s)} order-days" if t == "Processing" else f"{money(s)} (raw gap)"
                  for t, s in zip(shown["Type"], shown["Size"])],
        PerOrderText=[f"{p:.1f} days" if t == "Processing" else f"${p:.2f}"
                      for t, p in zip(shown["Type"], shown["SizePerOrder"])])
    section = {
        "answer": answer,
        "main_chart": charts["q3_main"],
        "support_chart": charts["q3_support"],
        "table": table(shown, [
            ("Type", "Type", None, False),
            ("Group", "Group", None, False),
            ("By", "Dimension", lambda v: v.lower(), False),
            ("Size", "SizeText", None, True),
            ("Orders", "Orders", num, True),
            ("Per order", "PerOrderText", None, True),
            ("Confidence", "Confidence", None, False),
            ("Suggested action", "Action", None, False),
        ]),
        "caveat": q3.caveat,
        "backlog": b,
        "overview": o,
        "interpretation": q3_interpretation(q3),
        "key": (f"Dispatch takes {f['median_low']:.0f}–{f['median_high']:.0f} days for nearly every order. "
                f"{f['short']}-day orders are not processed any faster, so {pct(f['late_short'])} of them go out late "
                f"(likely range {pct(f['late_low'])}–{pct(f['late_high'])}), against {pct(f['late_common'])} for "
                f"{f['common']}-day orders."),
        "meaning": ("The problem is a small number of very slow orders in Northwind's own dispatch process"
                    + (f", which are more common for {join_names(f['worse'])} shipments" if f["worse"] else "")
                    + ". " + ("Carrier freight comparisons are inconclusive after adjusting for order size and "
                              "destination, so the data doesn't support changing carriers on cost."
                              if not f["freight_material"]
                              else "Some carrier freight differences remain after adjustment.")),
        "actions": q3_actions(q3, f),
    }
    section["answer"] = section["meaning"]
    return section


# --- Appendix -----------------------------------------------------------------

def _regression_text(regression):
    """Add formatted effect and interval columns to the regression table.

    Args:
        regression (pandas.DataFrame): Q3 regression table.

    Returns:
        pandas.DataFrame: Copy with EffectText and IntervalText.
    """
    def fmt(model, value):
        """Format a regression effect in its model's unit.

        Args:
            model (str): "Freight" (percent) or "Dispatch" (days).
            value (float): Effect or interval bound.

        Returns:
            str: Formatted value.
        """
        return pct(value, True, 1) if model == "Freight" else f"{value:+.1f} days".replace("-", "−")

    out = regression.copy()
    out["EffectText"] = [fmt(m, v) for m, v in zip(out["Model"], out["Effect"])]
    out["IntervalText"] = [f"{fmt(m, lo)} to {fmt(m, hi)}"
                           for m, lo, hi in zip(out["Model"], out["Low95"], out["High95"])]
    return out

def appendix(q1, q2, q3, charts, checks):
    """Build the appendix context.

    Args:
        q1 (northwind.q1_markets.Q1Result): Q1 results.
        q2 (northwind.q2_inventory.Q2Result): Q2 results.
        q3 (northwind.q3_logistics.Q3Result): Q3 results.
        charts (dict[str, str]): Rendered charts.
        checks (list[dict]): SQL cross-check results.

    Returns:
        dict: Template context for the appendix and verification.
    """
    section = {}
    for r in checks:
        key = r["check"].split(" ")[0] if r["check"].startswith(("Q1", "Q2", "Q3")) else "Totals"
        s = section.setdefault(key, [0, 0])
        s[0] += bool(r["pass"])
        s[1] += 1
    reorder_cols = [c for c in q2.no_reorder_rule.columns if c.startswith("SuggestedReorder_")]
    q3b = q3.breakdowns
    breakdown_cols = lambda key: [  # noqa: E731
        (key, key, str, False), ("Orders", "Orders", num, True),
        ("Median days", "MedianDays", lambda v: num(v, 1), True),
        ("Mean days", "MeanDays", lambda v: num(v, 1), True),
        ("90th pct days", "P90Days", lambda v: num(v, 1), True),
        ("Slow share", "SlowShare", pct, True), ("Late", "LateOrders", num, True),
        ("Freight / unit (median)", "MedianFreightPerUnit", lambda v: f"${v:.2f}", True),
        ("Total freight", "TotalFreight", money, True)]
    return {
        "q1_quarterly_chart": charts["appendix_q1_quarterly"],
        "q1_uncertainty": table(q1.uncertainty, [
            ("Market", "Market", None, False),
            ("Relative growth", "RelativeGrowth", lambda v: pct(v, True), True),
            ("90% interval low", "Low", lambda v: pct(v, True), True),
            ("90% interval high", "High", lambda v: pct(v, True), True),
            ("Crosses a threshold", "CrossesThreshold", lambda v: "Yes" if v else "No", False)]),
        "q1_robustness": table(q1.robustness, [
            ("Market", "Market", None, False), ("Base", "Base", None, False),
            ("Ship-to country", "ShipTo", None, False), ("Latest quarter only", "LatestQuarter", None, False),
            ("Largest customer removed", "NoTopCustomer", None, False),
            ("Holds (≥2 of 3)", "Holds", lambda v: "Yes" if v else "No", False)]),
        "q1_windows": table(q1.windows, [("Market", "Market", None, False)]
                            + [(c, c, lambda v: pct(v, True), True) for c in q1.windows.columns
                               if c not in ("Market", "SameDirection")]
                            + [("Same direction in all three", "SameDirection",
                                lambda v: "Yes" if v else "No", False)]),
        "q1_window_growth": {k: pct(v, True) for k, v in (q1.window_growth or {}).items()},
        "q3_regression_without_slow": table(_regression_text(q3.regression_without_slow), [
            ("Model", "Model", None, False), ("Carrier", "Carrier", None, False),
            ("Compared with", "Baseline", None, False), ("Effect", "EffectText", None, True),
            ("95% interval", "IntervalText", None, True),
            ("Material", "Material", lambda v: "Yes" if v else "No", False)])
        if q3.regression_without_slow is not None and not q3.regression_without_slow.empty else None,
        "q1_movers": table(q1.movers, [
            ("Market", "Market", None, False), ("Customer", "CustomerName", None, False),
            ("Before", "RevenuePrior", money, True), ("After", "RevenueCurrent", money, True),
            ("Change", "Change", money, True)]),
        "q2_watch": table(q2.watch_list, [
            ("#", "Rank", None, True), ("Product", "ProductName", None, False),
            ("Category", "CategoryName", None, False), ("Tier", "Tier", None, False),
            ("In stock", "UnitsInStock", num, True), ("On order", "UnitsOnOrder", num, True),
            ("Reorder level", "ReorderLevel", num, True),
            ("Demand / month", "RecentMonthlyDemand", lambda v: num(v, 1), True),
            ("Months on hand", "CoverOnHand", lambda v: num(v, 2), True),
            ("Months incl. on order", "CoverWithOrders", lambda v: num(v, 2), True),
            ("At stake / month", "RevenueAtRisk", money, True), ("Action", "Action", None, False)]),
        "q2_no_rule": table(q2.no_reorder_rule, [
            ("#", "Rank", None, True), ("Product", "ProductName", None, False), ("Tier", "Tier", None, False),
            ("Demand / month", "RecentMonthlyDemand", lambda v: num(v, 1), True)]
            + [(f"Suggested level ({c.split('_')[1].replace('m', ' month lead time')})", c, num, True)
               for c in reorder_cols]),
        "q2_discontinued": table(q2.discontinued_stock, [
            ("Product", "ProductName", None, False), ("In stock", "UnitsInStock", num, True),
            ("Stock value (recent prices)", "StockValue", money, True)]),
        "q2_robustness": table(q2.robustness, [
            ("Demand window", "WindowDays", lambda v: f"{v} days", True),
            ("Critical/High in base", "BaseCriticalHigh", num, True),
            ("Still Critical/High", "StillCriticalHigh", num, True), ("Share", "Share", pct, True),
            ("Holds (≥80%)", "Holds", lambda v: "Yes" if v else "No", False),
            ("Products that moved", "Moved", lambda v: v or "—", False)]),
        "q3_carriers_chart": charts["appendix_q3_carriers"],
        "q3_breakdowns": {
            "Carrier": table(q3b["Carrier"], breakdown_cols("ShipperName")),
            "Employee": table(q3b["Employee"], breakdown_cols("EmployeeName")),
            "Destination": table(q3b["Destination"], breakdown_cols("DestRegion")),
            "Order size": table(q3b["SizeBand"], breakdown_cols("SizeBand")),
        },
        "q3_regression_reason": q3.regression_reason,
        "q3_regression": table(_regression_text(q3.regression), [
            ("Model", "Model", None, False), ("Carrier", "Carrier", None, False),
            ("Compared with", "Baseline", None, False), ("Effect", "EffectText", None, True),
            ("95% interval", "IntervalText", None, True),
            ("Material", "Material", lambda v: "Yes" if v else "No", False)])
        if not q3.regression.empty else None,
        "q3_robustness": table(q3.robustness, [
            ("Alternative", "Alternative", None, False), ("Type", "Type", None, False),
            ("Base top 3", "BaseTop3", num, True), ("Still in top 5", "StillInTop5", num, True),
            ("Holds", "Holds", lambda v: "Yes" if v else "No", False)]),
        "q3_consolidation": q3.consolidation,
        "checks_total": (sum(v[0] for v in section.values()), sum(v[1] for v in section.values())),
        "checks_by_section": section,
        "review": load_review(),
    }


def load_review(path=None):
    """Read the independent review's objections and resolutions, if any.

    Args:
        path (pathlib.Path | None): JSON file; None uses
            verification/fresh_review.json.

    Returns:
        list[dict]: Items with claim, severity, objection and
        resolution; empty if the review hasn't been recorded.
    """
    path = path or ROOT / "verification" / "fresh_review.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


# --- Page ---------------------------------------------------------------------

def summary_cards(q1, q2, q3, s1, s2, s3, config):
    """Build the summary cards and the ranked management priorities.

    Each card has one large metric, one finding and one action, taken
    from its section so the two can't disagree. Priorities are ranked by
    how certain the evidence is, how much money is at stake each month
    and how quickly the step can be taken.

    Args:
        q1 (northwind.q1_markets.Q1Result): Q1 results.
        q2 (northwind.q2_inventory.Q2Result): Q2 results.
        q3 (northwind.q3_logistics.Q3Result): Q3 results.
        s1 (dict): Q1 section context.
        s2 (dict): Q2 section context.
        s3 (dict): Q3 section context.
        config (northwind.config.Config): Settings.

    Returns:
        tuple[list[dict], list[dict]]: Summary cards and priorities.
    """
    watch, short = q2.watch_list, q2.shortlist
    urgent = int(watch["Tier"].isin(["Critical", "High"]).sum())
    thin = int((watch["CoverOnHand"] < config.high_cover).sum())
    f = q3_facts(q3)
    first_q1 = next(a for a in s1["actions"] if a["status"] == "Confirmed")
    top3 = join_names(short["ProductName"].head(3).tolist())
    cards = [
        {"label": "Markets", "anchor": "q1",
         "metric": pct(q1.company["Growth"], True), "metric_label": "revenue growth, year on year",
         "finding": (f"Only {join_names(s1['clear_gain'])} clearly gained share; "
                     f"{join_names(s1['clear_loss'])} clearly lost it."),
         "action": first_q1},
        {"label": "Stock", "anchor": "q2",
         "metric": f"{urgent} of {len(watch)}", "metric_label": "active products at critical or high stock risk",
         "finding": (f"Stock covers less than a month of recent demand for {thin} products "
                     "(assuming the undated stock count reflects 6 May 1998)."),
         "action": {"text": f"Order {top3} this week; quantities are under the stock chart",
                    "status": "Confirmed"}},
        {"label": "Logistics", "anchor": "q3",
         "metric": pct(f["late_short"]),
         "metric_label": f"of {f['short']}-day orders dispatched late, against {pct(f['late_common'])} "
                         f"of {f['common']}-day orders",
         "finding": (f"Short-deadline orders get no priority; typical dispatch takes "
                     f"{f['median_low']:.0f}–{f['median_high']:.0f} days everywhere."),
         "action": s3["actions"][0]},
    ]
    at_stake = short["RevenueAtRisk"].sum()
    days = max(1, round(short["CoverOnHand"].min() * config.days_per_month))
    confirmed = {a["market"] for a in s1["actions"] if a["status"] == "Confirmed"}
    losses = [loss for loss in s1["top_losses"] if loss[2] in confirmed]
    priorities = [
        {"rank": 1, "owner": "Purchasing", "status": "Confirmed",
         "title": f"Restock the top {len(short)} products",
         "why": (f"About {money(at_stake)} of sales a month depend on them, and the most urgent "
                 f"has roughly {days} days of stock left."),
         "next": f"Place orders for the top {config.buy_list_size} this week (quantities in question 2)."},
        {"rank": 2, "owner": "Operations", "status": "Confirmed",
         "title": "Put short-deadline orders first in the dispatch queue",
         "why": (f"{f['short']}-day orders go out late {pct(f['late_short'])} of the time, against "
                 f"{pct(f['late_common'])}, and the change costs almost nothing."),
         "next": (f"Sort the daily pick list by required date; check in a month that the "
                  f"{f['short']}-day late rate has fallen.")},
        {"rank": 3, "owner": "Sales", "status": "Confirmed",
         "title": "Win back the accounts behind the confirmed market losses",
         "why": (f"{join_names([n for n, _, _ in losses])} together bought "
                 f"{money(-sum(c for _, c, _ in losses))} less in the latest half-year than a year "
                 "earlier, in markets that lost share in every period compared."),
         "next": "Account managers call each of them this month to find out why orders fell."},
    ]
    return cards, priorities


def build_context(q1, q2, q3, charts, checks, config, input_sha256):
    """Assemble everything the template needs.

    Args:
        q1 (northwind.q1_markets.Q1Result): Q1 results.
        q2 (northwind.q2_inventory.Q2Result): Q2 results.
        q3 (northwind.q3_logistics.Q3Result): Q3 results.
        charts (dict[str, str]): Rendered charts.
        checks (list[dict]): SQL cross-check results.
        config (northwind.config.Config): Settings.
        input_sha256 (str): Fingerprint of the workbook.

    Returns:
        dict: Template context.
    """
    s1, s2, s3 = q1_section(q1, charts), q2_section(q2, charts, config), q3_section(q3, charts)
    summary, priorities = summary_cards(q1, q2, q3, s1, s2, s3, config)
    versions = {lib: importlib.metadata.version(lib) for lib in LIBRARIES}
    return {
        "title": "Northwind: markets, stock and logistics",
        "cutoff": config.cutoff.strftime("%d %B %Y").lstrip("0"),
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "input_sha256": input_sha256,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",  # patch version varies by machine
        "versions": versions,
        "repo_url": config.repo_url,
        "summary": summary,
        "priorities": priorities,
        "buy_list_size": config.buy_list_size,
        "q1": s1, "q2": s2, "q3": s3,
        "appendix": appendix(q1, q2, q3, charts, checks),
        "shortlist_size": config.shortlist_size,
        "tiers": metrics.TIER_ORDER,
    }


def render(context):
    """Render the report HTML.

    Args:
        context (dict): Output of ``build_context``.

    Returns:
        str: Complete HTML document.
    """
    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html", "j2"]), trim_blocks=True, lstrip_blocks=True)
    return env.get_template("report.html.j2").render(**context)


def write_site(page, docs_dir):
    """Write the page for GitHub Pages.

    Args:
        page (str): HTML document.
        docs_dir (pathlib.Path): Folder served by GitHub Pages.

    Returns:
        pathlib.Path: Path of the written index.html.
    """
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / ".nojekyll").write_text("", encoding="utf-8")
    out = docs_dir / "index.html"
    out.write_text(page, encoding="utf-8", newline="\n")
    return out
