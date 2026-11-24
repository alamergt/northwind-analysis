"""Charts for the report, rendered as themeable inline SVG.

Each chart is drawn with matplotlib in the light palette, then every
palette colour is swapped for a CSS variable so the same SVG follows the
page's light/dark theme. Colours follow the dataviz reference palette.
"""

import io
import re
from xml.sax.saxutils import escape

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

# Light value -> CSS variable. Light values must be unique; the page's CSS
# defines each variable for light and dark mode.
TOKENS = {
    "#fcfcfb": "--chart-surface",
    "#0b0b0b": "--ink",
    "#52514e": "--ink-2",
    "#898781": "--muted",
    "#e1e0d9": "--grid",
    "#c3c2b7": "--axis",
    "#efeee9": "--band",
    "#2a78d6": "--series-1",
    "#eb6834": "--series-2",
    "#1baf7a": "--series-3",
    "#e34948": "--negative",
    "#a9a8a1": "--neutral-mark",
}
C = {token.lstrip("-").replace("-", "_"): hex_ for hex_, token in TOKENS.items()}

# Scatter charts compare every pair of colours, so they use at most three
# (validated all-pairs in light and dark mode with the dataviz checks).
PERFORMANCE_COLORS = {"Outperforming": C["series_1"], "In line": C["neutral_mark"],
                      "Underperforming": C["negative"]}
# Q2 tiers: four tiers would fail the all-pairs checks, so Watch and OK
# share the neutral colour; marker shape is a second cue for every tier.
TIER_STYLES = {
    "Critical": (["Critical"], C["negative"], "o", 52),
    "High": (["High"], C["series_1"], "D", 34),
    "Watch or OK": (["Watch", "OK"], C["neutral_mark"], "o", 26),
}
DIMENSION_COLORS = {"Carrier": C["series_1"], "Employee": C["series_2"],
                    "Destination": C["series_3"]}

WIDTH = 7.2  # inches; the SVG scales to its container

plt.rcParams.update({
    "svg.fonttype": "none",
    "svg.hashsalt": "northwind",
    "font.family": "sans-serif",
    "font.size": 9,
    "axes.edgecolor": C["axis"],
    "axes.labelcolor": C["ink_2"],
    "axes.titlecolor": C["ink"],
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "xtick.color": C["muted"],
    "ytick.color": C["muted"],
    "xtick.labelcolor": C["ink_2"],
    "ytick.labelcolor": C["ink_2"],
    "axes.grid": False,
    "grid.color": C["grid"],
    "grid.linewidth": 0.75,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": C["chart_surface"],
    "axes.facecolor": C["chart_surface"],
    "legend.frameon": False,
    "legend.labelcolor": C["ink_2"],
    "text.color": C["ink"],
    "lines.solid_capstyle": "round",
})


def _money(value):
    """Format dollars compactly.

    Args:
        value (float): Amount in dollars.

    Returns:
        str: e.g. "$40.1K" or "$950".
    """
    sign = "−" if value < 0 else ""
    value = abs(value)
    return f"{sign}${value / 1000:,.1f}K" if value >= 1000 else f"{sign}${value:,.0f}"


def to_svg(fig, alt):
    """Render a figure as themeable, accessible inline SVG.

    Args:
        fig (matplotlib.figure.Figure): Figure to render; closed after.
        alt (str): Text alternative describing the chart's message.

    Returns:
        str: SVG markup with palette colours replaced by CSS variables,
        fixed metadata, and a role, label and title for screen readers.
    """
    buffer = io.StringIO()
    fig.savefig(buffer, format="svg", metadata={"Date": None, "Creator": None})
    plt.close(fig)
    svg = buffer.getvalue()
    svg = svg[svg.index("<svg"):]
    for hex_, token in TOKENS.items():
        svg = re.sub(re.escape(hex_), f"var({token})", svg, flags=re.IGNORECASE)
    svg = re.sub(r"font-family:[^;\"]*", "font-family: var(--font-sans)", svg)
    svg = re.sub(r"font: ([\d.]+)px '[^']*'", r"font: \1px var(--font-sans)", svg)
    svg = re.sub(r'(<svg[^>]*?) width="[^"]*" height="[^"]*"', r"\1", svg, count=1)
    svg = svg.replace("<svg ", f'<svg role="img" aria-label="{escape(alt, {chr(34): "&quot;"})}" ', 1)
    svg = re.sub(r"(<svg[^>]*>)", rf"\1<title>{escape(alt)}</title>", svg, count=1)
    return svg


def _hairline_grid(ax, axis="y"):
    """Draw recessive solid hairline gridlines behind the data.

    Args:
        ax (matplotlib.axes.Axes): Axes to style.
        axis (str): "x", "y" or "both".

    Returns:
        None.
    """
    ax.set_axisbelow(True)
    ax.grid(True, axis=axis, color=C["grid"], linewidth=0.75, linestyle="-")


# --- Q1 -----------------------------------------------------------------------

def q1_matrix(card, config):
    """Main Q1 chart: relative performance vs concentration, one bubble per market.

    Args:
        card (pandas.DataFrame): Q1 scorecard.
        config (northwind.config.Config): Thresholds.

    Returns:
        str: Inline SVG.
    """
    data = card[card["RecommendedAction"] != "Insufficient data"].copy()
    data["x"], data["y"] = data["RelativeGrowth"] * 100, data["Dependence"] * 100
    fig, ax = plt.subplots(figsize=(WIDTH, 4.6))
    xmin, xmax = min(-75, data["x"].min() - 10), max(95, data["x"].max() + 12)
    ymin, ymax = 20, max(65, data["y"].max() + 6)
    hi = config.concentration_threshold * 100
    margin = config.concentration_flag_margin * 100
    ax.axhspan(hi - margin, hi + margin, color=C["band"], zorder=0, linewidth=0)
    for x in (config.underperform_threshold * 100, config.outperform_threshold * 100):
        ax.axvline(x, color=C["axis"], linewidth=1, zorder=1)
    ax.axhline(hi, color=C["axis"], linewidth=1, zorder=1)
    ax.axvline(0, color=C["grid"], linewidth=0.75, zorder=0)

    # Region names = the recommended action for that area.
    lo_x, up_x = config.underperform_threshold * 100, config.outperform_threshold * 100
    regions = [((xmin + lo_x) / 2, "Rescue", "Diagnose"), ((lo_x + up_x) / 2, "Protect", "Maintain"),
               ((up_x + xmax) / 2, "Broaden", "Invest")]
    for x, top, bottom in regions:
        ax.text(x, ymax - 1.5, top, ha="center", va="top", color=C["muted"], fontsize=9, fontweight="bold")
        ax.text(x, ymin + 1.5, bottom, ha="center", va="bottom", color=C["muted"], fontsize=9, fontweight="bold")

    sizes = 60 + data["RevenueCurrent"] / data["RevenueCurrent"].max() * 900
    for level, color in PERFORMANCE_COLORS.items():
        part = data[data["Performance"] == level]
        ax.scatter(part["x"], part["y"], s=sizes[part.index], color=color, alpha=0.85,
                   edgecolors=C["chart_surface"], linewidths=2, zorder=3, label=level)

    placed = []
    for _, row in data.sort_values("x").iterrows():
        radius = np.sqrt(sizes[row.name]) / 2 + 3
        below = any(abs(row["x"] - px) < 14 and abs(row["y"] - py) < 5 and not pb
                    for px, py, pb in placed)
        offset = -radius if below else radius
        ax.annotate(row["Market"], (row["x"], row["y"]), xytext=(0, offset), textcoords="offset points",
                    ha="center", va="top" if below else "bottom", fontsize=8.5, color=C["ink"], zorder=4)
        placed.append((row["x"], row["y"], below))

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0f}%" if v else "0%"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlabel("Change in share of company revenue (relative to the company's growth)")
    ax.set_ylabel("Largest customer's share of the market")
    colour_legend = ax.legend(loc="upper center", bbox_to_anchor=(0.3, -0.14), ncol=3, fontsize=8.5,
                              markerscale=0.5, handletextpad=0.3, title="Colour: performance",
                              title_fontsize=8)
    ax.add_artist(colour_legend)
    top = data["RevenueCurrent"].max()
    refs = [v for v in (20_000, 50_000, 90_000) if v <= top * 1.05]
    size_handles = [ax.scatter([], [], s=60 + v / top * 900, color=C["neutral_mark"], alpha=0.5,
                               edgecolors=C["chart_surface"]) for v in refs]
    ax.legend(size_handles, [_money(v) for v in refs], loc="upper center", bbox_to_anchor=(0.82, -0.14),
              ncol=len(refs), fontsize=8.5, handletextpad=0.6, columnspacing=1.2,
              title="Size: revenue, Q4 1997 + Q1 1998", title_fontsize=8)
    fig.tight_layout()
    alt = ("Scatter chart of ten markets: change in share of company revenue against the largest "
           "customer's share of the market, divided into six areas named after the recommended actions. "
           + "; ".join(f"{r.Market}: {r.x:+.0f}% relative, largest customer {r.y:.0f}%, {r.RecommendedAction}"
                       for r in data.itertuples()))
    return to_svg(fig, alt)


def q1_movers(movers, card, config):
    """Supporting Q1 chart: biggest account gains and losses in each focus market.

    Args:
        movers (pandas.DataFrame): Q1 movers table.
        card (pandas.DataFrame): Q1 scorecard (for each market's action).
        config (northwind.config.Config): Focus markets.

    Returns:
        str: Inline SVG.
    """
    markets = [m for m in config.focus_markets if m in set(movers["Market"])]
    action = card.set_index("Market")["RecommendedAction"]
    fig, axes = plt.subplots(2, 2, figsize=(WIDTH, 5.4))
    limit = movers.loc[movers["Market"].isin(markets), "Change"].abs().max() * 1.45
    alt_parts = []
    for ax, market in zip(axes.flat, markets):
        m = movers[movers["Market"] == market].sort_values("Change")
        names = [n if len(n) <= 24 else n[:23] + "…" for n in m["CustomerName"]]
        colors = [C["series_1"] if v > 0 else C["negative"] for v in m["Change"]]
        y = np.arange(len(m))
        ax.barh(y, m["Change"], color=colors, height=0.6, zorder=2)
        ax.axvline(0, color=C["axis"], linewidth=1, zorder=3)
        for yi, v in zip(y, m["Change"]):
            ax.text(v + (limit * 0.03 if v >= 0 else -limit * 0.03), yi, ("+" if v > 0 else "") + _money(v),
                    va="center", ha="left" if v >= 0 else "right", fontsize=7.5, color=C["ink_2"])
        ax.set_yticks(y, names, fontsize=7.5)
        ax.tick_params(axis="y", length=0)
        ax.set_xlim(-limit, limit)
        ax.set_xticks([])
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.set_title(f"{market} · {action[market]}", fontsize=9)
        alt_parts.append(f"{market}: " + ", ".join(f"{n} {('+' if v > 0 else '')}{_money(v)}"
                                                  for n, v in zip(m["CustomerName"], m["Change"])))
    handles = [plt.Rectangle((0, 0), 1, 1, color=C["series_1"]), plt.Rectangle((0, 0), 1, 1, color=C["negative"])]
    fig.legend(handles, ["Revenue gained", "Revenue lost"], loc="lower center", ncol=2, fontsize=8.5,
               handlelength=1, handleheight=1, title="Change in account revenue, Q4 1996 + Q1 1997 → "
               "Q4 1997 + Q1 1998", title_fontsize=8)
    fig.tight_layout(h_pad=1.5, rect=(0, 0.08, 1, 1))
    return to_svg(fig, "Bar charts of the accounts whose revenue changed most in each focus market. "
                  + "; ".join(alt_parts))


def q1_quarterly(quarterly):
    """Appendix chart: each market's share of company revenue by quarter.

    Args:
        quarterly (pandas.DataFrame): Q1 quarterly table.

    Returns:
        str: Inline SVG.
    """
    data = quarterly[quarterly["IsComplete"]].copy()
    data["Q"] = data["Quarter"].astype(str)
    markets = sorted(data["Market"].unique())
    cols = 5
    rows = int(np.ceil(len(markets) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(WIDTH, 1.9 * rows), sharey=True)
    top = data["Share"].max() * 100 * 1.15
    quarters = sorted(data["Q"].unique())
    for ax, market in zip(axes.flat, markets):
        m = data[data["Market"] == market].set_index("Q").reindex(quarters)
        ax.plot(range(len(quarters)), m["Share"] * 100, color=C["series_1"], linewidth=2)
        ax.plot(len(quarters) - 1, m["Share"].iloc[-1] * 100, "o", color=C["series_1"],
                markersize=5, markeredgecolor=C["chart_surface"], markeredgewidth=1.5)
        ax.set_title(market, fontsize=8)
        ax.set_ylim(0, top)
        ax.set_xticks([0, len(quarters) - 1], [quarters[0], quarters[-1]], fontsize=7)
        ax.tick_params(axis="y", labelsize=7)
        _hairline_grid(ax)
    for ax in list(axes.flat)[len(markets):]:
        ax.axis("off")
    for ax in axes[:, 0]:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    fig.supylabel("Share of company revenue", fontsize=8.5, color=C["ink_2"])
    fig.supxlabel("Quarter", fontsize=8.5, color=C["ink_2"])
    fig.tight_layout()
    return to_svg(fig, "Small line charts of each market's share of company revenue per quarter, "
                  f"{quarters[0]} to {quarters[-1]}.")


# --- Q2 -----------------------------------------------------------------------

def q2_urgency(watch, shortlist_size):
    """Main Q2 chart: recent demand vs months of stock on hand, by tier.

    Args:
        watch (pandas.DataFrame): Ranked watch list.
        shortlist_size (int): How many top products get rank labels.

    Returns:
        str: Inline SVG.
    """
    data = watch[watch["Tier"].isin(["Critical", "High", "Watch", "OK"])].copy()
    floor = 0.03
    data["y"] = data["CoverOnHand"].clip(lower=floor)
    fig, ax = plt.subplots(figsize=(WIDTH, 4.4))
    ax.set_yscale("log")
    for level in (0.5, 1.0):
        ax.axhline(level, color=C["axis"], linewidth=1, zorder=1)
        ax.text(data["RecentMonthlyDemand"].max() * 1.02, level, f"{level:g} month", va="bottom",
                ha="right", fontsize=7.5, color=C["muted"])
    for label, (tiers, color, marker, size) in reversed(list(TIER_STYLES.items())):
        part = data[data["Tier"].isin(tiers)]
        ax.scatter(part["RecentMonthlyDemand"], part["y"], s=size, color=color, marker=marker,
                   edgecolors=C["chart_surface"], linewidths=1.5, zorder=3, label=f"{label} ({len(part)})")
    for _, row in data[data["Rank"] <= shortlist_size].iterrows():
        ax.annotate(str(row["Rank"]), (row["RecentMonthlyDemand"], row["y"]), xytext=(5, 3),
                    textcoords="offset points", fontsize=7.5, color=C["ink"], fontweight="bold", zorder=4)
    ax.set_ylim(floor * 0.8, max(data["y"].max() * 1.4, 10))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_yticks([0.05, 0.1, 0.5, 1, 2, 5, 10, 20])
    ax.set_xlabel("Recent demand (units per month, last 90 days)")
    ax.set_ylabel("Months of stock on hand (log scale)")
    _hairline_grid(ax, "both")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3,
              fontsize=8.5, handletextpad=0.2)
    fig.tight_layout()
    top = data[data["Rank"] <= shortlist_size]
    alt = (f"Scatter chart of {len(data)} active products: recent monthly demand against months of stock "
           f"on hand, coloured by tier. Top {shortlist_size}: "
           + "; ".join(f"{r.Rank}. {r.ProductName} ({r.Tier}, {r.CoverOnHand:.2f} months)"
                       for r in top.itertuples()))
    return to_svg(fig, alt)


def q2_gap(shortlist):
    """Supporting Q2 chart: units available vs one month of demand for the top products.

    The gap between the two dots is the least a purchase order would need
    to cover one month of recent demand.

    Args:
        shortlist (pandas.DataFrame): Top of the watch list.

    Returns:
        str: Inline SVG.
    """
    data = shortlist.iloc[::-1].copy()
    data["Available"] = data["UnitsInStock"] + data["UnitsOnOrder"]
    data["Gap"] = (data["RecentMonthlyDemand"] - data["Available"]).clip(lower=0)
    fig, ax = plt.subplots(figsize=(WIDTH, 0.38 * len(data) + 1.3))
    y = np.arange(len(data))
    ax.hlines(y, data["Available"], data["RecentMonthlyDemand"], color=C["grid"], linewidth=2, zorder=2)
    ax.scatter(data["Available"], y, s=60, color=C["series_2"], edgecolors=C["chart_surface"],
               linewidths=2, zorder=3, label="Units available (in stock + on order)")
    ax.scatter(data["RecentMonthlyDemand"], y, s=60, color=C["series_1"], edgecolors=C["chart_surface"],
               linewidths=2, zorder=4, label="One month of recent demand")
    right = max(data["RecentMonthlyDemand"].max(), data["Available"].max())
    for yi, (end, gap) in enumerate(zip(np.maximum(data["RecentMonthlyDemand"], data["Available"]), data["Gap"])):
        ax.text(end + right * 0.03, yi, f"short {gap:,.0f}" if gap > 0 else "covered", va="center",
                fontsize=7.5, color=C["ink_2"])
    labels = [f"{r} {n if len(n) <= 28 else n[:27] + '…'}" for r, n in zip(data["Rank"], data["ProductName"])]
    ax.set_yticks(y, labels, fontsize=8)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, right * 1.25)
    ax.set_xlabel("Units of product")
    _hairline_grid(ax, "x")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=8.5)
    fig.tight_layout()
    alt = ("Dot chart of the top products: units available against one month of recent demand. "
           + "; ".join(f"{r.ProductName}: {r.Available:,.0f} available, {r.RecentMonthlyDemand:,.0f} per month"
                       for r in data.iloc[::-1].itertuples()))
    return to_svg(fig, alt)


# --- Q3 -----------------------------------------------------------------------

def q3_opportunities(opps, top_n=8):
    """Supporting Q3 chart: where dispatch time is lost, by group.

    Freight gaps are not drawn: after adjustment they are not supported,
    so they appear only in the detailed table.

    Args:
        opps (pandas.DataFrame): Q3 opportunities table.
        top_n (int): Processing opportunities to show.

    Returns:
        str: Inline SVG.
    """
    proc = opps[opps["Type"] == "Processing"].head(top_n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(WIDTH, 0.36 * len(proc) + 1.4))
    y = np.arange(len(proc))
    ax.barh(y, proc["Size"], color=[DIMENSION_COLORS[d] for d in proc["Dimension"]], height=0.5, zorder=2)
    for yi, (size, per) in enumerate(zip(proc["Size"], proc["SizePerOrder"])):
        ax.text(size + proc["Size"].max() * 0.01, yi, f"{size:,.0f} order-days ({per:.1f} per order)",
                va="center", fontsize=7.5, color=C["ink_2"])
    ax.set_yticks(y, list(proc["Group"]), fontsize=8)
    ax.set_xlim(0, proc["Size"].max() * 1.5)
    ax.set_xlabel("Order-days lost against the best comparable group")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in DIMENSION_COLORS.values()]
    ax.legend(handles, [f"By {d.lower()}" for d in DIMENSION_COLORS], loc="lower right", fontsize=8,
              handlelength=1, handleheight=1)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    _hairline_grid(ax, "x")
    fig.tight_layout()
    alt = ("Bar chart of order-days lost to slow dispatch, by group: "
           + "; ".join(f"{r.Group} ({r.Dimension.lower()}) {r.Size:,.0f}" for r in proc.iloc[::-1].itertuples()))
    return to_svg(fig, alt)


def q3_deadlines(late_by_window):
    """Main Q3 chart: late-dispatch rate by the customer's allowed window.

    Args:
        late_by_window (pandas.DataFrame): Q3 late-by-window table.

    Returns:
        str: Inline SVG.
    """
    data = late_by_window.sort_values("AllowedDays")
    fig, ax = plt.subplots(figsize=(WIDTH, 2.8))
    x = np.arange(len(data))
    ax.bar(x, data["LateShare"] * 100, color=C["series_1"], width=0.3, zorder=2)
    for xi, (share, late, n) in enumerate(zip(data["LateShare"], data["LateOrders"], data["Orders"])):
        ax.text(xi, share * 100 + 0.6, f"{share:.0%}  ({late:.0f} of {n})", ha="center", va="bottom",
                fontsize=8, color=C["ink_2"])
    ax.set_xticks(x, [f"{d:.0f}-day window" for d in data["AllowedDays"]])
    ax.set_xlabel("Time the customer allowed between order and required date")
    ax.tick_params(axis="x", length=0)
    ax.set_ylim(0, max(data["LateShare"].max() * 100 * 1.3, 5))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_ylabel("Orders dispatched late (%)")
    _hairline_grid(ax)
    fig.tight_layout()
    alt = "Column chart of the share of orders dispatched late by allowed window: " + "; ".join(
        f"{d:.0f} days {s:.0%} ({lo:.0f} of {n})" for d, s, lo, n in
        zip(data["AllowedDays"], data["LateShare"], data["LateOrders"], data["Orders"]))
    return to_svg(fig, alt)


def q3_processing_by_carrier(orders):
    """Appendix chart: distribution of processing days by carrier.

    Args:
        orders (pandas.DataFrame): Shipped orders.

    Returns:
        str: Inline SVG.
    """
    carriers = sorted(orders["ShipperName"].unique())
    fig, ax = plt.subplots(figsize=(WIDTH, 2.6))
    values = [orders.loc[orders["ShipperName"] == c, "ProcessingDays"].dropna() for c in carriers]
    box = ax.boxplot(values, orientation="horizontal", widths=0.45, patch_artist=True,
                     medianprops={"color": C["ink"], "linewidth": 2},
                     whiskerprops={"color": C["axis"]}, capprops={"color": C["axis"]},
                     flierprops={"marker": "o", "markersize": 3, "markerfacecolor": C["muted"],
                                 "markeredgecolor": C["muted"]})
    for patch in box["boxes"]:
        patch.set(facecolor=C["band"], edgecolor=C["axis"])
    ax.set_yticks(range(1, len(carriers) + 1), carriers)
    ax.set_xlabel("Days from order to dispatch")
    _hairline_grid(ax, "x")
    fig.tight_layout()
    return to_svg(fig, "Box plots of days from order to dispatch for each carrier: " + "; ".join(
        f"{c} median {v.median():.0f}, 90th percentile {v.quantile(0.9):.0f}" for c, v in zip(carriers, values)))


def all_charts(q1, q2, q3, orders, config):
    """Render every chart used on the page.

    Args:
        q1 (northwind.q1_markets.Q1Result): Q1 results.
        q2 (northwind.q2_inventory.Q2Result): Q2 results.
        q3 (northwind.q3_logistics.Q3Result): Q3 results.
        orders (pandas.DataFrame): Shipped orders for the appendix chart.
        config (northwind.config.Config): Settings.

    Returns:
        dict[str, str]: SVG markup keyed by chart name.
    """
    return {
        "q1_main": q1_matrix(q1.scorecard, config),
        "q1_support": q1_movers(q1.movers, q1.scorecard, config),
        "q2_main": q2_urgency(q2.watch_list, config.shortlist_size),
        "q2_support": q2_gap(q2.shortlist),
        "q3_main": q3_deadlines(q3.late_by_window),
        "q3_support": q3_opportunities(q3.opportunities),
        "appendix_q1_quarterly": q1_quarterly(q1.quarterly),
        "appendix_q3_carriers": q3_processing_by_carrier(orders),
    }


__all__ = ["all_charts", "to_svg", "TOKENS", "pd"]
