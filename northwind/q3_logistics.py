"""Q3: how processing time and freight vary across shipments, and where
the biggest logistics improvements are (plan.md sections 3.5-3.7, 4)."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from northwind import metrics

DIMENSIONS = {"Carrier": "ShipperName", "Destination": "DestRegion", "Employee": "EmployeeName"}

ACTION_TEMPLATES = {
    ("Processing", "Carrier"): "Review pickup scheduling and dispatch hand-off for {g} shipments",
    ("Processing", "Destination"): "Review dispatch preparation for orders going to {g}",
    ("Processing", "Employee"): "Review how orders handled by {g} move from order to dispatch",
    ("Freight", "Carrier"): "Review {g}'s rates, or move comparable shipments to a cheaper carrier",
}

NO_ACTION = ("No action: the gap isn't clear once order size and destination are taken into account")

CAVEAT = (
    "Processing time ends when Northwind dispatches the order; delivery dates aren't in the "
    "data, so carrier delivery performance can't be judged. Freight is assumed to be a cost "
    "to Northwind. Opportunity sizes are gaps against the best comparable group in the same "
    "order-size band, not guaranteed savings."
)


@dataclass
class Q3Result:
    """Outputs of the Q3 logistics analysis.

    Attributes:
        overview (dict): Company-wide processing and freight figures.
        breakdowns (dict[str, pandas.DataFrame]): Processing and freight
            by carrier, destination, size band, employee and quarter.
        within_bands (dict[str, pandas.DataFrame]): Carrier and
            destination medians within each size band.
        opportunities (pandas.DataFrame): Processing and freight gaps,
            ranked within each type.
        backlog (dict): The unshipped orders.
        consolidation (dict): Small orders where freight is a large share
            of revenue.
        late_by_window (pandas.DataFrame): Late dispatches by the
            customer's allowed window.
        deadlines (dict): Whether short-deadline orders are prioritised.
        regression (pandas.DataFrame): Carrier effects after adjusting
            for size and destination; empty if not triggered.
        regression_reason (str | None): Why the regression ran.
        robustness (pandas.DataFrame): Top opportunities under
            alternative definitions (plan 8.3).
        regression_without_slow (pandas.DataFrame): The carrier
            regression with the slowest 10% of orders removed.
        slow_share_by_carrier (dict[str, float]): Share of each carrier's
            orders that are slow.
        caveat (str): Statement shown with the Q3 results.
    """

    overview: dict
    breakdowns: dict
    within_bands: dict
    opportunities: pd.DataFrame
    backlog: dict
    consolidation: dict
    late_by_window: pd.DataFrame
    deadlines: dict
    regression: pd.DataFrame
    regression_reason: str | None
    robustness: pd.DataFrame
    regression_without_slow: pd.DataFrame = None
    slow_share_by_carrier: dict = None
    caveat: str = CAVEAT


# --- Descriptive tables -----------------------------------------------------

def shipped_orders(model, config):
    """Return shipped orders with a slow-order flag.

    Args:
        model (northwind.model.Model): Joined tables.
        config (northwind.config.Config): Slow-order quantile.

    Returns:
        pandas.DataFrame: Shipped orders with IsSlow added.
    """
    shipped = model.orders[model.orders["IsShipped"]].copy()
    cutoff = shipped["ProcessingDays"].quantile(config.slow_quantile)
    shipped["IsSlow"] = shipped["ProcessingDays"] > cutoff
    return shipped


def breakdown(orders, col):
    """Summarise processing and freight for each value of one column.

    Args:
        orders (pandas.DataFrame): Shipped orders.
        col (str): Grouping column.

    Returns:
        pandas.DataFrame: Orders, processing median/mean/90th percentile,
        slow and late counts and shares, freight per unit and share
        medians, and total freight per group.
    """
    table = orders.groupby(col, observed=True).agg(
        Orders=("OrderID", "size"),
        MedianDays=("ProcessingDays", "median"),
        MeanDays=("ProcessingDays", "mean"),
        P90Days=("ProcessingDays", lambda x: x.quantile(0.9)),
        SlowOrders=("IsSlow", "sum"),
        LateOrders=("IsLate", "sum"),
        MedianFreightPerUnit=("FreightPerUnit", "median"),
        MedianFreightShare=("FreightShare", "median"),
        TotalFreight=("Freight", "sum"),
    )
    table["SlowShare"] = table["SlowOrders"] / table["Orders"]
    table["LateShare"] = table["LateOrders"] / table["Orders"]
    return table.reset_index()


def within_bands(orders, col, band_col="SizeBand"):
    """Return medians for each group within each size band.

    Args:
        orders (pandas.DataFrame): Shipped orders.
        col (str): Grouping column, e.g. ShipperName.
        band_col (str): Size band column.

    Returns:
        pandas.DataFrame: One row per band and group.
    """
    return orders.groupby([band_col, col], observed=True).agg(
        Orders=("OrderID", "size"),
        MedianDays=("ProcessingDays", "median"),
        MeanDays=("ProcessingDays", "mean"),
        MedianFreightPerUnit=("FreightPerUnit", "median"),
    ).reset_index()


# --- Opportunity sizing (plan 3.7) -------------------------------------------

def group_gaps(orders, col, value_col, config, band_col="SizeBand",
               weight_col=None, benchmark="best"):
    """Size each group's gap against a benchmark within each size band.

    For each band the benchmark level is the median of the best group
    (lowest median among groups with enough orders), or the median of
    all orders when ``benchmark="overall"``. Each order's excess is
    ``max(0, value - benchmark) * weight`` (plan 3.7). A group's
    opportunity is how much more excess per order it has than the
    benchmark reference, times its orders, summed over bands, so the
    best group itself scores zero.

    Args:
        orders (pandas.DataFrame): Shipped orders.
        col (str): Grouping column.
        value_col (str): Measure, e.g. ProcessingDays or FreightPerUnit.
        config (northwind.config.Config): Minimum orders per band.
        band_col (str): Size band column.
        weight_col (str | None): Multiplier per order, e.g. Units to
            turn freight per unit into dollars; None means 1.
        benchmark (str): "best" or "overall".

    Returns:
        pandas.DataFrame: Group, Orders, ExcessTotal, Opportunity,
        OpportunityPerOrder and Benchmarks (best group per band).

    Raises:
        ValueError: If ``benchmark`` is not recognised.
    """
    if benchmark not in ("best", "overall"):
        raise ValueError(f"Unknown benchmark: {benchmark}")
    rows = {}
    for band, frame in orders.groupby(band_col, observed=True):
        frame = frame.dropna(subset=[value_col])
        medians = frame.groupby(col)[value_col].agg(["median", "size"])
        eligible = medians[medians["size"] >= config.min_group_orders_per_band]
        if benchmark == "best" and not eligible.empty:
            best = eligible["median"].idxmin()
            level = eligible.loc[best, "median"]
        else:
            best, level = "all orders", frame[value_col].median()
        weight = frame[weight_col] if weight_col else 1.0
        excess = (frame[value_col] - level).clip(lower=0) * weight
        per_order = excess.groupby(frame[col]).mean()
        reference = per_order[best] if best in per_order.index else excess.mean()
        counts = frame.groupby(col).size()
        for group, n in counts.items():
            row = rows.setdefault(group, {"Orders": 0, "ExcessTotal": 0.0,
                                          "Opportunity": 0.0, "Benchmarks": []})
            row["Orders"] += int(n)
            row["ExcessTotal"] += float(excess[frame[col] == group].sum())
            row["Opportunity"] += float(n * max(0.0, per_order[group] - reference))
            row["Benchmarks"].append(f"{band}: {best}")
    table = pd.DataFrame.from_dict(rows, orient="index").rename_axis("Group").reset_index()
    table["OpportunityPerOrder"] = table["Opportunity"] / table["Orders"]
    table["Benchmarks"] = table["Benchmarks"].str.join("; ")
    return table.sort_values("Opportunity", ascending=False).reset_index(drop=True)


def opportunities(orders, config, band_col="SizeBand", benchmark="best"):
    """Collect processing and freight opportunities across dimensions.

    Args:
        orders (pandas.DataFrame): Shipped orders.
        config (northwind.config.Config): Settings.
        band_col (str): Size band column.
        benchmark (str): "best" or "overall" (see ``group_gaps``).

    Returns:
        pandas.DataFrame: One row per positive opportunity with Type
        (Processing in order-days, Freight in dollars), Dimension, Group,
        Size, Orders, SizePerOrder and Action; ranked within each Type.
    """
    specs = [("Processing", dim, col, "ProcessingDays", None) for dim, col in DIMENSIONS.items()]
    specs.append(("Freight", "Carrier", DIMENSIONS["Carrier"], "FreightPerUnit", "Units"))
    rows = []
    for kind, dim, col, value_col, weight_col in specs:
        gaps = group_gaps(orders, col, value_col, config, band_col, weight_col, benchmark)
        for _, g in gaps[gaps["Opportunity"] > 0].iterrows():
            rows.append({
                "Type": kind,
                "Unit": "order-days" if kind == "Processing" else "dollars",
                "Dimension": dim,
                "Group": g["Group"],
                "Key": f"{kind}|{dim}|{g['Group']}",
                "Size": g["Opportunity"],
                "Orders": g["Orders"],
                "SizePerOrder": g["OpportunityPerOrder"],
                "Benchmarks": g["Benchmarks"],
                "Action": ACTION_TEMPLATES[(kind, dim)].format(g=g["Group"]),
            })
    table = pd.DataFrame(rows)
    if table.empty:
        return table
    table = table.sort_values(["Type", "Size"], ascending=[True, False]).reset_index(drop=True)
    table["RankInType"] = table.groupby("Type").cumcount() + 1
    return table


# --- Fixed findings ----------------------------------------------------------

def backlog(model, config):
    """Summarise orders that were never shipped.

    Args:
        model (northwind.model.Model): Joined tables.
        config (northwind.config.Config): Cutoff.

    Returns:
        dict: Orders, revenue held, units, median and oldest age in days,
        and how many are already past their required date.
    """
    open_orders = model.orders[~model.orders["IsShipped"]]
    age = (config.cutoff - open_orders["OrderDate"]).dt.days
    overdue = (open_orders["RequiredDate"] < config.cutoff).sum()
    return {
        "Orders": int(len(open_orders)),
        "RevenueHeld": float(open_orders["NetRevenue"].sum()),
        "Units": int(open_orders["Units"].sum()),
        "MedianAgeDays": float(age.median()) if len(age) else float("nan"),
        "OldestAgeDays": int(age.max()) if len(age) else 0,
        "PastRequiredDate": int(overdue),
    }


def consolidation(orders, config):
    """Size the small-order consolidation opportunity (plan 3.7).

    Args:
        orders (pandas.DataFrame): Shipped orders.
        config (northwind.config.Config): Freight-share threshold.

    Returns:
        dict: Candidate orders, their freight, that freight's share of all
        freight, and whether it is material (at least 1% of freight).
    """
    small = orders[orders["SizeBand"] == metrics.SIZE_BAND_LABELS[0]]
    candidates = small[small["FreightShare"] > config.consolidation_share]
    freight = float(candidates["Freight"].sum())
    share = freight / float(orders["Freight"].sum())
    return {"Orders": int(len(candidates)), "Freight": freight,
            "ShareOfAllFreight": share, "Material": share >= 0.01}


def late_by_window(orders):
    """Count late dispatches by the customer's allowed window.

    Args:
        orders (pandas.DataFrame): Shipped orders.

    Returns:
        pandas.DataFrame: AllowedDays, Orders, LateOrders and LateShare.
    """
    table = orders.groupby("AllowedDays").agg(Orders=("OrderID", "size"),
                                              LateOrders=("IsLate", "sum")).reset_index()
    table["LateShare"] = table["LateOrders"] / table["Orders"]
    return table


# --- Plan 4.4: conditional regression ----------------------------------------

def region_mix_gap(orders):
    """Return the largest gap between carriers in any destination's share.

    Args:
        orders (pandas.DataFrame): Shipped orders.

    Returns:
        float: Largest absolute difference in destination share between
        any two carriers.
    """
    mix = pd.crosstab(orders["ShipperName"], orders["DestRegion"], normalize="index")
    return float((mix.max() - mix.min()).max())


def ols_hc1(y, X):
    """Fit ordinary least squares with HC1 robust standard errors.

    Args:
        y (numpy.ndarray): Outcome, shape (n,).
        X (pandas.DataFrame): Design matrix including the intercept.

    Returns:
        pandas.DataFrame: Estimate and StdError per column of ``X``.
    """
    x = X.to_numpy(dtype=float)
    n, k = x.shape
    xtx_inv = np.linalg.pinv(x.T @ x)
    beta = xtx_inv @ x.T @ y
    resid = y - x @ beta
    meat = x.T @ (x * resid[:, None] ** 2)
    cov = xtx_inv @ meat @ xtx_inv * n / (n - k)
    return pd.DataFrame({"Estimate": beta, "StdError": np.sqrt(np.diag(cov))}, index=X.columns)


def _design(orders, categorical, numeric, baselines):
    """Build a design matrix with an intercept and dummy variables.

    Args:
        orders (pandas.DataFrame): Shipped orders.
        categorical (list[str]): Columns to dummy-code.
        numeric (dict[str, pandas.Series]): Extra numeric columns.
        baselines (dict[str, str]): Reference level per categorical column.

    Returns:
        pandas.DataFrame: Design matrix.
    """
    parts = [pd.Series(1.0, index=orders.index, name="Intercept")]
    for name, series in numeric.items():
        parts.append(series.rename(name))
    for col in categorical:
        values = orders[col].astype(str)
        levels = sorted(values.unique())
        base = baselines.get(col, levels[0])
        for level in levels:
            if level != base:
                parts.append((values == level).astype(float).rename(f"{col}={level}"))
    return pd.concat(parts, axis=1)


def carrier_regression(orders, config):
    """Estimate carrier effects on freight and dispatch time (plan 4.4).

    Freight: log(Freight) on carrier, log(units), log(net revenue) and
    destination; baseline = the carrier with the lowest median freight
    per unit. Dispatch: processing days on carrier, size band,
    destination, employee and order quarter; baseline = the carrier with
    the lowest mean processing days. Each other carrier's effect is
    therefore its gap to the best carrier.

    Args:
        orders (pandas.DataFrame): Shipped orders.
        config (northwind.config.Config): Materiality thresholds.

    Returns:
        pandas.DataFrame: One row per model and carrier with the effect
        (percent for freight, days for dispatch), 95% interval and
        whether it is material.
    """
    data = orders[(orders["Freight"] > 0) & (orders["NetRevenue"] > 0)].copy()
    data["Quarter"] = data["Quarter"].astype(str)
    by_carrier = data.groupby("ShipperName")
    specs = {
        "Freight": (np.log(data["Freight"].to_numpy()), ["ShipperName", "DestRegion"],
                    {"log_units": np.log(data["Units"]), "log_revenue": np.log(data["NetRevenue"])},
                    by_carrier["FreightPerUnit"].median().idxmin()),
        "Dispatch": (data["ProcessingDays"].to_numpy(dtype=float),
                     ["ShipperName", "SizeBand", "DestRegion", "EmployeeName", "Quarter"], {},
                     by_carrier["ProcessingDays"].mean().idxmin()),
    }
    rows = []
    for model_name, (y, categorical, numeric, base) in specs.items():
        fit = ols_hc1(y, _design(data, categorical, numeric, {"ShipperName": base}))
        for term, est in fit.iterrows():
            if not term.startswith("ShipperName="):
                continue
            low, high = est["Estimate"] - 1.96 * est["StdError"], est["Estimate"] + 1.96 * est["StdError"]
            if model_name == "Freight":
                effect, low, high = np.expm1(est["Estimate"]), np.expm1(low), np.expm1(high)
                material = abs(effect) >= config.freight_materiality and (low > 0 or high < 0)
            else:
                effect = est["Estimate"]
                material = abs(effect) >= config.dispatch_materiality_days and (low > 0 or high < 0)
            rows.append({"Model": model_name, "Carrier": term.split("=", 1)[1], "Baseline": base,
                         "Effect": float(effect), "Low95": float(low), "High95": float(high),
                         "Unit": "% vs baseline" if model_name == "Freight" else "days vs baseline",
                         "Material": bool(material)})
    return pd.DataFrame(rows)


def apply_adjustment(opps, regression):
    """Mark carrier opportunities as supported or not by the regression.

    A carrier's opportunity is supported only if the regression finds a
    material gap between that carrier and the best carrier for the same
    measure (freight or dispatch). The best carrier itself has no gap.

    Args:
        opps (pandas.DataFrame): Opportunities with Confidence; modified
            in place.
        regression (pandas.DataFrame): Output of ``carrier_regression``.

    Returns:
        pandas.DataFrame: The same table with Confidence updated for
        carrier rows.
    """
    if regression.empty or opps.empty:
        return opps
    model_for = {"Freight": "Freight", "Processing": "Dispatch"}
    for i, row in opps[opps["Dimension"] == "Carrier"].iterrows():
        fit = regression[(regression["Model"] == model_for[row["Type"]])
                         & (regression["Carrier"] == row["Group"])]
        supported = (not fit.empty) and bool(fit["Material"].iloc[0]) and fit["Effect"].iloc[0] > 0
        opps.loc[i, "Confidence"] = ("Supported after adjustment" if supported
                                     else "Not supported after adjustment")
        if not supported:
            opps.loc[i, "Action"] = NO_ACTION
    return opps


def deadline_priority(orders):
    """Check whether short-deadline orders are processed faster.

    Args:
        orders (pandas.DataFrame): Shipped orders.

    Returns:
        dict: Median processing days per allowed window, whether the
        shortest-window orders are processed faster than the most common
        window, and the share of late orders that are slow orders.
    """
    medians = orders.groupby("AllowedDays")["ProcessingDays"].median()
    shortest = medians.index.min()
    common = orders["AllowedDays"].mode().iloc[0]
    late = orders[orders["IsLate"]]
    return {
        "MedianDaysByWindow": {int(k): float(v) for k, v in medians.items()},
        "ShortestWindow": int(shortest),
        "ShortWindowPrioritised": bool(medians[shortest] < medians[common]),
        "LateThatAreSlow": float(late["IsSlow"].mean()) if len(late) else float("nan"),
    }


def regression_trigger(orders, opps, config):
    """Decide whether the carrier regression is needed (plan 4.4).

    Args:
        orders (pandas.DataFrame): Shipped orders.
        opps (pandas.DataFrame): Output of ``opportunities``.
        config (northwind.config.Config): Region-mix tolerance.

    Returns:
        str | None: Reason, or None if the condition is not met.
    """
    carrier_gap = (not opps.empty) and (opps["Dimension"] == "Carrier").any()
    gap = region_mix_gap(orders)
    if carrier_gap and gap > config.region_mix_tolerance:
        return (f"carrier differences remain within size bands and carriers' destination "
                f"mix differs by up to {gap:.0%}")
    return None


# --- Plan 4.4: small-sample bootstrap -----------------------------------------

def flag_small_opportunities(opps, orders, config):
    """Add a confidence column; bootstrap opportunities on few orders.

    Args:
        opps (pandas.DataFrame): Output of ``opportunities``; modified in place.
        orders (pandas.DataFrame): Shipped orders.
        config (northwind.config.Config): Threshold, seed and resamples.

    Returns:
        pandas.DataFrame: The same table with Confidence added.
    """
    if opps.empty:
        opps["Confidence"] = []
        return opps
    confidence = []
    rng = np.random.default_rng(config.seed)
    for _, row in opps.iterrows():
        if row["Orders"] >= config.min_opportunity_orders:
            confidence.append("Clear")
            continue
        col = DIMENSIONS[row["Dimension"]]
        value_col, weight = (("ProcessingDays", None) if row["Type"] == "Processing"
                             else ("FreightPerUnit", "Units"))
        sizes = []
        for _ in range(200):
            sample = orders.iloc[rng.integers(0, len(orders), len(orders))]
            gaps = group_gaps(sample, col, value_col, config, weight_col=weight).set_index("Group")
            sizes.append(gaps["Opportunity"].get(row["Group"], 0.0))
        low = np.quantile(sizes, (1 - config.bootstrap_interval) / 2)
        confidence.append("Confirmed" if low > 0 else "Not conclusive")
    opps["Confidence"] = confidence
    return opps


# --- Plan 8.3: robustness ------------------------------------------------------

def robustness(orders, base, config):
    """Check whether the top 3 opportunities of each type stay in the top 5.

    Alternatives: size bands by revenue instead of units; the top 1% of
    freight values removed; benchmark = all orders in the band instead
    of the best group.

    Args:
        orders (pandas.DataFrame): Shipped orders.
        base (pandas.DataFrame): Base opportunities.
        config (northwind.config.Config): Settings.

    Returns:
        pandas.DataFrame: One row per alternative and type with how many
        of the base top 3 stay in the top 5, and whether that holds.
    """
    by_revenue = orders.copy()
    by_revenue["RevenueBand"] = metrics.assign_size_band(
        by_revenue["NetRevenue"], metrics.size_band_edges(by_revenue["NetRevenue"]))
    trimmed = orders[orders["Freight"] <= orders["Freight"].quantile(config.freight_outlier_quantile)]
    alternatives = {
        "Revenue size bands": opportunities(by_revenue, config, band_col="RevenueBand"),
        "Top 1% freight removed": opportunities(trimmed, config),
        "Benchmark = all orders": opportunities(orders, config, benchmark="overall"),
    }
    rows = []
    for name, alt in alternatives.items():
        for kind in ("Processing", "Freight"):
            top3 = base.loc[base["Type"] == kind].head(3)["Key"].tolist()
            top5 = alt.loc[alt["Type"] == kind].head(5)["Key"].tolist() if not alt.empty else []
            kept = sum(k in top5 for k in top3)
            rows.append({"Alternative": name, "Type": kind, "BaseTop3": len(top3),
                         "StillInTop5": kept, "Holds": kept == len(top3)})
    return pd.DataFrame(rows)


# --- Entry point -------------------------------------------------------------

def run(model, config):
    """Run the full Q3 analysis.

    Args:
        model (northwind.model.Model): Joined tables.
        config (northwind.config.Config): Settings.

    Returns:
        Q3Result: All Q3 tables and findings.
    """
    orders = shipped_orders(model, config)
    opps = flag_small_opportunities(opportunities(orders, config), orders, config)
    reason = regression_trigger(orders, opps, config)
    regression = carrier_regression(orders, config) if reason else pd.DataFrame()
    # Added after the independent review: does the carrier gap survive
    # without the slowest 10% of orders?
    without_slow = (carrier_regression(orders[~orders["IsSlow"]], config) if reason else pd.DataFrame())
    opps = apply_adjustment(opps, regression)
    overview = {
        "ShippedOrders": int(len(orders)),
        "MedianDays": float(orders["ProcessingDays"].median()),
        "MeanDays": float(orders["ProcessingDays"].mean()),
        "SlowCutoffDays": float(orders["ProcessingDays"].quantile(config.slow_quantile)),
        "SlowOrders": int(orders["IsSlow"].sum()),
        "LateOrders": int(orders["IsLate"].sum()),
        "TotalFreight": float(orders["Freight"].sum()),
        "MedianFreightShare": float(orders["FreightShare"].median()),
        "RegionMixGap": region_mix_gap(orders),
    }
    return Q3Result(
        overview=overview,
        breakdowns={name: breakdown(orders, col) for name, col in
                    {**DIMENSIONS, "SizeBand": "SizeBand", "Quarter": "Quarter"}.items()},
        within_bands={name: within_bands(orders, DIMENSIONS[name])
                      for name in ("Carrier", "Destination")},
        opportunities=opps,
        backlog=backlog(model, config),
        consolidation=consolidation(orders, config),
        late_by_window=late_by_window(orders),
        deadlines=deadline_priority(orders),
        regression=regression,
        regression_reason=reason,
        regression_without_slow=without_slow,
        slow_share_by_carrier=orders.groupby("ShipperName")["IsSlow"].mean().to_dict(),
        robustness=robustness(orders, opps, config),
    )
