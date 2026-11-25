# Docstring report (course SKILL.md: python-docstrings)

Scope: every module, class, function and method (including nested helpers) in `northwind/`, `run_analysis.py` and `verification/`. Tests are outside the scope.

**How the skill was applied.** Docstrings were written in Google style while the code was built. At the instructor's request they were then audited against every SKILL.md rule with `verification/check_docstrings.py`. The first audit found 50 of 162 docstrings breaking a rule: 40 had lines over 72 characters, 7 nested helpers had no docstring, and several summaries wrapped onto a second line or weren't in the imperative. All were fixed, touching docstrings only (an AST comparison confirmed the code is unchanged), and all tests still pass. CI now runs the audit on every push.

**Result:** 168/168 docstrings follow every rule (re-checked after the executive revisions added 6 functions).

## Assumptions to check

1. `metrics.top_share_of_increase`: documented as able to exceed 1, because a single account's gain can exceed a market's net increase when other accounts fell (`max / sum` with no cap).
2. `metrics.risk_tier`: products with no recent demand are documented as "No recent demand" even when out of stock, because that condition is checked first (decided at gate 1).
3. `metrics.recent_monthly_demand`: the 90-day window is documented as inclusive at both ends (6 Feb–6 May 1998), matching the `>=` and `<=` comparisons.
4. `metrics.demand_variability`: documented as using the population standard deviation (`ddof=0`), with zero-sales months counted.
5. `q2_inventory.average_net_price`: products with no sales in the window fall back to their all-time average, via `combine_first`.
6. `q3_logistics.group_gaps`: when several groups tie for the lowest median, the first in alphabetical order is the benchmark, because `idxmin` returns the first label.
7. `q3_logistics` freight: documented as a cost to Northwind; the data doesn't say who pays.
8. `q2_inventory.assess_products` `FlagPossibleShortage`: documented as a screening flag, not a confirmed backorder.

## Also noticed

- `q1_markets.summarise` produces per-market sentences that the page no longer shows (the report builds its own text). It's kept for the console and tests, but it could be removed.

## Docstrings

#### `module` — [northwind/__init__.py:1](northwind/__init__.py:1)
```python
"""Northwind business analysis: data loading, metrics and reporting.
"""
```

#### `load_model` — [northwind/__init__.py:9](northwind/__init__.py:9)
```python
"""Load, clean and join the workbook in one call.

Args:
    config (northwind.config.Config | None): Settings; None uses the
        defaults.

Returns:
    northwind.model.Model: Analysis-ready tables.
"""
```

#### `module` — [northwind/charts.py:1](northwind/charts.py:1)
```python
"""Charts for the report, rendered as themeable inline SVG.

Each chart is drawn with matplotlib in the light palette, then every
palette colour is swapped for a CSS variable so the same SVG follows the
page's light/dark theme. Colours follow the dataviz reference palette.
"""
```

#### `_money` — [northwind/charts.py:83](northwind/charts.py:83)
```python
"""Format dollars compactly.

Args:
    value (float): Amount in dollars.

Returns:
    str: e.g. "$40.1K" or "$950".
"""
```

#### `to_svg` — [northwind/charts.py:97](northwind/charts.py:97)
```python
"""Render a figure as themeable, accessible inline SVG.

Args:
    fig (matplotlib.figure.Figure): Figure to render; closed after.
    alt (str): Text alternative describing the chart's message.

Returns:
    str: SVG markup with palette colours replaced by CSS variables,
    fixed metadata, and a role, label and title for screen readers.
"""
```

#### `_hairline_grid` — [northwind/charts.py:123](northwind/charts.py:123)
```python
"""Draw recessive solid hairline gridlines behind the data.

Args:
    ax (matplotlib.axes.Axes): Axes to style.
    axis (str): "x", "y" or "both".

Returns:
    None.
"""
```

#### `_place_labels` — [northwind/charts.py:137](northwind/charts.py:137)
```python
"""Label each bubble where the text doesn't overlap other labels.

Tries above, below, right and left of the bubble in turn and keeps
the first position whose text box is clear of labels already placed
and inside the axes.

Args:
    fig (matplotlib.figure.Figure): Figure being drawn.
    ax (matplotlib.axes.Axes): Axes holding the bubbles.
    data (pandas.DataFrame): Rows with Market, x and y.
    sizes (pandas.Series): Marker areas, same index as ``data``.

Returns:
    None.
"""
```

#### `q1_matrix` — [northwind/charts.py:176](northwind/charts.py:176)
```python
"""Draw the main Q1 chart: share change against concentration.

Args:
    card (pandas.DataFrame): Q1 scorecard.
    config (northwind.config.Config): Thresholds.

Returns:
    str: Inline SVG.
"""
```

#### `q1_movers` — [northwind/charts.py:239](northwind/charts.py:239)
```python
"""Draw the supporting Q1 chart: biggest account changes.

Args:
    movers (pandas.DataFrame): Q1 movers table.
    card (pandas.DataFrame): Q1 scorecard (for each market's
        action).
    config (northwind.config.Config): Focus markets.

Returns:
    str: Inline SVG.
"""
```

#### `q1_quarterly` — [northwind/charts.py:284](northwind/charts.py:284)
```python
"""Draw each market's share of company revenue by quarter.

Args:
    quarterly (pandas.DataFrame): Q1 quarterly table.

Returns:
    str: Inline SVG.
"""
```

#### `q2_urgency` — [northwind/charts.py:324](northwind/charts.py:324)
```python
"""Draw the main Q2 chart: demand against months of stock.

Args:
    watch (pandas.DataFrame): Ranked watch list.
    shortlist_size (int): How many top products get rank labels.

Returns:
    str: Inline SVG.
"""
```

#### `q2_gap` — [northwind/charts.py:368](northwind/charts.py:368)
```python
"""Draw the supporting Q2 chart: stock against one month of demand.

The gap between the two dots is the least a purchase order would
need to cover one month of recent demand.

Args:
    shortlist (pandas.DataFrame): Top of the watch list.

Returns:
    str: Inline SVG.
"""
```

#### `q3_opportunities` — [northwind/charts.py:411](northwind/charts.py:411)
```python
"""Draw the supporting Q3 chart: dispatch time lost by group.

Freight gaps are not drawn: after adjustment they are not supported,
so they appear only in the detailed table.

Args:
    opps (pandas.DataFrame): Q3 opportunities table.
    top_n (int): Processing opportunities to show.

Returns:
    str: Inline SVG.
"""
```

#### `q3_deadlines` — [northwind/charts.py:446](northwind/charts.py:446)
```python
"""Draw the main Q3 chart: late-dispatch rate by allowed window.

Args:
    late_by_window (pandas.DataFrame): Q3 late-by-window table.

Returns:
    str: Inline SVG.
"""
```

#### `q3_processing_by_carrier` — [northwind/charts.py:476](northwind/charts.py:476)
```python
"""Draw the distribution of processing days by carrier.

Args:
    orders (pandas.DataFrame): Shipped orders.

Returns:
    str: Inline SVG.
"""
```

#### `all_charts` — [northwind/charts.py:503](northwind/charts.py:503)
```python
"""Render every chart used on the page.

Args:
    q1 (northwind.q1_markets.Q1Result): Q1 results.
    q2 (northwind.q2_inventory.Q2Result): Q2 results.
    q3 (northwind.q3_logistics.Q3Result): Q3 results.
    orders (pandas.DataFrame): Shipped orders for the appendix
        chart.
    config (northwind.config.Config): Settings.

Returns:
    dict[str, str]: SVG markup keyed by chart name.
"""
```

#### `module` — [northwind/clean.py:1](northwind/clean.py:1)
```python
"""Apply the cleaning rules from plan.md section 2.3.
"""
```

#### `clean_tables` — [northwind/clean.py:16](northwind/clean.py:16)
```python
"""Return cleaned copies of the workbook sheets.

Drops leftover columns, rounds discounts, parses order dates
(missing ShippedDate stays missing) and makes Discontinued a
boolean. The input is not modified.

Args:
    raw (dict[str, pandas.DataFrame]): Sheets as read from the
        workbook.

Returns:
    dict[str, pandas.DataFrame]: Cleaned sheets, keyed by sheet
    name.
"""
```

#### `module` — [northwind/config.py:1](northwind/config.py:1)
```python
"""Paths, dates, thresholds and region maps used by every analysis step.
"""
```

#### `Config` — [northwind/config.py:80](northwind/config.py:80)
```python
"""Settings for one analysis run.

Attributes:
    workbook (pathlib.Path): Input Excel workbook.
    output_dir (pathlib.Path): Folder for generated tables and
        manifest.
    docs_dir (pathlib.Path): Folder served by GitHub Pages.
    cutoff (pandas.Timestamp): Last order date; all recent windows
        end here.
    first_full_quarter (str): First complete calendar quarter.
    last_full_quarter (str): Last complete calendar quarter.
    current_window (tuple[str, ...]): Quarters in the Q1 growth
        window.
    prior_window (tuple[str, ...]): Same quarters one year earlier.
    outperform_threshold (float): Relative growth at or above which
        a market is Outperforming.
    underperform_threshold (float): Relative growth at or below
        which a market is Underperforming.
    concentration_threshold (float): Largest-customer share above
        which concentration risk is High.
    concentration_flag_margin (float): Dependence within this
        distance of the threshold is flagged as near the line.
    narrow_growth_share (float): One account supplying more than
        this share of a market's increase is flagged as narrow
        growth.
    min_orders_per_window (int): Fewer orders than this in either
        window gives "Insufficient data".
    near_threshold_margin (float): Relative growth this close to a
        performance threshold triggers the bootstrap check (plan
        4.4).
    bootstrap_resamples (int): Resamples for the bootstrap check.
    bootstrap_interval (float): Width of the bootstrap interval.
    movers_per_side (int): Gaining and losing accounts listed per
        market.
    demand_window_days (int): Length of the recent-demand window.
    days_per_month (float): Days used to convert to monthly rates.
    acceleration_ratio (float): Recent/long-run demand ratio above
        which demand counts as speeding up.
    demand_months (tuple[str, str]): First and last full month used
        for demand variability.
    critical_cover (float): Months of cover (incl. on order) below
        which a product is Critical.
    high_cover (float): Months of on-hand cover below which a
        product can be High.
    watch_cover (float): Months of on-hand cover used by Watch
        rules.
    high_variability (float): Coefficient of variation above which
        demand counts as erratic.
    lead_time_scenarios (tuple[float, ...]): Assumed lead times in
        months for suggested reorder levels.
    shortlist_size (int): Products shown on the main page for Q2.
    buy_list_size (int): Products listed with order quantities.
    slow_quantile (float): Quantile of processing days that defines
        a slow order.
    consolidation_share (float): Freight share of revenue above
        which a small order is a consolidation candidate.
    min_group_orders_per_band (int): Orders a group needs in a size
        band to serve as that band's benchmark.
    min_opportunity_orders (int): Opportunities resting on fewer
        orders get a bootstrap check (plan 4.4).
    region_mix_tolerance (float): Largest acceptable gap between
        carriers' destination shares before the regression check
        runs.
    freight_materiality (float): Carrier freight difference that
        counts as material.
    dispatch_materiality_days (float): Carrier dispatch difference
        that counts as material.
    freight_outlier_quantile (float): Freight above this quantile is
        dropped in the robustness check.
    seed (int): Random seed for any resampling.
    repo_url (str | None): Public repository link shown on the page;
        None until the repository exists (gate 7).
    focus_markets (tuple[str, ...]): Markets analysed individually.
    market_groups (dict[str, str]): Country to Q1 market.
    dest_regions (dict[str, str]): Country to Q3 destination region.
"""
```

#### `module` — [northwind/load.py:1](northwind/load.py:1)
```python
"""Read the Northwind workbook and check it has the expected structure.
"""
```

#### `SchemaError` — [northwind/load.py:26](northwind/load.py:26)
```python
"""Raised when the workbook lacks a required sheet or column.
"""
```

#### `file_sha256` — [northwind/load.py:30](northwind/load.py:30)
```python
"""Return the SHA-256 fingerprint of a file.

Args:
    path (str | pathlib.Path): File to fingerprint.

Returns:
    str: Hex digest of the file contents.
"""
```

#### `validate_schema` — [northwind/load.py:46](northwind/load.py:46)
```python
"""Check that every required sheet and column is present.

Args:
    sheets (dict[str, pandas.DataFrame]): Sheets keyed by sheet
        name.

Returns:
    None.

Raises:
    SchemaError: If a required sheet or column is missing.
"""
```

#### `load_workbook` — [northwind/load.py:68](northwind/load.py:68)
```python
"""Read all sheets of the workbook and validate their structure.

Args:
    path (str | pathlib.Path): Workbook to read.

Returns:
    dict[str, pandas.DataFrame]: Every sheet, keyed by sheet name.

Raises:
    FileNotFoundError: If the workbook does not exist.
    SchemaError: If a required sheet or column is missing.
"""
```

#### `module` — [northwind/metrics.py:1](northwind/metrics.py:1)
```python
"""Metric definitions from plan.md section 3, each coded once.
"""
```

#### `map_regions` — [northwind/metrics.py:13](northwind/metrics.py:13)
```python
"""Map each country to its group.

Args:
    countries (pandas.Series): Country names.
    mapping (dict[str, str]): Country to group name.

Returns:
    pandas.Series: Group name for each country, same index.

Raises:
    ValueError: If any country is not in ``mapping``.
"""
```

#### `quarter_of` — [northwind/metrics.py:32](northwind/metrics.py:32)
```python
"""Return the calendar quarter of each date.

Args:
    dates (pandas.Series): Datetimes.

Returns:
    pandas.Series: Quarterly periods, e.g. ``1997Q4``.
"""
```

#### `gross_revenue` — [northwind/metrics.py:46](northwind/metrics.py:46)
```python
"""Return revenue before discount for each order line.

Args:
    unit_price (pandas.Series): Price charged per unit on the line.
    quantity (pandas.Series): Units on the line.

Returns:
    pandas.Series: ``unit_price * quantity``.
"""
```

#### `net_revenue` — [northwind/metrics.py:59](northwind/metrics.py:59)
```python
"""Return revenue after discount for each order line.

Args:
    unit_price (pandas.Series): Price charged per unit on the line.
    quantity (pandas.Series): Units on the line.
    discount (pandas.Series): Discount as a fraction, 0 to 1.

Returns:
    pandas.Series: ``unit_price * quantity * (1 - discount)``.
"""
```

#### `window_growth` — [northwind/metrics.py:75](northwind/metrics.py:75)
```python
"""Return the relative change between two revenue windows.

Args:
    prior (float): Revenue in the earlier window.
    current (float): Revenue in the later window.

Returns:
    float: ``(current - prior) / prior``, or NaN if ``prior`` <= 0.
"""
```

#### `decompose_change` — [northwind/metrics.py:90](northwind/metrics.py:90)
```python
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
```

#### `account_contributions` — [northwind/metrics.py:119](northwind/metrics.py:119)
```python
"""Return each customer's change in revenue between two windows.

Args:
    rev_prior (pandas.Series): Revenue per customer, earlier window.
    rev_current (pandas.Series): Revenue per customer, later window.

Returns:
    pandas.Series: Change per customer (absent = 0), largest first;
    sums to the total change.
"""
```

#### `top_share` — [northwind/metrics.py:137](northwind/metrics.py:137)
```python
"""Return the largest value's share of the total.

Args:
    values (pandas.Series): Non-negative amounts, e.g. revenue per
        customer.

Returns:
    float: ``max / sum``, or NaN if the total is not positive.
"""
```

#### `top_share_of_increase` — [northwind/metrics.py:153](northwind/metrics.py:153)
```python
"""Return the largest account gain as a share of the net increase.

Args:
    contributions (pandas.Series): Change in revenue per customer.

Returns:
    float: Largest gain divided by the net change, or NaN if the net
    change is not positive. Can exceed 1 when other accounts fell.
"""
```

#### `relative_growth` — [northwind/metrics.py:193](northwind/metrics.py:193)
```python
"""Return the change in a market's share of company revenue.

Equals ``(1 + market growth) / (1 + company growth) - 1``.

Args:
    share_prior (float): Market share in the earlier window.
    share_current (float): Market share in the later window.

Returns:
    float: ``share_current / share_prior - 1``; NaN if the earlier
    share is not positive.
"""
```

#### `performance_level` — [northwind/metrics.py:211](northwind/metrics.py:211)
```python
"""Classify relative growth as Outperforming, In line or Underperforming.

Args:
    rel_growth (float): Output of ``relative_growth``.
    config (northwind.config.Config): Performance thresholds.

Returns:
    str | None: The level, or None if ``rel_growth`` is NaN.
"""
```

#### `concentration_risk` — [northwind/metrics.py:230](northwind/metrics.py:230)
```python
"""Classify dependence on the largest customer as High or Low.

Args:
    dependence (float): Largest customer's share of market revenue.
    config (northwind.config.Config): Concentration threshold.

Returns:
    str: "High" if dependence exceeds the threshold, else "Low".
"""
```

#### `near_concentration_line` — [northwind/metrics.py:243](northwind/metrics.py:243)
```python
"""Flag dependence close to the concentration threshold.

Args:
    dependence (float): Largest customer's share of market revenue.
    config (northwind.config.Config): Threshold and margin.

Returns:
    bool: True if within the margin of the threshold, inclusive.
"""
```

#### `narrow_growth` — [northwind/metrics.py:259](northwind/metrics.py:259)
```python
"""Flag growth supplied mostly by one account.

Args:
    top_increase_share (float): Output of ``top_share_of_increase``;
        NaN when revenue did not increase.
    config (northwind.config.Config): Narrow-growth share.

Returns:
    bool: True if one account supplied more than the set share.
"""
```

#### `recommended_action` — [northwind/metrics.py:273](northwind/metrics.py:273)
```python
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
```

#### `recent_monthly_demand` — [northwind/metrics.py:295](northwind/metrics.py:295)
```python
"""Return units ordered per month over the recent window, per product.

The window is the ``window_days`` calendar days ending on
``cutoff``, both ends included.

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
```

#### `longrun_monthly_demand` — [northwind/metrics.py:318](northwind/metrics.py:318)
```python
"""Return units ordered per month since each product's first sale.

Args:
    lines (pandas.DataFrame): Order lines with ProductID, OrderDate
        and Quantity.
    cutoff (pandas.Timestamp): End of the period, included.
    days_per_month (float): Days per month for the conversion.

Returns:
    pandas.Series: Monthly units indexed by ProductID.
"""
```

#### `demand_variability` — [northwind/metrics.py:336](northwind/metrics.py:336)
```python
"""Return the coefficient of variation of monthly units per product.

Months without sales count as zero. Uses the population standard
deviation.

Args:
    lines (pandas.DataFrame): Order lines with ProductID, OrderDate
        and Quantity.
    first_month (str): First full month, e.g. "1996-07".
    last_month (str): Last full month, e.g. "1998-04".

Returns:
    pandas.Series: Std / mean of monthly units, indexed by
        ProductID; NaN where mean demand is zero.
"""
```

#### `months_of_cover` — [northwind/metrics.py:367](northwind/metrics.py:367)
```python
"""Return how many months stock lasts at the given demand.

Args:
    stock (pandas.Series): Units available.
    monthly_demand (pandas.Series): Units demanded per month.

Returns:
    pandas.Series: ``stock / monthly_demand``; NaN where demand is
        0.
"""
```

#### `risk_tier` — [northwind/metrics.py:382](northwind/metrics.py:382)
```python
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
```

#### `processing_days` — [northwind/metrics.py:415](northwind/metrics.py:415)
```python
"""Return days from order to dispatch.

Args:
    order_date (pandas.Series): Order dates.
    shipped_date (pandas.Series): Dispatch dates; NaT if not
        shipped.

Returns:
    pandas.Series: Days as floats; NaN for unshipped orders.
"""
```

#### `slack_days` — [northwind/metrics.py:429](northwind/metrics.py:429)
```python
"""Return days between dispatch and the customer's required date.

Args:
    required_date (pandas.Series): Required dates.
    shipped_date (pandas.Series): Dispatch dates; NaT if not
        shipped.

Returns:
    pandas.Series: Positive = early, negative = late; NaN if
        unshipped.
"""
```

#### `is_late` — [northwind/metrics.py:444](northwind/metrics.py:444)
```python
"""Flag orders dispatched after the required date.

Args:
    slack (pandas.Series): Output of ``slack_days``.

Returns:
    pandas.Series: True where slack < 0; False for unshipped orders.
"""
```

#### `freight_per_unit` — [northwind/metrics.py:458](northwind/metrics.py:458)
```python
"""Return freight cost per unit shipped.

Args:
    freight (pandas.Series): Freight per order.
    units (pandas.Series): Units per order.

Returns:
    pandas.Series: ``freight / units``; NaN where units is 0.
"""
```

#### `freight_share` — [northwind/metrics.py:471](northwind/metrics.py:471)
```python
"""Return freight as a share of order net revenue.

Args:
    freight (pandas.Series): Freight per order.
    revenue (pandas.Series): Net revenue per order.

Returns:
    pandas.Series: ``freight / revenue``; NaN where revenue is 0.
"""
```

#### `size_band_edges` — [northwind/metrics.py:484](northwind/metrics.py:484)
```python
"""Return quartile edges of order size.

Args:
    units (pandas.Series): Units per order, all orders.

Returns:
    numpy.ndarray: Five edges: min, 25th, 50th, 75th percentile,
        max.

Raises:
    ValueError: If edges are not strictly increasing.
"""
```

#### `assign_size_band` — [northwind/metrics.py:503](northwind/metrics.py:503)
```python
"""Label each order with its size band.

Bands include their upper edge; the lowest band also includes the
minimum.

Args:
    units (pandas.Series): Units per order.
    edges (numpy.ndarray): Output of ``size_band_edges``.

Returns:
    pandas.Series: Ordered categorical of ``SIZE_BAND_LABELS``.
"""
```

#### `excess_over_benchmark` — [northwind/metrics.py:521](northwind/metrics.py:521)
```python
"""Return the total amount by which values exceed a benchmark.

Values at or below the benchmark contribute zero, never a negative.

Args:
    values (pandas.Series): Per-order measure, e.g. processing days.
    benchmark (float): Benchmark level.
    weights (pandas.Series | None): Multiplier per order, e.g. units
        for freight per unit; None means 1.

Returns:
    float: Sum of ``max(0, value - benchmark) * weight``, ignoring
        NaN.
"""
```

#### `module` — [northwind/model.py:1](northwind/model.py:1)
```python
"""Build the order-line, order and product tables (plan.md section 2.2).
"""
```

#### `ModelError` — [northwind/model.py:11](northwind/model.py:11)
```python
"""Raised when a join changes row counts or leaves keys unmatched.
"""
```

#### `Model` — [northwind/model.py:16](northwind/model.py:16)
```python
"""Joined, analysis-ready tables.

Attributes:
    order_lines (pandas.DataFrame): One row per product on an order.
    orders (pandas.DataFrame): One row per order.
    products (pandas.DataFrame): One row per product, with demand.
    customers (pandas.DataFrame): One row per customer, with market.
    size_band_edges (numpy.ndarray): Order-size quartile edges.
"""
```

#### `_join` — [northwind/model.py:34](northwind/model.py:34)
```python
"""Left-join many-to-one and check nothing was lost or left unmatched.

Args:
    left (pandas.DataFrame): Many side.
    right (pandas.DataFrame): One side; ``on`` must be unique here.
    on (str): Join key.
    label (str): Join name used in error messages.
    required (list[str]): Columns from ``right`` that must be
        filled.

Returns:
    pandas.DataFrame: Joined table with the same rows as ``left``.

Raises:
    ModelError: If the row count changes or a required column has
        missing values after the join.
"""
```

#### `build_model` — [northwind/model.py:61](northwind/model.py:61)
```python
"""Join the cleaned sheets into the three analysis tables.

Args:
    tables (dict[str, pandas.DataFrame]): Output of
        ``northwind.clean.clean_tables``.
    config (northwind.config.Config): Cutoff, windows and region
        maps.

Returns:
    Model: Order lines, orders, products and customers.

Raises:
    ModelError: If any join loses rows or leaves keys unmatched.
    ValueError: If a country is missing from a region map.
"""
```

#### `module` — [northwind/q1_markets.py:1](northwind/q1_markets.py:1)
```python
"""Q1: rate markets on share change and customer concentration.

Shows how each market performed relative to the company, how much it
depends on one customer, and where sales attention could go
(plan.md section 3.2).
"""
```

#### `Q1Result` — [northwind/q1_markets.py:26](northwind/q1_markets.py:26)
```python
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
```

#### `prepare_lines` — [northwind/q1_markets.py:64](northwind/q1_markets.py:64)
```python
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
```

#### `_in_quarters` — [northwind/q1_markets.py:90](northwind/q1_markets.py:90)
```python
"""Return the lines whose quarter is in ``quarters``.

Args:
    lines (pandas.DataFrame): Lines with a Quarter column.
    quarters (Iterable[str]): Quarters such as "1997Q4".

Returns:
    pandas.DataFrame: Matching lines.
"""
```

#### `_full_quarters` — [northwind/q1_markets.py:103](northwind/q1_markets.py:103)
```python
"""Return the complete quarters in the analysis period.

Args:
    config (northwind.config.Config): First and last full quarter.

Returns:
    list[str]: Quarters in order, e.g. ["1996Q3", ..., "1998Q1"].
"""
```

#### `_latest_four` — [northwind/q1_markets.py:116](northwind/q1_markets.py:116)
```python
"""Return the four most recent complete quarters.

Args:
    config (northwind.config.Config): Last full quarter.

Returns:
    list[str]: Four quarters ending at ``config.last_full_quarter``.
"""
```

#### `quarterly_table` — [northwind/q1_markets.py:130](northwind/q1_markets.py:130)
```python
"""Return revenue, orders, customers and share per market and quarter.

Args:
    lines (pandas.DataFrame): Output of ``prepare_lines``.
    config (northwind.config.Config): Last full quarter.

Returns:
    pandas.DataFrame: One row per market and quarter (all quarters,
    zero-filled), with Share of company revenue and IsComplete False
    for the partial last quarter.
"""
```

#### `_trend` — [northwind/q1_markets.py:157](northwind/q1_markets.py:157)
```python
"""Return a linear trend per period as a share of the average level.

Args:
    series (pandas.Series): Values in time order; NaN are dropped.

Returns:
    float: Least-squares slope divided by the mean; NaN if fewer
        than two values or the mean is not positive.
"""
```

#### `_sign` — [northwind/q1_markets.py:174](northwind/q1_markets.py:174)
```python
"""Return -1, 0 or 1; 0 for NaN.

Args:
    value (float): Number to classify.

Returns:
    int: Sign of ``value``.
"""
```

#### `scorecard` — [northwind/q1_markets.py:186](northwind/q1_markets.py:186)
```python
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
```

#### `needs_bootstrap` — [northwind/q1_markets.py:312](northwind/q1_markets.py:312)
```python
"""Decide whether a market meets a plan 4.4 trigger.

Args:
    row (pandas.Series): One scorecard row.
    config (northwind.config.Config): Thresholds and margin.

Returns:
    str | None: The reason, or None if no trigger is met.
"""
```

#### `bootstrap_relative_growth` — [northwind/q1_markets.py:333](northwind/q1_markets.py:333)
```python
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
```

#### `performance_confidence` — [northwind/q1_markets.py:366](northwind/q1_markets.py:366)
```python
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
```

#### `uncertainty_table` — [northwind/q1_markets.py:406](northwind/q1_markets.py:406)
```python
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
```

#### `robustness` — [northwind/q1_markets.py:434](northwind/q1_markets.py:434)
```python
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
```

#### `window_check` — [northwind/q1_markets.py:469](northwind/q1_markets.py:469)
```python
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
```

#### `_money` — [northwind/q1_markets.py:504](northwind/q1_markets.py:504)
```python
"""Format dollars compactly, e.g. $12.3K.

Args:
    value (float): Amount in dollars.

Returns:
    str: Formatted amount.
"""
```

#### `flag_list` — [northwind/q1_markets.py:516](northwind/q1_markets.py:516)
```python
"""Return the warning flags raised for one market.

Args:
    row (pandas.Series): One scorecard row with confidence added.

Returns:
    list[str]: Flag descriptions; empty if none.
"""
```

#### `summarise` — [northwind/q1_markets.py:539](northwind/q1_markets.py:539)
```python
"""Write one plain-language recommendation per market.

Args:
    card (pandas.DataFrame): Scorecard with confidence added.
    movers (pandas.DataFrame): Movers table.
    company (dict): Company totals from ``scorecard``.

Returns:
    dict[str, str]: Text keyed by market.
"""
```

#### `run` — [northwind/q1_markets.py:576](northwind/q1_markets.py:576)
```python
"""Run the full Q1 analysis.

Args:
    model (northwind.model.Model): Joined tables.
    config (northwind.config.Config): Settings.

Returns:
    Q1Result: All Q1 tables and summaries.
"""
```

#### `module` — [northwind/q2_inventory.py:1](northwind/q2_inventory.py:1)
```python
"""Q2: rank active products for restocking.

Shows which products purchasing should restock first (plan.md
sections 3.3, 3.4 and 4).
"""
```

#### `Q2Result` — [northwind/q2_inventory.py:22](northwind/q2_inventory.py:22)
```python
"""Outputs of the Q2 restocking analysis.

Attributes:
    watch_list (pandas.DataFrame): Every active product, ranked by
        tier and then monthly revenue at stake, with an action
        (appendix).
    shortlist (pandas.DataFrame): The top of the watch list shown on
        the main page.
    headline (str): Catalogue-wide finding stated above the
        shortlist.
    no_reorder_rule (pandas.DataFrame): Active products with reorder
        level 0, with suggested levels.
    discontinued_stock (pandas.DataFrame): Discontinued products
        that still hold stock.
    robustness (pandas.DataFrame): Critical/High membership under
        other demand windows (plan 8.3).
    tier_counts (dict[str, int]): Active products per tier.
    caveat (str): Statement shown with the Q2 results.
"""
```

#### `_reorder_column` — [northwind/q2_inventory.py:53](northwind/q2_inventory.py:53)
```python
"""Return the column name for a suggested reorder level.

Args:
    lead_time (float): Assumed lead time in months.

Returns:
    str: e.g. "SuggestedReorder_0.5m".
"""
```

#### `average_net_price` — [northwind/q2_inventory.py:65](northwind/q2_inventory.py:65)
```python
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
```

#### `pending_units` — [northwind/q2_inventory.py:98](northwind/q2_inventory.py:98)
```python
"""Return units on orders that have not been shipped, per product.

Args:
    lines (pandas.DataFrame): Order lines with ProductID, Quantity
        and ShippedDate.

Returns:
    pandas.Series: Units waiting to ship, indexed by ProductID.
"""
```

#### `restock_action` — [northwind/q2_inventory.py:111](northwind/q2_inventory.py:111)
```python
"""Return the recommended purchasing action for one product.

Args:
    row (pandas.Series): One row of ``assess_products``.

Returns:
    str: Action text.
"""
```

#### `assess_products` — [northwind/q2_inventory.py:136](northwind/q2_inventory.py:136)
```python
"""Compute demand, stock cover, tier and action for every product.

Args:
    model (northwind.model.Model): Joined tables.
    config (northwind.config.Config): Windows and thresholds.
    window_days (int | None): Recent-demand window; None uses
        ``config.demand_window_days``.

Returns:
    pandas.DataFrame: One row per product (active and discontinued).
"""
```

#### `rank` — [northwind/q2_inventory.py:178](northwind/q2_inventory.py:178)
```python
"""Order products by tier, then by monthly revenue at stake.

Args:
    products (pandas.DataFrame): Output of ``assess_products``.

Returns:
    pandas.DataFrame: Sorted copy with a 1-based Rank column.
"""
```

#### `robustness` — [northwind/q2_inventory.py:193](northwind/q2_inventory.py:193)
```python
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
```

#### `headline` — [northwind/q2_inventory.py:221](northwind/q2_inventory.py:221)
```python
"""State the catalogue-wide stock finding in one sentence.

Args:
    active (pandas.DataFrame): Ranked active products.
    config (northwind.config.Config): Cover thresholds.

Returns:
    str: Headline text.
"""
```

#### `run` — [northwind/q2_inventory.py:241](northwind/q2_inventory.py:241)
```python
"""Run the full Q2 analysis.

Args:
    model (northwind.model.Model): Joined tables.
    config (northwind.config.Config): Settings.

Returns:
    Q2Result: All Q2 tables.
"""
```

#### `per_unit` — [northwind/q2_inventory.py:83](northwind/q2_inventory.py:83)
```python
"""Return net revenue per unit for each product.

Args:
    frame (pandas.DataFrame): Order lines.

Returns:
    pandas.Series: Net revenue / units, by ProductID.
"""
```

#### `module` — [northwind/q3_logistics.py:1](northwind/q3_logistics.py:1)
```python
"""Q3: compare processing time and freight across shipments.

Shows how they vary and where the biggest logistics improvements are
(plan.md sections 3.5-3.7 and 4).
"""
```

#### `Q3Result` — [northwind/q3_logistics.py:34](northwind/q3_logistics.py:34)
```python
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
    consolidation (dict): Small orders where freight is a large
        share of revenue.
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
    slow_share_by_carrier (dict[str, float]): Share of each
        carrier's orders that are slow.
    caveat (str): Statement shown with the Q3 results.
"""
```

#### `shipped_orders` — [northwind/q3_logistics.py:81](northwind/q3_logistics.py:81)
```python
"""Return shipped orders with a slow-order flag.

Args:
    model (northwind.model.Model): Joined tables.
    config (northwind.config.Config): Slow-order quantile.

Returns:
    pandas.DataFrame: Shipped orders with IsSlow added.
"""
```

#### `breakdown` — [northwind/q3_logistics.py:97](northwind/q3_logistics.py:97)
```python
"""Summarise processing and freight for each value of one column.

Args:
    orders (pandas.DataFrame): Shipped orders.
    col (str): Grouping column.

Returns:
    pandas.DataFrame: Orders, processing median/mean/90th
        percentile, slow and late counts and shares, freight per
        unit and share medians, and total freight per group.
"""
```

#### `within_bands` — [northwind/q3_logistics.py:125](northwind/q3_logistics.py:125)
```python
"""Return medians for each group within each size band.

Args:
    orders (pandas.DataFrame): Shipped orders.
    col (str): Grouping column, e.g. ShipperName.
    band_col (str): Size band column.

Returns:
    pandas.DataFrame: One row per band and group.
"""
```

#### `group_gaps` — [northwind/q3_logistics.py:146](northwind/q3_logistics.py:146)
```python
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
```

#### `opportunities` — [northwind/q3_logistics.py:205](northwind/q3_logistics.py:205)
```python
"""Collect processing and freight opportunities across dimensions.

Args:
    orders (pandas.DataFrame): Shipped orders.
    config (northwind.config.Config): Settings.
    band_col (str): Size band column.
    benchmark (str): "best" or "overall" (see ``group_gaps``).

Returns:
    pandas.DataFrame: One row per positive opportunity with Type
        (Processing in order-days, Freight in dollars), Dimension,
        Group, Size, Orders, SizePerOrder and Action; ranked within
        each Type.
"""
```

#### `backlog` — [northwind/q3_logistics.py:248](northwind/q3_logistics.py:248)
```python
"""Summarise orders that were never shipped.

Args:
    model (northwind.model.Model): Joined tables.
    config (northwind.config.Config): Cutoff.

Returns:
    dict: Orders, revenue held, units, median and oldest age in
        days, and how many are already past their required date.
"""
```

#### `consolidation` — [northwind/q3_logistics.py:272](northwind/q3_logistics.py:272)
```python
"""Size the small-order consolidation opportunity (plan 3.7).

Args:
    orders (pandas.DataFrame): Shipped orders.
    config (northwind.config.Config): Freight-share threshold.

Returns:
    dict: Candidate orders, their freight, that freight's share of
        all freight, and whether it is material (at least 1% of
        freight).
"""
```

#### `late_by_window` — [northwind/q3_logistics.py:292](northwind/q3_logistics.py:292)
```python
"""Count late dispatches by the customer's allowed window.

Args:
    orders (pandas.DataFrame): Shipped orders.

Returns:
    pandas.DataFrame: AllowedDays, Orders, LateOrders and LateShare.
"""
```

#### `region_mix_gap` — [northwind/q3_logistics.py:309](northwind/q3_logistics.py:309)
```python
"""Return the largest gap between carriers in any destination's share.

Args:
    orders (pandas.DataFrame): Shipped orders.

Returns:
    float: Largest absolute difference in destination share between
    any two carriers.
"""
```

#### `ols_hc1` — [northwind/q3_logistics.py:323](northwind/q3_logistics.py:323)
```python
"""Fit ordinary least squares with HC1 robust standard errors.

Args:
    y (numpy.ndarray): Outcome, shape (n,).
    X (pandas.DataFrame): Design matrix including the intercept.

Returns:
    pandas.DataFrame: Estimate and StdError per column of ``X``.
"""
```

#### `_design` — [northwind/q3_logistics.py:343](northwind/q3_logistics.py:343)
```python
"""Build a design matrix with an intercept and dummy variables.

Args:
    orders (pandas.DataFrame): Shipped orders.
    categorical (list[str]): Columns to dummy-code.
    numeric (dict[str, pandas.Series]): Extra numeric columns.
    baselines (dict[str, str]): Reference level per categorical
        column.

Returns:
    pandas.DataFrame: Design matrix.
"""
```

#### `carrier_regression` — [northwind/q3_logistics.py:369](northwind/q3_logistics.py:369)
```python
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
```

#### `apply_adjustment` — [northwind/q3_logistics.py:419](northwind/q3_logistics.py:419)
```python
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
```

#### `deadline_priority` — [northwind/q3_logistics.py:449](northwind/q3_logistics.py:449)
```python
"""Check whether short-deadline orders are processed faster.

Args:
    orders (pandas.DataFrame): Shipped orders.

Returns:
    dict: Median processing days per allowed window, whether the
    shortest-window orders are processed faster than the most common
    window, and the share of late orders that are slow orders.
"""
```

#### `regression_trigger` — [northwind/q3_logistics.py:472](northwind/q3_logistics.py:472)
```python
"""Decide whether the carrier regression is needed (plan 4.4).

Args:
    orders (pandas.DataFrame): Shipped orders.
    opps (pandas.DataFrame): Output of ``opportunities``.
    config (northwind.config.Config): Region-mix tolerance.

Returns:
    str | None: Reason, or None if the condition is not met.
"""
```

#### `flag_small_opportunities` — [northwind/q3_logistics.py:493](northwind/q3_logistics.py:493)
```python
"""Add a confidence column; bootstrap opportunities on few orders.

Args:
    opps (pandas.DataFrame): Output of ``opportunities``; modified
        in place.
    orders (pandas.DataFrame): Shipped orders.
    config (northwind.config.Config): Threshold, seed and resamples.

Returns:
    pandas.DataFrame: The same table with Confidence added.
"""
```

#### `robustness` — [northwind/q3_logistics.py:530](northwind/q3_logistics.py:530)
```python
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
```

#### `run` — [northwind/q3_logistics.py:568](northwind/q3_logistics.py:568)
```python
"""Run the full Q3 analysis.

Args:
    model (northwind.model.Model): Joined tables.
    config (northwind.config.Config): Settings.

Returns:
    Q3Result: All Q3 tables and findings.
"""
```

#### `module` — [northwind/report.py:1](northwind/report.py:1)
```python
"""Assemble the self-contained HTML report (plan.md section 5).
"""
```

#### `pct` — [northwind/report.py:21](northwind/report.py:21)
```python
"""Format a fraction as a percentage.

Args:
    value (float): Fraction, e.g. 0.25.
    signed (bool): Show a leading + for positive values.
    digits (int): Decimal places.

Returns:
    str: e.g. "+25%", or an em dash for missing values.
"""
```

#### `money` — [northwind/report.py:38](northwind/report.py:38)
```python
"""Format dollars compactly.

Args:
    value (float): Amount in dollars.
    digits (int): Decimals for thousands.

Returns:
    str: e.g. "$25.9K", "$950", "−$10.5K".
"""
```

#### `num` — [northwind/report.py:55](northwind/report.py:55)
```python
"""Format a number with thousands separators.

Args:
    value (float): Number.
    digits (int): Decimal places.

Returns:
    str: Formatted number, or an em dash for missing values.
"""
```

#### `table` — [northwind/report.py:68](northwind/report.py:68)
```python
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
```

#### `join_names` — [northwind/report.py:87](northwind/report.py:87)
```python
"""Join names as plain English: "A", "A and B", "A, B and C".

Args:
    names (list[str]): Names.

Returns:
    str: Joined text.
"""
```

#### `q1_section` — [northwind/report.py:104](northwind/report.py:104)
```python
"""Build the Q1 section context.

Args:
    q1 (northwind.q1_markets.Q1Result): Q1 results.
    charts (dict[str, str]): Rendered charts.

Returns:
    dict: Template context for Q1.
"""
```

#### `market_action` — [northwind/report.py:230](northwind/report.py:230)
```python
"""Write one specific action for a market: who to contact and why.

Args:
    row (pandas.Series): Scorecard row (Market may be the index
        name).
    movers (pandas.DataFrame): Q1 movers table.

Returns:
    str: Action naming the first account and the next step.
"""
```

#### `metrics_text` — [northwind/report.py:265](northwind/report.py:265)
```python
"""Return the generic description of an action.

Args:
    action (str): Action name.

Returns:
    str: Description from the metrics module.
"""
```

#### `rescue_detail` — [northwind/report.py:277](northwind/report.py:277)
```python
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
```

#### `q1_interpretation` — [northwind/report.py:321](northwind/report.py:321)
```python
"""Turn the Q1 results into business implications, one per market group.

Args:
    q1 (northwind.q1_markets.Q1Result): Q1 results.

Returns:
    list[str]: Interpretation bullets (plain text).
"""
```

#### `shortfall_range` — [northwind/report.py:400](northwind/report.py:400)
```python
"""Return the top products' shortfall to one month of demand.

Args:
    short (pandas.DataFrame): Q2 shortlist.

Returns:
    tuple[float, float]: Shortfall using long-run demand and using
    recent (90-day) demand. Recent demand is the early-1998 peak, so
    it gives the upper figure.
"""
```

#### `q2_interpretation` — [northwind/report.py:417](northwind/report.py:417)
```python
"""Turn the Q2 results into business implications.

Args:
    q2 (northwind.q2_inventory.Q2Result): Q2 results.
    config (northwind.config.Config): Settings.

Returns:
    list[str]: Interpretation bullets (plain text).
"""
```

#### `wilson` — [northwind/report.py:450](northwind/report.py:450)
```python
"""Return the Wilson 95% interval for a proportion.

Args:
    k (int): Successes.
    n (int): Trials.
    z (float): Normal quantile.

Returns:
    tuple[float, float]: Lower and upper bounds.
"""
```

#### `q3_facts` — [northwind/report.py:469](northwind/report.py:469)
```python
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
```

#### `q3_interpretation` — [northwind/report.py:511](northwind/report.py:511)
```python
"""Turn the Q3 results into business implications.

Args:
    q3 (northwind.q3_logistics.Q3Result): Q3 results.

Returns:
    list[str]: Interpretation bullets (plain text).
"""
```

#### `q1_flag_text` — [northwind/report.py:555](northwind/report.py:555)
```python
"""Return short flag labels for one Q1 market.

Args:
    row (pandas.Series): Scorecard row.

Returns:
    list[str]: Flag labels.
"""
```

#### `q2_section` — [northwind/report.py:574](northwind/report.py:574)
```python
"""Build the Q2 section context.

Args:
    q2 (northwind.q2_inventory.Q2Result): Q2 results.
    charts (dict[str, str]): Rendered charts.
    config (northwind.config.Config): Settings.

Returns:
    dict: Template context for Q2.
"""
```

#### `buy_list` — [northwind/report.py:637](northwind/report.py:637)
```python
"""Return the top products with how many units to order.

The order range runs from the units needed to cover one month at
long-run demand to the units needed at recent (peak) demand.

Args:
    short (pandas.DataFrame): Q2 shortlist, in rank order.
    size (int): Number of products to list.

Returns:
    pandas.DataFrame: Top rows with an OrderRange column.
"""
```

#### `q3_actions` — [northwind/report.py:659](northwind/report.py:659)
```python
"""Write the Q3 actions, each naming what to look at first.

Args:
    q3 (northwind.q3_logistics.Q3Result): Q3 results.
    f (dict): Output of ``q3_facts``.

Returns:
    list[dict]: Actions with text and status.
"""
```

#### `q3_section` — [northwind/report.py:681](northwind/report.py:681)
```python
"""Build the Q3 section context.

Args:
    q3 (northwind.q3_logistics.Q3Result): Q3 results.
    charts (dict[str, str]): Rendered charts.

Returns:
    dict: Template context for Q3.
"""
```

#### `_regression_text` — [northwind/report.py:737](northwind/report.py:737)
```python
"""Add formatted effect and interval columns to the regression table.

Args:
    regression (pandas.DataFrame): Q3 regression table.

Returns:
    pandas.DataFrame: Copy with EffectText and IntervalText.
"""
```

#### `appendix` — [northwind/report.py:764](northwind/report.py:764)
```python
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
```

#### `load_review` — [northwind/report.py:870](northwind/report.py:870)
```python
"""Read the independent review's objections and resolutions, if any.

Args:
    path (pathlib.Path | None): JSON file; None uses
        verification/fresh_review.json.

Returns:
    list[dict]: Items with claim, severity, objection and
    resolution; empty if the review hasn't been recorded.
"""
```

#### `summary_cards` — [northwind/report.py:889](northwind/report.py:889)
```python
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
```

#### `build_context` — [northwind/report.py:961](northwind/report.py:961)
```python
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
```

#### `render` — [northwind/report.py:997](northwind/report.py:997)
```python
"""Render the report HTML.

Args:
    context (dict): Output of ``build_context``.

Returns:
    str: Complete HTML document.
"""
```

#### `write_site` — [northwind/report.py:1011](northwind/report.py:1011)
```python
"""Write the page for GitHub Pages.

Args:
    page (str): HTML document.
    docs_dir (pathlib.Path): Folder served by GitHub Pages.

Returns:
    pathlib.Path: Path of the written index.html.
"""
```

#### `flags` — [northwind/report.py:131](northwind/report.py:131)
```python
"""Return the flag labels for one market, or a dash.

Args:
    row (pandas.Series): Scorecard row.

Returns:
    str: Flags joined by semicolons, or "—".
"""
```

#### `tentative` — [northwind/report.py:169](northwind/report.py:169)
```python
"""Say whether a market's action should be marked tentative.

Args:
    market (str): Market name.

Returns:
    bool: True if its share direction changes between period
    comparisons or its performance level isn't conclusive.
"""
```

#### `biggest` — [northwind/report.py:333](northwind/report.py:333)
```python
"""Return the account with the largest change in one direction.

Args:
    market (str): Market name.
    direction (str): "Gain" or "Loss".

Returns:
    str | None: "Name ($change)", or None if there is none.
"""
```

#### `share` — [northwind/report.py:349](northwind/report.py:349)
```python
"""Return a market's share of revenue before and after.

Args:
    market (str): Market name.

Returns:
    str: e.g. "10.6% → 19.7%".
"""
```

#### `fmt` — [northwind/report.py:746](northwind/report.py:746)
```python
"""Format a regression effect in its model's unit.

Args:
    model (str): "Freight" (percent) or "Dispatch" (days).
    value (float): Effect or interval bound.

Returns:
    str: Formatted value.
"""
```

#### `module` — [run_analysis.py:1](run_analysis.py:1)
```python
"""Build every output from the workbook.

Usage:
    python run_analysis.py

Builds the model, runs Q1-Q3, cross-checks the results in SQL, renders
the charts and writes the page to docs/index.html. Exits with status 1
if any cross-check fails.
"""
```

#### `write_table` — [run_analysis.py:21](run_analysis.py:21)
```python
"""Write a table as UTF-8 CSV, creating the folder if needed.

Args:
    frame (pandas.DataFrame): Table to write.
    path (pathlib.Path): Destination file.

Returns:
    None.
"""
```

#### `main` — [run_analysis.py:35](run_analysis.py:35)
```python
"""Run the pipeline and write tables and the run manifest.

Args:
    None.

Returns:
    int: Process exit status, 0 on success.
"""
```

#### `module` — [verification/check_docstrings.py:1](verification/check_docstrings.py:1)
```python
"""Check docstrings against the course SKILL.md rules.

Rules checked for every module, class, function and method (including
nested functions):

* a docstring exists; modules get one at the very top;
* function and method docstrings are multi-line, with a one-line summary
  ending in a period, then a blank line;
* an ``Args:`` section lists every parameter except ``self``/``cls``
  exactly once, in signature order (``Args:`` / ``None.`` when there
  are none);
* a ``Returns:`` (or ``Yields:``) section is present;
* no docstring line is longer than 72 characters;
* the summary doesn't start with "This function", "Helper", "Used to".

Usage:
    python verification/check_docstrings.py [paths...]

Exits with status 1 and lists every problem if any rule is broken.
"""
```

#### `_params` — [verification/check_docstrings.py:32](verification/check_docstrings.py:32)
```python
"""Return a function's parameter names in signature order.

Args:
    node (ast.FunctionDef | ast.AsyncFunctionDef): Function node.

Returns:
    list[str]: Names, excluding ``self`` and ``cls``; ``*args`` and
    ``**kwargs`` keep their bare names.
"""
```

#### `_documented_args` — [verification/check_docstrings.py:52](verification/check_docstrings.py:52)
```python
"""Return parameter names listed in a Google-style Args section.

Args:
    doc (str): Docstring text.

Returns:
    list[str] | None: Names in order; an empty list for
    ``Args: None.``; None if there is no Args section.
"""
```

#### `check_node` — [verification/check_docstrings.py:85](verification/check_docstrings.py:85)
```python
"""Check one module, class or function docstring.

Args:
    node (ast.AST): Module, ClassDef or FunctionDef node.
    path (pathlib.Path): File the node is in.
    problems (list[str]): Collected problems; appended to.

Returns:
    None.
"""
```

#### `main` — [verification/check_docstrings.py:127](verification/check_docstrings.py:127)
```python
"""Check every Python file under the given paths.

Args:
    paths (list[str] | None): Files or folders relative to the
        project root; None uses the default set.

Returns:
    int: 0 if every docstring follows the rules, otherwise 1.
"""
```

#### `module` — [verification/check_public_site.py:1](verification/check_public_site.py:1)
```python
"""Check the published page and repository anonymously.

Implements plan.md §8.5 as an anonymous visitor would see it.

Uses only the Python standard library: no cookies, no tokens, no
sign-in.

Checks:
1. The page URL returns HTTP 200 over HTTPS.
2. The page served is byte-for-byte the same as docs/index.html here.
3. The page contains the three questions and the appendix.
4. The repository page and raw README return HTTP 200, and the public
   GitHub API reports the repository as public.

Usage:
    python verification/check_public_site.py

Exits with status 1 if any check fails, and writes the results to
outputs/verification/public_site.json.
"""
```

#### `fetch` — [verification/check_public_site.py:36](verification/check_public_site.py:36)
```python
"""Fetch a URL anonymously.

Args:
    url (str): Address to fetch.

Returns:
    tuple[int, bytes, str]: Status code, body and final URL (after
    redirects); status 0 and an empty body on network errors.
"""
```

#### `main` — [verification/check_public_site.py:56](verification/check_public_site.py:56)
```python
"""Run every check, print a report and save it.

Args:
    None.

Returns:
    int: 0 if every check passes, otherwise 1.
"""
```

#### `record` — [verification/check_public_site.py:67](verification/check_public_site.py:67)
```python
"""Add one check result.

Args:
    name (str): Check description.
    ok (bool): Whether it passed.
    detail (str): Evidence shown in the report.

Returns:
    None.
"""
```

#### `module` — [verification/check_site_current.py:1](verification/check_site_current.py:1)
```python
"""Check that the committed page matches a fresh build (used by CI).

Run after ``python run_analysis.py``. Compares the freshly built
``docs/index.html`` with the version committed at HEAD. The build
timestamp is ignored, and each chart is compared by its text description
(which lists every plotted value) rather than by drawing coordinates, so
sub-pixel font differences between operating systems don't cause false
failures while any change in a number or a word still does.

Usage:
    python verification/check_site_current.py

Exits with status 1 if the pages differ.
"""
```

#### `normalise` — [verification/check_site_current.py:26](verification/check_site_current.py:26)
```python
"""Reduce a page to the parts that must match exactly.

Args:
    page (str): HTML document.

Returns:
    list[str]: Lines with the timestamp removed and each SVG
    replaced by its aria-label.
"""
```

#### `main` — [verification/check_site_current.py:41](verification/check_site_current.py:41)
```python
"""Compare the built page with the committed one.

Args:
    None.

Returns:
    int: 0 if they match, otherwise 1.
"""
```

#### `module` — [verification/sql_crosscheck.py:1](verification/sql_crosscheck.py:1)
```python
"""Recalculate headline figures in SQL and compare with the model.

This path shares no code with the pandas pipeline: the workbook is read
cell by cell with openpyxl and every figure is computed in plain SQL.

Usage:
    python verification/sql_crosscheck.py

Exits with status 1 if any figure disagrees.
"""
```

#### `load_into_sqlite` — [verification/sql_crosscheck.py:29](verification/sql_crosscheck.py:29)
```python
"""Copy the needed sheets into an in-memory SQLite database.

Args:
    path (pathlib.Path): Workbook to read.

Returns:
    sqlite3.Connection: Database with one table per sheet; dates are
    stored as ISO 8601 text.
"""
```

#### `product_checks` — [verification/sql_crosscheck.py:139](verification/sql_crosscheck.py:139)
```python
"""Recompute recent demand and risk tier per active product in SQL.

Args:
    con (sqlite3.Connection): Database from ``load_into_sqlite``.
    config (northwind.config.Config): Window and tier thresholds.
    watch_list (pandas.DataFrame): Q2 watch list from the pipeline.

Returns:
    list[dict]: One demand comparison per product, one tier
    comparison per product, and a summary check of tier agreement.
"""
```

#### `logistics_checks` — [verification/sql_crosscheck.py:223](verification/sql_crosscheck.py:223)
```python
"""Recompute carrier medians and opportunities per size band in SQL.

The size-band edges are the only input taken from the pipeline.

Args:
    con (sqlite3.Connection): Database from ``load_into_sqlite``.
    config (northwind.config.Config): Minimum orders per band.
    model (northwind.model.Model): Supplies the size-band edges.
    q3_result (northwind.q3_logistics.Q3Result): Pipeline results.

Returns:
    list[dict]: Comparison results.
"""
```

#### `pandas_figures` — [verification/sql_crosscheck.py:255](verification/sql_crosscheck.py:255)
```python
"""Compute the same figures from the pandas model.

Args:
    model (northwind.model.Model): Model built by the pipeline.

Returns:
    tuple[dict, dict, dict]: Scalar totals, revenue by quarter and
    revenue by customer country.
"""
```

#### `compare` — [verification/sql_crosscheck.py:283](verification/sql_crosscheck.py:283)
```python
"""Compare one figure from each path.

Args:
    name (str): Figure name.
    sql_value (float | int): Value from SQL.
    pandas_value (float | int): Value from the pandas model.
    tol (float): Largest allowed absolute difference.

Returns:
    dict: Name, both values, absolute difference and pass flag.
"""
```

#### `market_checks` — [verification/sql_crosscheck.py:317](verification/sql_crosscheck.py:317)
```python
"""Recompute Q1 window revenue and growth per market in SQL.

The country-to-market map is the only input taken from the
pipeline's configuration.

Args:
    con (sqlite3.Connection): Database from ``load_into_sqlite``.
    config (northwind.config.Config): Windows and market map.
    scorecard (pandas.DataFrame): Q1 scorecard from the pipeline.

Returns:
    list[dict]: Comparison results.
"""
```

#### `run_checks` — [verification/sql_crosscheck.py:351](verification/sql_crosscheck.py:351)
```python
"""Run every cross-check and save the results as JSON.

Args:
    config (northwind.config.Config | None): Settings; None uses
        the defaults.
    model (northwind.model.Model | None): Pipeline model; None
        builds it.

Returns:
    list[dict]: One result per check, each with a pass flag.
"""
```

#### `main` — [verification/sql_crosscheck.py:386](verification/sql_crosscheck.py:386)
```python
"""Run the cross-check and print a report.

Args:
    None.

Returns:
    int: 0 if every figure matches, otherwise 1.
"""
```

Reply with numbered corrections (for example "3: exclusive at the start") or ask for any docstring to be rewritten.
