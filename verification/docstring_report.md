# Docstring report (python-docstrings skill)

## Skill invocation

- **Skill:** `python-docstrings`, the instructor-provided Claude Code
  skill, installed unchanged at `.claude/skills/python-docstrings/SKILL.md`
  (git-ignored, so it isn't in the public repository).
- **How:** invoked through Claude Code's Skill tool in this session on
  2026-11-24: `Skill(skill="python-docstrings", args="Document all Python
  files: northwind/*.py, run_analysis.py, verification/*.py,
  tests/**/*.py")`. The tool returned `Launching skill: python-docstrings`
  and loaded the skill's instructions, which were then followed as written.
- **Scope:** every module, class, function and method (including nested
  helpers, pytest fixtures and test functions) in `northwind/`,
  `run_analysis.py`, `verification/` and `tests/`. Fixtures received by a
  test are documented as parameters.
- **Style:** Google style, as already used by the project; 72-character
  lines; one Args line per parameter in signature order; a Returns section
  always.
- **Changes:** 166 docstrings in `tests/`: 157 written
  where none existed and 9 rewritten because they broke a
  rule (single-line fixture docstrings without Args/Returns, helpers
  without Args/Returns, module docstrings with lines over 72 characters).
  The 180 docstrings in `northwind/`, `run_analysis.py`,
  `verification/` and the remaining test docstrings already met every rule,
  so the skill left them unchanged.
- **Corrections after review (assumptions 7 and 16):** two docstrings
  reworded: the summary and description of
  `test_q3_real.test_regression_uses_best_carrier_as_baseline`, and the
  `regression_reason` attribute in the `Q3Result` docstring
  (`northwind/q3_logistics.py`). Wording only; no code changed.
- **Only docstrings changed:** each changed file's AST, with docstrings
  removed, is identical to `git show HEAD:<file>` (14 of 14 files).
- **Compliance:** `python verification/check_docstrings.py northwind
  run_analysis.py verification tests` reports **346/346 docstrings
  follow every rule (0 problems)**. CI now runs that same command.

## Docstrings written

### tests/conftest.py

#### `sheets` (rewritten) — [tests/conftest.py:88](tests/conftest.py:88)
```python
"""Return a fresh copy of the synthetic sheets for one test.

Args:
    None.

Returns:
    dict[str, pandas.DataFrame]: Sheets keyed by sheet name; a test
    may modify them freely.
"""
```

#### `synthetic_workbook` (rewritten) — [tests/conftest.py:102](tests/conftest.py:102)
```python
"""Write the synthetic sheets to a real .xlsx file.

Args:
    tmp_path_factory (pytest.TempPathFactory): Session temp-folder
        factory.

Returns:
    pathlib.Path: The workbook, shared by the whole test session.
"""
```

#### `synthetic_model` (rewritten) — [tests/conftest.py:120](tests/conftest.py:120)
```python
"""Build a model from the synthetic workbook, end to end.

Args:
    synthetic_workbook (pathlib.Path): Synthetic .xlsx file.

Returns:
    northwind.model.Model: Model built with a cutoff of 6 May 1998.
"""
```

#### `config` (rewritten) — [tests/conftest.py:134](tests/conftest.py:134)
```python
"""Return the default configuration.

Args:
    None.

Returns:
    northwind.config.Config: A ``Config()`` with default settings.
"""
```

### tests/unit/test_load_clean.py

Test functions (each docstring is the summary below, then the Args lines for the parameters named, then `Returns:` / `None.`; `Args:` / `None.` where there are no parameters):

| Function | Location | Summary | Args |
|---|---|---|---|
| `test_missing_sheet_raises` | [tests/unit/test_load_clean.py:10](tests/unit/test_load_clean.py:10) | Check that a missing sheet raises SchemaError naming it. | `sheets` |
| `test_missing_column_raises` | [tests/unit/test_load_clean.py:24](tests/unit/test_load_clean.py:24) | Check that a missing column raises SchemaError naming it. | `sheets` |
| `test_missing_file_raises` | [tests/unit/test_load_clean.py:38](tests/unit/test_load_clean.py:38) | Check that a nonexistent workbook raises FileNotFoundError. | `tmp_path` |
| `test_fingerprint_is_stable` | [tests/unit/test_load_clean.py:51](tests/unit/test_load_clean.py:51) | Check that the file SHA-256 is repeatable and 64 characters. | `synthetic_workbook` |
| `test_discounts_rounded_to_two_decimals` | [tests/unit/test_load_clean.py:64](tests/unit/test_load_clean.py:64) | Check that cleaning rounds discounts to two decimals. | `sheets` |
| `test_leftover_columns_dropped` | [tests/unit/test_load_clean.py:77](tests/unit/test_load_clean.py:77) | Check that unused columns are dropped and Price is kept. | `sheets` |
| `test_unshipped_date_stays_missing` | [tests/unit/test_load_clean.py:93](tests/unit/test_load_clean.py:93) | Check that an unshipped order keeps a missing ShippedDate. | `sheets` |
| `test_input_not_modified` | [tests/unit/test_load_clean.py:108](tests/unit/test_load_clean.py:108) | Check that cleaning leaves the input sheets unchanged. | `sheets` |

Args lines used by these tests:
```text
sheets (dict[str, pandas.DataFrame]): Fresh synthetic sheets.
tmp_path (pathlib.Path): Empty per-test folder.
synthetic_workbook (pathlib.Path): Synthetic .xlsx file.
```

### tests/unit/test_metrics.py

#### `test_decomposition_adds_up_exactly` — [tests/unit/test_metrics.py:75](tests/unit/test_metrics.py:75)
```python
"""Check the orders and size effects sum to the revenue change.

Args:
    r0 (float): Revenue in the earlier window.
    o0 (int): Orders in the earlier window.
    r1 (float): Revenue in the later window.
    o1 (int): Orders in the later window.

Returns:
    None.
"""
```

#### `test_performance_level_edges` — [tests/unit/test_metrics.py:160](tests/unit/test_metrics.py:160)
```python
"""Check performance levels at the threshold edges.

Args:
    rel (float): Relative growth; NaN when there is no data.
    expected (str | None): Expected performance level.

Returns:
    None.
"""
```

#### `test_concentration_risk_has_two_levels` — [tests/unit/test_metrics.py:174](tests/unit/test_metrics.py:174)
```python
"""Check concentration risk is High only above 50%.

Args:
    dep (float): Share of revenue from the top customer.
    expected (str): Expected risk level.

Returns:
    None.
"""
```

#### `test_near_concentration_line_flag` — [tests/unit/test_metrics.py:191](tests/unit/test_metrics.py:191)
```python
"""Check the flag for dependence within 5 points of 50%.

Args:
    dep (float): Share of revenue from the top customer; may be NaN.
    expected (bool): Expected flag.

Returns:
    None.
"""
```

#### `test_narrow_growth_flag` — [tests/unit/test_metrics.py:205](tests/unit/test_metrics.py:205)
```python
"""Check the narrow-growth flag is set only above 60%.

Args:
    share (float): Top customer's share of the increase; may be NaN.
    expected (bool): Expected flag.

Returns:
    None.
"""
```

#### `test_all_six_actions` — [tests/unit/test_metrics.py:229](tests/unit/test_metrics.py:229)
```python
"""Check each performance and risk pair maps to its action.

Args:
    performance (str): Performance level.
    risk (str): Concentration risk level.
    expected (str): Expected recommended action.

Returns:
    None.
"""
```

#### `_lines` — [tests/unit/test_metrics.py:259](tests/unit/test_metrics.py:259)
```python
"""Build order lines for the demand tests.

Args:
    rows (list[tuple[int, str, int]]): ProductID, ISO order date and
        quantity for each line.

Returns:
    pandas.DataFrame: Lines with OrderDate parsed to datetimes.
"""
```

#### `_tier` — [tests/unit/test_metrics.py:338](tests/unit/test_metrics.py:338)
```python
"""Return the risk tier of one product.

Args:
    stock (int): Units in stock.
    on_order (int): Units on order.
    reorder (int): Reorder level; 0 means no reorder rule.
    demand (float): Recent monthly demand in units.
    cv (float): Coefficient of variation of monthly demand.

Returns:
    str: Tier from ``metrics.risk_tier`` with the default config.
"""
```

#### `test_risk_tier_rules` — [tests/unit/test_metrics.py:371](tests/unit/test_metrics.py:371)
```python
"""Check the risk-tier rules at and around each boundary.

Args:
    stock (int): Units in stock.
    on_order (int): Units on order.
    reorder (int): Reorder level; 0 means no reorder rule.
    demand (float): Recent monthly demand in units.
    cv (float): Coefficient of variation of monthly demand.
    expected (str): Expected tier.

Returns:
    None.
"""
```

Test functions (each docstring is the summary below, then the Args lines for the parameters named, then `Returns:` / `None.`; `Args:` / `None.` where there are no parameters):

| Function | Location | Summary | Args |
|---|---|---|---|
| `test_region_maps_cover_same_21_countries` | [tests/unit/test_metrics.py:17](tests/unit/test_metrics.py:17) | Check both region maps cover the same 21 countries. | None. |
| `test_unknown_country_raises` | [tests/unit/test_metrics.py:30](tests/unit/test_metrics.py:30) | Check that mapping an unknown country raises ValueError. | None. |
| `test_net_and_gross_revenue` | [tests/unit/test_metrics.py:45](tests/unit/test_metrics.py:45) | Check gross and discounted net revenue per line. | None. |
| `test_window_growth` | [tests/unit/test_metrics.py:61](tests/unit/test_metrics.py:61) | Check window growth, and NaN when prior revenue is zero. | None. |
| `test_decomposition_signs` | [tests/unit/test_metrics.py:91](tests/unit/test_metrics.py:91) | Check that growth from more orders is all orders effect. | None. |
| `test_account_contributions_sum_to_change` | [tests/unit/test_metrics.py:106](tests/unit/test_metrics.py:106) | Check account contributions sum to the total change. | None. |
| `test_top_shares` | [tests/unit/test_metrics.py:122](tests/unit/test_metrics.py:122) | Check top-customer share of revenue and of the increase. | None. |
| `test_relative_growth_equals_share_change` | [tests/unit/test_metrics.py:136](tests/unit/test_metrics.py:136) | Check relative growth equals the change in revenue share. | None. |
| `test_insufficient_data_overrides_action` | [tests/unit/test_metrics.py:244](tests/unit/test_metrics.py:244) | Check that thin data gives Insufficient data. | None. |
| `test_recent_window_boundaries` | [tests/unit/test_metrics.py:274](tests/unit/test_metrics.py:274) | Check the 90-day window keeps both end days and nothing else. | None. |
| `test_longrun_demand_from_first_sale` | [tests/unit/test_metrics.py:294](tests/unit/test_metrics.py:294) | Check long-run demand is measured from the first sale. | None. |
| `test_variability_counts_zero_months` | [tests/unit/test_metrics.py:308](tests/unit/test_metrics.py:308) | Check demand variability counts months without sales. | None. |
| `test_zero_demand_gives_no_cover_not_error` | [tests/unit/test_metrics.py:325](tests/unit/test_metrics.py:325) | Check zero demand gives NaN months of cover, not an error. | None. |
| `test_processing_and_lateness` | [tests/unit/test_metrics.py:390](tests/unit/test_metrics.py:390) | Check processing days, NaN when unshipped, and late flags. | None. |
| `test_freight_ratios_handle_zero` | [tests/unit/test_metrics.py:408](tests/unit/test_metrics.py:408) | Check freight ratios, including NaN for zero units. | None. |
| `test_size_bands_at_edges` | [tests/unit/test_metrics.py:421](tests/unit/test_metrics.py:421) | Check size bands, with edge values in the lower band. | None. |
| `test_size_band_edges_must_be_distinct` | [tests/unit/test_metrics.py:438](tests/unit/test_metrics.py:438) | Check that duplicate size-band edges raise ValueError. | None. |
| `test_excess_never_negative_and_weighted` | [tests/unit/test_metrics.py:453](tests/unit/test_metrics.py:453) | Check excess over a benchmark is non-negative and weightable. | None. |

### tests/unit/test_model.py

Test functions (each docstring is the summary below, then the Args lines for the parameters named, then `Returns:` / `None.`; `Args:` / `None.` where there are no parameters):

| Function | Location | Summary | Args |
|---|---|---|---|
| `test_row_counts` | [tests/unit/test_model.py:12](tests/unit/test_model.py:12) | Check order-line and order counts against hand values. | `synthetic_model` |
| `test_revenue_totals_match_hand_calculation` | [tests/unit/test_model.py:26](tests/unit/test_model.py:26) | Check net and gross revenue against the hand calculation. | `synthetic_model` |
| `test_revenue_uses_line_price_not_list_price` | [tests/unit/test_model.py:44](tests/unit/test_model.py:44) | Check that revenue uses the order-line price, not list price. | `synthetic_model` |
| `test_order_measures` | [tests/unit/test_model.py:59](tests/unit/test_model.py:59) | Check processing days, shipped and late flags, units, freight. | `synthetic_model` |
| `test_markets_and_regions` | [tests/unit/test_model.py:77](tests/unit/test_model.py:77) | Check market comes from the customer, region from ship country. | `synthetic_model` |
| `test_customer_without_orders_kept` | [tests/unit/test_model.py:94](tests/unit/test_model.py:94) | Check that a customer without orders is kept in the model. | `synthetic_model` |
| `test_product_demand` | [tests/unit/test_model.py:108](tests/unit/test_model.py:108) | Check recent monthly demand over the 90-day window. | `synthetic_model` |
| `test_unmatched_key_raises` | [tests/unit/test_model.py:125](tests/unit/test_model.py:125) | Check that an unknown shipper ID raises ModelError. | `sheets` |
| `test_unmapped_country_raises` | [tests/unit/test_model.py:139](tests/unit/test_model.py:139) | Check that an unmapped customer country raises ValueError. | `sheets` |

Args lines used by these tests:
```text
synthetic_model (northwind.model.Model): Model of the synthetic workbook.
sheets (dict[str, pandas.DataFrame]): Fresh synthetic sheets.
```

### tests/unit/test_q1_markets.py

#### `_make_lines` (rewritten) — [tests/unit/test_q1_markets.py:14](tests/unit/test_q1_markets.py:14)
```python
"""Build order lines for three markets with known answers.

Up:   prior 10 orders x $100 = $1,000; current 12 x $150 = $1,800,
      split evenly between C1 and C2 (dependence exactly 50%).
Down: prior 10 x $100 = $1,000 from C3; current C3 4 x $100 + C4 4 x
      $50 = $600 (C3 holds 2/3 of the latest four quarters).
Tiny: 2 orders in each window, too few to judge.

Args:
    None.

Returns:
    pandas.DataFrame: Lines with OrderID, CustomerID, CustomerName,
    Quarter, NetRevenue and Market.
"""
```

#### `_make_lines.add` — [tests/unit/test_q1_markets.py:32](tests/unit/test_q1_markets.py:32)
```python
"""Append ``n`` identical orders to ``rows``.

Args:
    market (str): Market name.
    customer (str): Customer ID; its name is ``Name <ID>``.
    quarter (str): Order quarter, e.g. ``1997Q4``.
    n (int): Number of orders.
    revenue (float): Net revenue of each order.

Returns:
    None. Appends to ``rows`` and advances ``order_id``.
"""
```

#### `lines` — [tests/unit/test_q1_markets.py:66](tests/unit/test_q1_markets.py:66)
```python
"""Return the hand-built order lines.

Args:
    None.

Returns:
    pandas.DataFrame: Output of ``_make_lines``.
"""
```

#### `scored` — [tests/unit/test_q1_markets.py:79](tests/unit/test_q1_markets.py:79)
```python
"""Score the hand-built markets.

Args:
    lines (pandas.DataFrame): Hand-built order lines.

Returns:
    tuple[pandas.DataFrame, pandas.DataFrame, dict]: Scorecard
    indexed by Market, movers table and company totals.
"""
```

#### `test_bootstrap_triggers` — [tests/unit/test_q1_markets.py:263](tests/unit/test_q1_markets.py:263)
```python
"""Check when a market needs the bootstrap check, and why.

Args:
    rel (float): Relative growth.
    consistent (bool): Whether the share measures agree in
        direction.
    expected (str | None): Expected trigger reason; None when no
        bootstrap is needed.

Returns:
    None.
"""
```

Test functions (each docstring is the summary below, then the Args lines for the parameters named, then `Returns:` / `None.`; `Args:` / `None.` where there are no parameters):

| Function | Location | Summary | Args |
|---|---|---|---|
| `test_company_totals` | [tests/unit/test_q1_markets.py:93](tests/unit/test_q1_markets.py:93) | Check company revenue in both windows and its growth. | `scored` |
| `test_relative_growth_and_shares` | [tests/unit/test_q1_markets.py:110](tests/unit/test_q1_markets.py:110) | Check market growth, relative growth and revenue shares. | `scored` |
| `test_actions_and_flags` | [tests/unit/test_q1_markets.py:129](tests/unit/test_q1_markets.py:129) | Check performance, risk, action and flags per market. | `scored` |
| `test_partial_quarter_excluded` | [tests/unit/test_q1_markets.py:151](tests/unit/test_q1_markets.py:151) | Check that the partial quarter is left out of the windows. | `scored` |
| `test_decomposition_adds_up` | [tests/unit/test_q1_markets.py:166](tests/unit/test_q1_markets.py:166) | Check the orders and size effects sum to each change. | `scored` |
| `test_dependence` | [tests/unit/test_q1_markets.py:183](tests/unit/test_q1_markets.py:183) | Check top-customer dependence in each market. | `scored` |
| `test_movers_sum_and_direction` | [tests/unit/test_q1_markets.py:199](tests/unit/test_q1_markets.py:199) | Check movers sum to the market change and are labelled right. | `scored` |
| `test_consistency_flag` | [tests/unit/test_q1_markets.py:219](tests/unit/test_q1_markets.py:219) | Check the share measures agree in direction for market Up. | `scored` |
| `test_quarterly_table` | [tests/unit/test_q1_markets.py:234](tests/unit/test_q1_markets.py:234) | Check the quarterly table's rows, completeness flag and totals. | `lines` |
| `test_bootstrap_is_reproducible_and_brackets_estimate` | [tests/unit/test_q1_markets.py:280](tests/unit/test_q1_markets.py:280) | Check the bootstrap is repeatable and brackets the estimate. | `lines`, `scored` |
| `test_clear_levels_skip_bootstrap` | [tests/unit/test_q1_markets.py:299](tests/unit/test_q1_markets.py:299) | Check only triggered markets are bootstrapped. | `lines` |
| `test_summary_is_worded_as_recommendation` | [tests/unit/test_q1_markets.py:316](tests/unit/test_q1_markets.py:316) | Check market summaries read as suggestions with caveats. | `lines` |
| `test_unknown_basis_raises` | [tests/unit/test_q1_markets.py:334](tests/unit/test_q1_markets.py:334) | Check that an unknown revenue basis raises ValueError. | `synthetic_model` |

Args lines used by these tests:
```text
scored (tuple[pandas.DataFrame, pandas.DataFrame, dict]): Scorecard indexed by Market, movers table and company totals.
lines (pandas.DataFrame): Hand-built order lines.
synthetic_model (northwind.model.Model): Model of the synthetic workbook.
```

### tests/unit/test_q2_inventory.py

#### `module` (rewritten) — [tests/unit/test_q2_inventory.py:1](tests/unit/test_q2_inventory.py:1)
```python
"""Unit tests for Q2 restocking, using the synthetic workbook.

Synthetic products (see tests/conftest.py):
  1 Tea:   active, stock 0, 10 on order, reorder level 5;
           10 units ordered on 1 Apr 1998 (inside the 90-day
           window).
  2 Fish:  active, stock 50, nothing on order, no reorder rule;
           4 units on the unshipped order of 1 May 1998.
  3 Juice: discontinued, stock 3; last sold Oct 1997.
"""
```

#### `result` — [tests/unit/test_q2_inventory.py:24](tests/unit/test_q2_inventory.py:24)
```python
"""Run Q2 on the synthetic model.

Args:
    synthetic_model (northwind.model.Model): Model of the synthetic
        workbook.

Returns:
    northwind.q2_inventory.Q2Result: Q2 results, shared by the
    module.
"""
```

#### `products` — [tests/unit/test_q2_inventory.py:39](tests/unit/test_q2_inventory.py:39)
```python
"""Assess every synthetic product.

Args:
    synthetic_model (northwind.model.Model): Model of the synthetic
        workbook.

Returns:
    pandas.DataFrame: Product assessment indexed by ProductID.
"""
```

#### `test_restock_actions` — [tests/unit/test_q2_inventory.py:171](tests/unit/test_q2_inventory.py:171)
```python
"""Check the restock action for each tier and situation.

Args:
    tier (str): Risk tier.
    on_order (int): Units on order.
    no_rule (bool): Whether the product has no reorder level.
    expected (str): Expected action.

Returns:
    None.
"""
```

Test functions (each docstring is the summary below, then the Args lines for the parameters named, then `Returns:` / `None.`; `Args:` / `None.` where there are no parameters):

| Function | Location | Summary | Args |
|---|---|---|---|
| `test_demand_cover_and_tier` | [tests/unit/test_q2_inventory.py:52](tests/unit/test_q2_inventory.py:52) | Check demand, cover, tier and action for Tea and Fish. | `products` |
| `test_average_price_falls_back_to_all_orders` | [tests/unit/test_q2_inventory.py:69](tests/unit/test_q2_inventory.py:69) | Check the average price falls back to all orders when needed. | `products` |
| `test_revenue_at_risk_and_suggested_levels` | [tests/unit/test_q2_inventory.py:84](tests/unit/test_q2_inventory.py:84) | Check revenue at risk and suggested reorder levels. | `products` |
| `test_pending_units_and_shortage_flag` | [tests/unit/test_q2_inventory.py:99](tests/unit/test_q2_inventory.py:99) | Check pending units and the possible-shortage flag. | `products` |
| `test_watch_list_excludes_discontinued_and_is_ranked` | [tests/unit/test_q2_inventory.py:114](tests/unit/test_q2_inventory.py:114) | Check the watch list drops discontinued items and is ranked. | `result` |
| `test_side_tables` | [tests/unit/test_q2_inventory.py:130](tests/unit/test_q2_inventory.py:130) | Check the no-reorder-rule and discontinued-stock tables. | `result` |
| `test_robustness_shape` | [tests/unit/test_q2_inventory.py:145](tests/unit/test_q2_inventory.py:145) | Check the robustness table covers 60 and 120 days and holds. | `result` |
| `test_rank_breaks_ties_by_revenue` | [tests/unit/test_q2_inventory.py:187](tests/unit/test_q2_inventory.py:187) | Check ranking by tier, then by revenue at risk. | None. |

Args lines used by these tests:
```text
products (pandas.DataFrame): Product assessment indexed by ProductID.
result (northwind.q2_inventory.Q2Result): Q2 results for the synthetic model.
```

### tests/unit/test_q3_logistics.py

#### `_orders` (rewritten) — [tests/unit/test_q3_logistics.py:11](tests/unit/test_q3_logistics.py:11)
```python
"""Build shipped orders in one size band.

Args:
    groups (dict[str, list[float]]): Values for each order, keyed by
        group.

Returns:
    pandas.DataFrame: One Small, 2-unit order per value, with the
    value as both ProcessingDays and FreightPerUnit.
"""
```

#### `orders` — [tests/unit/test_q3_logistics.py:33](tests/unit/test_q3_logistics.py:33)
```python
"""Return ten orders for group A and ten for group B.

Args:
    None.

Returns:
    pandas.DataFrame: A at 5 days each; B with eight at 5 days and
    two at 15 days.
"""
```

Test functions (each docstring is the summary below, then the Args lines for the parameters named, then `Returns:` / `None.`; `Args:` / `None.` where there are no parameters):

| Function | Location | Summary | Args |
|---|---|---|---|
| `test_gap_against_best_group` | [tests/unit/test_q3_logistics.py:47](tests/unit/test_q3_logistics.py:47) | Check gaps are measured against the best group's median. | `orders` |
| `test_gap_is_weighted` | [tests/unit/test_q3_logistics.py:64](tests/unit/test_q3_logistics.py:64) | Check the gap is weighted by units when asked. | `orders` |
| `test_best_group_needs_enough_orders` | [tests/unit/test_q3_logistics.py:77](tests/unit/test_q3_logistics.py:77) | Check a group with too few orders can't be the benchmark. | None. |
| `test_overall_benchmark_and_bad_option` | [tests/unit/test_q3_logistics.py:93](tests/unit/test_q3_logistics.py:93) | Check the overall benchmark, and ValueError for a bad option. | `orders` |
| `test_ols_hc1_recovers_exact_line` | [tests/unit/test_q3_logistics.py:108](tests/unit/test_q3_logistics.py:108) | Check OLS recovers an exact line with zero standard errors. | None. |
| `test_adjustment_marks_carriers` | [tests/unit/test_q3_logistics.py:125](tests/unit/test_q3_logistics.py:125) | Check adjustment relabels carrier gaps and their actions. | None. |
| `test_deadline_priority` | [tests/unit/test_q3_logistics.py:152](tests/unit/test_q3_logistics.py:152) | Check short-deadline priority, late-and-slow share and medians. | None. |
| `test_backlog_and_consolidation` | [tests/unit/test_q3_logistics.py:173](tests/unit/test_q3_logistics.py:173) | Check the unshipped backlog and the consolidation estimate. | `synthetic_model` |
| `test_late_by_window` | [tests/unit/test_q3_logistics.py:197](tests/unit/test_q3_logistics.py:197) | Check order and late counts by allowed delivery window. | `synthetic_model` |

Args lines used by these tests:
```text
orders (pandas.DataFrame): Shipped orders for groups A and B.
synthetic_model (northwind.model.Model): Model of the synthetic workbook.
```

### tests/unit/test_report.py

#### `_row` — [tests/unit/test_report.py:15](tests/unit/test_report.py:15)
```python
"""Build a scorecard row for a Rescue market, Central.

Args:
    top_change (float): Revenue change of the top customer, Big Co.

Returns:
    pandas.Series: Row with Big Co as top customer and 55%
    dependence on it.
"""
```

Test functions (each docstring is the summary below, then the Args lines for the parameters named, then `Returns:` / `None.`; `Args:` / `None.` where there are no parameters):

| Function | Location | Summary | Args |
|---|---|---|---|
| `test_rescue_when_key_account_grew_points_elsewhere` | [tests/unit/test_report.py:29](tests/unit/test_report.py:29) | Check that a growing key account points the rescue at a loser. | None. |
| `test_rescue_when_key_account_fell_reviews_it` | [tests/unit/test_report.py:44](tests/unit/test_report.py:44) | Check that a shrinking key account is put up for review. | None. |

### tests/integration/test_q1_real.py

#### `result` — [tests/integration/test_q1_real.py:19](tests/integration/test_q1_real.py:19)
```python
"""Run Q1 on the real workbook.

Args:
    None.

Returns:
    northwind.q1_markets.Q1Result: Q1 results, shared by the module.
"""
```

Test functions (each docstring is the summary below, then the Args lines for the parameters named, then `Returns:` / `None.`; `Args:` / `None.` where there are no parameters):

| Function | Location | Summary | Args |
|---|---|---|---|
| `test_ten_markets_four_focus` | [tests/integration/test_q1_real.py:32](tests/integration/test_q1_real.py:32) | Check there are ten markets and the four expected focus ones. | `result` |
| `test_markets_add_up_to_company` | [tests/integration/test_q1_real.py:47](tests/integration/test_q1_real.py:47) | Check market revenue, orders and shares add up to the company. | `result` |
| `test_relative_growth_formula` | [tests/integration/test_q1_real.py:65](tests/integration/test_q1_real.py:65) | Check relative growth against its formula for every market. | `result` |
| `test_decomposition_adds_up_for_every_market` | [tests/integration/test_q1_real.py:79](tests/integration/test_q1_real.py:79) | Check the orders and size effects sum to each market's change. | `result` |
| `test_quarterly_table_matches_total_revenue` | [tests/integration/test_q1_real.py:93](tests/integration/test_q1_real.py:93) | Check the quarterly table sums to total net revenue. | `result` |
| `test_actions_and_confidence_valid` | [tests/integration/test_q1_real.py:107](tests/integration/test_q1_real.py:107) | Check action, confidence and risk use only allowed values. | `result` |
| `test_near_line_flag_matches_definition` | [tests/integration/test_q1_real.py:123](tests/integration/test_q1_real.py:123) | Check the near-line flag matches its 45-55% definition. | `result` |
| `test_bootstrap_only_where_triggered` | [tests/integration/test_q1_real.py:138](tests/integration/test_q1_real.py:138) | Check only triggered markets get a bootstrap confidence label. | `result` |
| `test_run_is_deterministic` | [tests/integration/test_q1_real.py:154](tests/integration/test_q1_real.py:154) | Check a second run gives the same scorecard and bootstrap. | `result` |
| `test_uncertainty_covers_every_market_and_brackets_estimate` | [tests/integration/test_q1_real.py:170](tests/integration/test_q1_real.py:170) | Check every market has a likely range around its estimate. | `result` |
| `test_every_market_has_a_summary` | [tests/integration/test_q1_real.py:186](tests/integration/test_q1_real.py:186) | Check every market has a summary. | `result` |
| `test_window_check_covers_every_market` | [tests/integration/test_q1_real.py:199](tests/integration/test_q1_real.py:199) | Check the window check covers every market and matches the base. | `result` |

Args lines used by these tests:
```text
result (northwind.q1_markets.Q1Result): Q1 results for the real workbook.
```

### tests/integration/test_q2_real.py

#### `result` — [tests/integration/test_q2_real.py:17](tests/integration/test_q2_real.py:17)
```python
"""Run Q2 on the real workbook.

Args:
    None.

Returns:
    northwind.q2_inventory.Q2Result: Q2 results, shared by the
    module.
"""
```

Test functions (each docstring is the summary below, then the Args lines for the parameters named, then `Returns:` / `None.`; `Args:` / `None.` where there are no parameters):

| Function | Location | Summary | Args |
|---|---|---|---|
| `test_ranks_every_active_product_once` | [tests/integration/test_q2_real.py:31](tests/integration/test_q2_real.py:31) | Check every active product is ranked exactly once. | `result` |
| `test_ranking_follows_tier_order` | [tests/integration/test_q2_real.py:48](tests/integration/test_q2_real.py:48) | Check the watch list is sorted by tier. | `result` |
| `test_critical_rule_holds` | [tests/integration/test_q2_real.py:62](tests/integration/test_q2_real.py:62) | Check Critical products are out of stock or under 0.5 months. | `result` |
| `test_side_tables` | [tests/integration/test_q2_real.py:76](tests/integration/test_q2_real.py:76) | Check the no-reorder-rule and discontinued-stock tables. | `result` |
| `test_suggested_levels_non_negative` | [tests/integration/test_q2_real.py:91](tests/integration/test_q2_real.py:91) | Check the three suggested reorder levels are non-negative. | `result` |
| `test_robustness_meets_plan_threshold` | [tests/integration/test_q2_real.py:106](tests/integration/test_q2_real.py:106) | Check the ranking holds under every alternative window. | `result` |
| `test_shortlist_is_top_ten` | [tests/integration/test_q2_real.py:119](tests/integration/test_q2_real.py:119) | Check the shortlist is the top ten of the watch list. | `result` |
| `test_deterministic` | [tests/integration/test_q2_real.py:134](tests/integration/test_q2_real.py:134) | Check a second run gives the same watch list. | `result` |

Args lines used by these tests:
```text
result (northwind.q2_inventory.Q2Result): Q2 results for the real workbook.
```

### tests/integration/test_q3_real.py

#### `result` — [tests/integration/test_q3_real.py:16](tests/integration/test_q3_real.py:16)
```python
"""Run Q3 on the real workbook.

Args:
    None.

Returns:
    northwind.q3_logistics.Q3Result: Q3 results, shared by the
    module.
"""
```

Test functions (each docstring is the summary below, then the Args lines for the parameters named, then `Returns:` / `None.`; `Args:` / `None.` where there are no parameters):

| Function | Location | Summary | Args |
|---|---|---|---|
| `test_overview_counts` | [tests/integration/test_q3_real.py:30](tests/integration/test_q3_real.py:30) | Check shipped, late and backlog counts against control totals. | `result` |
| `test_breakdowns_cover_every_shipped_order` | [tests/integration/test_q3_real.py:46](tests/integration/test_q3_real.py:46) | Check each breakdown covers every shipped and late order. | `result` |
| `test_opportunities_ranked_and_non_negative` | [tests/integration/test_q3_real.py:61](tests/integration/test_q3_real.py:61) | Check opportunities are positive and ranked within each type. | `result` |
| `test_regression_uses_best_carrier_as_baseline` | [tests/integration/test_q3_real.py:78](tests/integration/test_q3_real.py:78) | Check the regression, if run, covers both models and baselines. (Extended description added after review: it does not check that the baseline is the best carrier.) | `result` |
| `test_late_by_window_adds_up` | [tests/integration/test_q3_real.py:97](tests/integration/test_q3_real.py:97) | Check the late-by-window table adds up to control totals. | `result` |
| `test_no_action_recommended_on_unsupported_gaps` | [tests/integration/test_q3_real.py:111](tests/integration/test_q3_real.py:111) | Check unsupported gaps carry no action and no rate review. | `result` |
| `test_robustness_shape` | [tests/integration/test_q3_real.py:127](tests/integration/test_q3_real.py:127) | Check the robustness table has six rows of both types. | `result` |
| `test_deterministic` | [tests/integration/test_q3_real.py:141](tests/integration/test_q3_real.py:141) | Check a second run gives the same opportunities and regression. | `result` |
| `test_regression_without_slow_orders_runs_when_triggered` | [tests/integration/test_q3_real.py:157](tests/integration/test_q3_real.py:157) | Check the regression without slow orders runs when triggered. | `result` |

Args lines used by these tests:
```text
result (northwind.q3_logistics.Q3Result): Q3 results for the real workbook.
```

### tests/integration/test_real_workbook.py

#### `module` (rewritten) — [tests/integration/test_real_workbook.py:1](tests/integration/test_real_workbook.py:1)
```python
"""Integration tests: the model reproduces the real workbook's totals."""
```

#### `model` — [tests/integration/test_real_workbook.py:16](tests/integration/test_real_workbook.py:16)
```python
"""Load the model from the real workbook.

Args:
    None.

Returns:
    northwind.model.Model: Model shared by the module.
"""
```

Test functions (each docstring is the summary below, then the Args lines for the parameters named, then `Returns:` / `None.`; `Args:` / `None.` where there are no parameters):

| Function | Location | Summary | Args |
|---|---|---|---|
| `test_join_row_counts` | [tests/integration/test_real_workbook.py:28](tests/integration/test_real_workbook.py:28) | Check joined table row counts against control totals. | `model` |
| `test_no_missing_keys_after_joins` | [tests/integration/test_real_workbook.py:42](tests/integration/test_real_workbook.py:42) | Check joins leave no missing keys or looked-up names. | `model` |
| `test_revenue_control_totals` | [tests/integration/test_real_workbook.py:60](tests/integration/test_real_workbook.py:60) | Check net and gross revenue against control totals. | `model` |
| `test_order_control_totals` | [tests/integration/test_real_workbook.py:74](tests/integration/test_real_workbook.py:74) | Check order counts against control totals. | `model` |
| `test_product_control_totals` | [tests/integration/test_real_workbook.py:91](tests/integration/test_real_workbook.py:91) | Check active products and missing reorder rules. | `model` |
| `test_markets_sum_to_total` | [tests/integration/test_real_workbook.py:105](tests/integration/test_real_workbook.py:105) | Check market revenue sums to the total and has focus markets. | `model` |
| `test_every_order_in_a_size_band` | [tests/integration/test_real_workbook.py:119](tests/integration/test_real_workbook.py:119) | Check every order falls in one of four size bands. | `model` |
| `test_allowed_windows_are_standard` | [tests/integration/test_real_workbook.py:132](tests/integration/test_real_workbook.py:132) | Check allowed delivery windows are 14, 28 or 42 days. | `model` |
| `test_input_not_modified` | [tests/integration/test_real_workbook.py:144](tests/integration/test_real_workbook.py:144) | Check that loading leaves the workbook file unchanged. | `model` |

Args lines used by these tests:
```text
model (northwind.model.Model): Model of the real workbook.
```

### tests/e2e/test_pipeline.py

#### `module` (rewritten) — [tests/e2e/test_pipeline.py:1](tests/e2e/test_pipeline.py:1)
```python
"""End-to-end tests of the whole pipeline on a project copy (plan 7.3)."""
```

#### `runs` — [tests/e2e/test_pipeline.py:46](tests/e2e/test_pipeline.py:46)
```python
"""Run the pipeline twice, each in a fresh project copy.

Args:
    tmp_path_factory (pytest.TempPathFactory): Session temp-folder
        factory.

Returns:
    tuple[tuple[pathlib.Path, subprocess.CompletedProcess], ...]:
    Folder and finished run of each copy.
"""
```

#### `page` — [tests/e2e/test_pipeline.py:62](tests/e2e/test_pipeline.py:62)
```python
"""Return the page built by the first run.

Args:
    runs (tuple[tuple[pathlib.Path, subprocess.CompletedProcess],
        ...]): Folder and finished run of each of the two copies.

Returns:
    str: HTML of ``docs/index.html``.
"""
```

#### `_section` — [tests/e2e/test_pipeline.py:106](tests/e2e/test_pipeline.py:106)
```python
"""Return one question's section of the page.

Args:
    page (str): HTML of the page built by the first run.
    qid (str): Section id, ``q1`` to ``q3``.

Returns:
    str: HTML from the section's ``id`` attribute up to its
    ``</section>`` tag.
"""
```

#### `_text` — [tests/e2e/test_pipeline.py:318](tests/e2e/test_pipeline.py:318)
```python
"""Return the visible text of an HTML fragment.

Args:
    html_part (str): HTML to convert.

Returns:
    str: Text without charts or tags, whitespace collapsed and
    apostrophes unescaped.
"""
```

Test functions (each docstring is the summary below, then the Args lines for the parameters named, then `Returns:` / `None.`; `Args:` / `None.` where there are no parameters):

| Function | Location | Summary | Args |
|---|---|---|---|
| `test_pipeline_succeeds` | [tests/e2e/test_pipeline.py:76](tests/e2e/test_pipeline.py:76) | Check both runs exit cleanly and write the page and .nojekyll. | `runs` |
| `test_page_has_every_section` | [tests/e2e/test_pipeline.py:92](tests/e2e/test_pipeline.py:92) | Check the page contains every required section. | `page` |
| `test_two_titled_charts_per_question` | [tests/e2e/test_pipeline.py:121](tests/e2e/test_pipeline.py:121) | Check each question has two charts, each with a title. | `page` |
| `test_each_question_has_required_parts_in_order` | [tests/e2e/test_pipeline.py:136](tests/e2e/test_pipeline.py:136) | Check each question's parts appear in order with enough items. | `page` |
| `test_one_primary_chart_visible_per_question` | [tests/e2e/test_pipeline.py:157](tests/e2e/test_pipeline.py:157) | Check one chart, and only Q2's table, show before the details. | `page` |
| `test_shortages_are_not_called_confirmed_backorders` | [tests/e2e/test_pipeline.py:174](tests/e2e/test_pipeline.py:174) | Check shortages are described as possible, not confirmed. | `page` |
| `test_rescue_does_not_blame_a_growing_key_account` | [tests/e2e/test_pipeline.py:188](tests/e2e/test_pipeline.py:188) | Check Q1 doesn't blame a key account that grew. | `page` |
| `test_no_recommendation_to_act_on_unsupported_freight` | [tests/e2e/test_pipeline.py:202](tests/e2e/test_pipeline.py:202) | Check Q3 recommends no action on the unsupported freight gap. | `page` |
| `test_no_missing_value_text` | [tests/e2e/test_pipeline.py:217](tests/e2e/test_pipeline.py:217) | Check no NaN, None or inf text appears outside the charts. | `page` |
| `test_self_contained` | [tests/e2e/test_pipeline.py:232](tests/e2e/test_pipeline.py:232) | Check the page is self-contained, with colors only in CSS. | `page` |
| `test_charts_have_text_alternatives` | [tests/e2e/test_pipeline.py:246](tests/e2e/test_pipeline.py:246) | Check all eight charts have an image role and an aria-label. | `page` |
| `test_headline_numbers_match_tables` | [tests/e2e/test_pipeline.py:260](tests/e2e/test_pipeline.py:260) | Check headline numbers on the page match the output files. | `runs`, `page` |
| `test_deterministic_apart_from_timestamp` | [tests/e2e/test_pipeline.py:284](tests/e2e/test_pipeline.py:284) | Check both runs match apart from the build timestamp. | `runs` |
| `test_input_unchanged` | [tests/e2e/test_pipeline.py:302](tests/e2e/test_pipeline.py:302) | Check the run leaves the workbook copy unchanged. | `runs` |
| `test_q3_does_not_overstate` | [tests/e2e/test_pipeline.py:332](tests/e2e/test_pipeline.py:332) | Check Q3 avoids the overstated claims and shows uncertainty. | `page` |
| `test_q1_separates_clear_from_tentative` | [tests/e2e/test_pipeline.py:348](tests/e2e/test_pipeline.py:348) | Check Q1 labels clear and tentative results separately. | `page` |
| `test_q2_states_assumption_and_range` | [tests/e2e/test_pipeline.py:363](tests/e2e/test_pipeline.py:363) | Check Q2 states the stock-count assumption and a unit range. | `page` |
| `test_review_listed_in_appendix` | [tests/e2e/test_pipeline.py:378](tests/e2e/test_pipeline.py:378) | Check the appendix lists the independent review and its fixes. | `page` |
| `test_summary_cards_have_one_metric_finding_and_action` | [tests/e2e/test_pipeline.py:393](tests/e2e/test_pipeline.py:393) | Check each of three summary cards has one metric and one action. | `page` |
| `test_three_ranked_priorities_all_confirmed` | [tests/e2e/test_pipeline.py:411](tests/e2e/test_pipeline.py:411) | Check three ranked, confirmed priorities with distinct owners. | `page` |
| `test_q1_chart_guide_explains_axes_and_six_categories` | [tests/e2e/test_pipeline.py:427](tests/e2e/test_pipeline.py:427) | Check the Q1 chart guide explains its axes and six categories. | `page` |
| `test_q1_actions_name_an_account` | [tests/e2e/test_pipeline.py:442](tests/e2e/test_pipeline.py:442) | Check Q1's actions name an account to call. | `page` |
| `test_q2_buy_list_and_selection_rule` | [tests/e2e/test_pipeline.py:456](tests/e2e/test_pipeline.py:456) | Check the Q2 buy list has five rows and states its rule. | `page` |
| `test_glossary_explains_terms` | [tests/e2e/test_pipeline.py:474](tests/e2e/test_pipeline.py:474) | Check the glossary defines each key term. | `page` |
| `test_q1_question_wording` | [tests/e2e/test_pipeline.py:489](tests/e2e/test_pipeline.py:489) | Check Q1 uses the revised question wording. | `page` |
| `test_five_assignment_parts_visible_before_details` | [tests/e2e/test_pipeline.py:503](tests/e2e/test_pipeline.py:503) | Check each question shows the five parts before the details. | `page` |

Args lines used by these tests:
```text
runs (tuple[tuple[pathlib.Path, subprocess.CompletedProcess], ...]): Folder and finished run of each of the two copies.
page (str): HTML of the page built by the first run.
```

### Already compliant, left unchanged

| Name | Location | Summary |
|---|---|---|
| `<module>` | [northwind/__init__.py:1](northwind/__init__.py:1) | Northwind business analysis: data loading, metrics and reporting. |
| `load_model` | [northwind/__init__.py:9](northwind/__init__.py:9) | Load, clean and join the workbook in one call. |
| `<module>` | [northwind/charts.py:1](northwind/charts.py:1) | Charts for the report, rendered as themeable inline SVG. |
| `_money` | [northwind/charts.py:83](northwind/charts.py:83) | Format dollars compactly. |
| `to_svg` | [northwind/charts.py:97](northwind/charts.py:97) | Render a figure as themeable, accessible inline SVG. |
| `_hairline_grid` | [northwind/charts.py:123](northwind/charts.py:123) | Draw recessive solid hairline gridlines behind the data. |
| `_place_labels` | [northwind/charts.py:137](northwind/charts.py:137) | Label each bubble where the text doesn't overlap other labels. |
| `q1_matrix` | [northwind/charts.py:176](northwind/charts.py:176) | Draw the main Q1 chart: share change against concentration. |
| `q1_movers` | [northwind/charts.py:239](northwind/charts.py:239) | Draw the supporting Q1 chart: biggest account changes. |
| `q1_quarterly` | [northwind/charts.py:284](northwind/charts.py:284) | Draw each market's share of company revenue by quarter. |
| `q2_urgency` | [northwind/charts.py:324](northwind/charts.py:324) | Draw the main Q2 chart: demand against months of stock. |
| `q2_gap` | [northwind/charts.py:368](northwind/charts.py:368) | Draw the supporting Q2 chart: stock against one month of demand. |
| `q3_opportunities` | [northwind/charts.py:411](northwind/charts.py:411) | Draw the supporting Q3 chart: dispatch time lost by group. |
| `q3_deadlines` | [northwind/charts.py:446](northwind/charts.py:446) | Draw the main Q3 chart: late-dispatch rate by allowed window. |
| `q3_processing_by_carrier` | [northwind/charts.py:476](northwind/charts.py:476) | Draw the distribution of processing days by carrier. |
| `all_charts` | [northwind/charts.py:503](northwind/charts.py:503) | Render every chart used on the page. |
| `<module>` | [northwind/clean.py:1](northwind/clean.py:1) | Apply the cleaning rules from plan.md section 2.3. |
| `clean_tables` | [northwind/clean.py:16](northwind/clean.py:16) | Return cleaned copies of the workbook sheets. |
| `<module>` | [northwind/config.py:1](northwind/config.py:1) | Paths, dates, thresholds and region maps used by every analysis step. |
| `Config` | [northwind/config.py:80](northwind/config.py:80) | Settings for one analysis run. |
| `<module>` | [northwind/load.py:1](northwind/load.py:1) | Read the Northwind workbook and check it has the expected structure. |
| `SchemaError` | [northwind/load.py:26](northwind/load.py:26) | Raised when the workbook lacks a required sheet or column. |
| `file_sha256` | [northwind/load.py:30](northwind/load.py:30) | Return the SHA-256 fingerprint of a file. |
| `validate_schema` | [northwind/load.py:46](northwind/load.py:46) | Check that every required sheet and column is present. |
| `load_workbook` | [northwind/load.py:68](northwind/load.py:68) | Read all sheets of the workbook and validate their structure. |
| `<module>` | [northwind/metrics.py:1](northwind/metrics.py:1) | Metric definitions from plan.md section 3, each coded once. |
| `map_regions` | [northwind/metrics.py:13](northwind/metrics.py:13) | Map each country to its group. |
| `quarter_of` | [northwind/metrics.py:32](northwind/metrics.py:32) | Return the calendar quarter of each date. |
| `gross_revenue` | [northwind/metrics.py:46](northwind/metrics.py:46) | Return revenue before discount for each order line. |
| `net_revenue` | [northwind/metrics.py:59](northwind/metrics.py:59) | Return revenue after discount for each order line. |
| `window_growth` | [northwind/metrics.py:75](northwind/metrics.py:75) | Return the relative change between two revenue windows. |
| `decompose_change` | [northwind/metrics.py:90](northwind/metrics.py:90) | Split a revenue change into order-count and order-size effects. |
| `account_contributions` | [northwind/metrics.py:119](northwind/metrics.py:119) | Return each customer's change in revenue between two windows. |
| `top_share` | [northwind/metrics.py:137](northwind/metrics.py:137) | Return the largest value's share of the total. |
| `top_share_of_increase` | [northwind/metrics.py:153](northwind/metrics.py:153) | Return the largest account gain as a share of the net increase. |
| `relative_growth` | [northwind/metrics.py:193](northwind/metrics.py:193) | Return the change in a market's share of company revenue. |
| `performance_level` | [northwind/metrics.py:211](northwind/metrics.py:211) | Classify relative growth as Outperforming, In line or Underperforming. |
| `concentration_risk` | [northwind/metrics.py:230](northwind/metrics.py:230) | Classify dependence on the largest customer as High or Low. |
| `near_concentration_line` | [northwind/metrics.py:243](northwind/metrics.py:243) | Flag dependence close to the concentration threshold. |
| `narrow_growth` | [northwind/metrics.py:259](northwind/metrics.py:259) | Flag growth supplied mostly by one account. |
| `recommended_action` | [northwind/metrics.py:273](northwind/metrics.py:273) | Map performance and concentration risk to a recommended action. |
| `recent_monthly_demand` | [northwind/metrics.py:295](northwind/metrics.py:295) | Return units ordered per month over the recent window, per product. |
| `longrun_monthly_demand` | [northwind/metrics.py:318](northwind/metrics.py:318) | Return units ordered per month since each product's first sale. |
| `demand_variability` | [northwind/metrics.py:336](northwind/metrics.py:336) | Return the coefficient of variation of monthly units per product. |
| `months_of_cover` | [northwind/metrics.py:367](northwind/metrics.py:367) | Return how many months stock lasts at the given demand. |
| `risk_tier` | [northwind/metrics.py:382](northwind/metrics.py:382) | Assign each product a restocking risk tier (plan 3.4). |
| `processing_days` | [northwind/metrics.py:415](northwind/metrics.py:415) | Return days from order to dispatch. |
| `slack_days` | [northwind/metrics.py:429](northwind/metrics.py:429) | Return days between dispatch and the customer's required date. |
| `is_late` | [northwind/metrics.py:444](northwind/metrics.py:444) | Flag orders dispatched after the required date. |
| `freight_per_unit` | [northwind/metrics.py:458](northwind/metrics.py:458) | Return freight cost per unit shipped. |
| `freight_share` | [northwind/metrics.py:471](northwind/metrics.py:471) | Return freight as a share of order net revenue. |
| `size_band_edges` | [northwind/metrics.py:484](northwind/metrics.py:484) | Return quartile edges of order size. |
| `assign_size_band` | [northwind/metrics.py:503](northwind/metrics.py:503) | Label each order with its size band. |
| `excess_over_benchmark` | [northwind/metrics.py:521](northwind/metrics.py:521) | Return the total amount by which values exceed a benchmark. |
| `<module>` | [northwind/model.py:1](northwind/model.py:1) | Build the order-line, order and product tables (plan.md section 2.2). |
| `ModelError` | [northwind/model.py:11](northwind/model.py:11) | Raised when a join changes row counts or leaves keys unmatched. |
| `Model` | [northwind/model.py:16](northwind/model.py:16) | Joined, analysis-ready tables. |
| `_join` | [northwind/model.py:34](northwind/model.py:34) | Left-join many-to-one and check nothing was lost or left unmatched. |
| `build_model` | [northwind/model.py:61](northwind/model.py:61) | Join the cleaned sheets into the three analysis tables. |
| `<module>` | [northwind/q1_markets.py:1](northwind/q1_markets.py:1) | Q1: rate markets on share change and customer concentration. |
| `Q1Result` | [northwind/q1_markets.py:26](northwind/q1_markets.py:26) | Outputs of the Q1 market analysis. |
| `prepare_lines` | [northwind/q1_markets.py:64](northwind/q1_markets.py:64) | Return order lines with the market each one belongs to. |
| `_in_quarters` | [northwind/q1_markets.py:90](northwind/q1_markets.py:90) | Return the lines whose quarter is in ``quarters``. |
| `_full_quarters` | [northwind/q1_markets.py:103](northwind/q1_markets.py:103) | Return the complete quarters in the analysis period. |
| `_latest_four` | [northwind/q1_markets.py:116](northwind/q1_markets.py:116) | Return the four most recent complete quarters. |
| `quarterly_table` | [northwind/q1_markets.py:130](northwind/q1_markets.py:130) | Return revenue, orders, customers and share per market and quarter. |
| `_trend` | [northwind/q1_markets.py:157](northwind/q1_markets.py:157) | Return a linear trend per period as a share of the average level. |
| `_sign` | [northwind/q1_markets.py:174](northwind/q1_markets.py:174) | Return -1, 0 or 1; 0 for NaN. |
| `scorecard` | [northwind/q1_markets.py:186](northwind/q1_markets.py:186) | Score every market on relative performance and concentration. |
| `needs_bootstrap` | [northwind/q1_markets.py:312](northwind/q1_markets.py:312) | Decide whether a market meets a plan 4.4 trigger. |
| `bootstrap_relative_growth` | [northwind/q1_markets.py:333](northwind/q1_markets.py:333) | Return a bootstrap interval for a market's relative growth. |
| `performance_confidence` | [northwind/q1_markets.py:366](northwind/q1_markets.py:366) | Add PerformanceConfidence and FlagNotConclusive to the scorecard. |
| `uncertainty_table` | [northwind/q1_markets.py:406](northwind/q1_markets.py:406) | Return relative-growth intervals for every market (appendix). |
| `robustness` | [northwind/q1_markets.py:434](northwind/q1_markets.py:434) | Recompute performance levels under three alternative definitions. |
| `window_check` | [northwind/q1_markets.py:469](northwind/q1_markets.py:469) | Check whether each market's share moved the same way in other periods. |
| `_money` | [northwind/q1_markets.py:504](northwind/q1_markets.py:504) | Format dollars compactly, e.g. $12.3K. |
| `flag_list` | [northwind/q1_markets.py:516](northwind/q1_markets.py:516) | Return the warning flags raised for one market. |
| `summarise` | [northwind/q1_markets.py:539](northwind/q1_markets.py:539) | Write one plain-language recommendation per market. |
| `run` | [northwind/q1_markets.py:576](northwind/q1_markets.py:576) | Run the full Q1 analysis. |
| `<module>` | [northwind/q2_inventory.py:1](northwind/q2_inventory.py:1) | Q2: rank active products for restocking. |
| `Q2Result` | [northwind/q2_inventory.py:22](northwind/q2_inventory.py:22) | Outputs of the Q2 restocking analysis. |
| `_reorder_column` | [northwind/q2_inventory.py:53](northwind/q2_inventory.py:53) | Return the column name for a suggested reorder level. |
| `average_net_price` | [northwind/q2_inventory.py:65](northwind/q2_inventory.py:65) | Return average net price per unit for each product. |
| `average_net_price.per_unit` | [northwind/q2_inventory.py:83](northwind/q2_inventory.py:83) | Return net revenue per unit for each product. |
| `pending_units` | [northwind/q2_inventory.py:98](northwind/q2_inventory.py:98) | Return units on orders that have not been shipped, per product. |
| `restock_action` | [northwind/q2_inventory.py:111](northwind/q2_inventory.py:111) | Return the recommended purchasing action for one product. |
| `assess_products` | [northwind/q2_inventory.py:136](northwind/q2_inventory.py:136) | Compute demand, stock cover, tier and action for every product. |
| `rank` | [northwind/q2_inventory.py:178](northwind/q2_inventory.py:178) | Order products by tier, then by monthly revenue at stake. |
| `robustness` | [northwind/q2_inventory.py:193](northwind/q2_inventory.py:193) | Check whether Critical/High products stay there with other windows. |
| `headline` | [northwind/q2_inventory.py:221](northwind/q2_inventory.py:221) | State the catalogue-wide stock finding in one sentence. |
| `run` | [northwind/q2_inventory.py:241](northwind/q2_inventory.py:241) | Run the full Q2 analysis. |
| `<module>` | [northwind/q3_logistics.py:1](northwind/q3_logistics.py:1) | Q3: compare processing time and freight across shipments. |
| `Q3Result` | [northwind/q3_logistics.py:34](northwind/q3_logistics.py:34) | Outputs of the Q3 logistics analysis. |
| `shipped_orders` | [northwind/q3_logistics.py:81](northwind/q3_logistics.py:81) | Return shipped orders with a slow-order flag. |
| `breakdown` | [northwind/q3_logistics.py:97](northwind/q3_logistics.py:97) | Summarise processing and freight for each value of one column. |
| `within_bands` | [northwind/q3_logistics.py:125](northwind/q3_logistics.py:125) | Return medians for each group within each size band. |
| `group_gaps` | [northwind/q3_logistics.py:146](northwind/q3_logistics.py:146) | Size each group's gap against a benchmark within each size band. |
| `opportunities` | [northwind/q3_logistics.py:205](northwind/q3_logistics.py:205) | Collect processing and freight opportunities across dimensions. |
| `backlog` | [northwind/q3_logistics.py:248](northwind/q3_logistics.py:248) | Summarise orders that were never shipped. |
| `consolidation` | [northwind/q3_logistics.py:272](northwind/q3_logistics.py:272) | Size the small-order consolidation opportunity (plan 3.7). |
| `late_by_window` | [northwind/q3_logistics.py:292](northwind/q3_logistics.py:292) | Count late dispatches by the customer's allowed window. |
| `region_mix_gap` | [northwind/q3_logistics.py:309](northwind/q3_logistics.py:309) | Return the largest gap between carriers in any destination's share. |
| `ols_hc1` | [northwind/q3_logistics.py:323](northwind/q3_logistics.py:323) | Fit ordinary least squares with HC1 robust standard errors. |
| `_design` | [northwind/q3_logistics.py:343](northwind/q3_logistics.py:343) | Build a design matrix with an intercept and dummy variables. |
| `carrier_regression` | [northwind/q3_logistics.py:369](northwind/q3_logistics.py:369) | Estimate carrier effects on freight and dispatch time (plan 4.4). |
| `apply_adjustment` | [northwind/q3_logistics.py:419](northwind/q3_logistics.py:419) | Mark carrier opportunities as supported or not by the regression. |
| `deadline_priority` | [northwind/q3_logistics.py:449](northwind/q3_logistics.py:449) | Check whether short-deadline orders are processed faster. |
| `regression_trigger` | [northwind/q3_logistics.py:472](northwind/q3_logistics.py:472) | Decide whether the carrier regression is needed (plan 4.4). |
| `flag_small_opportunities` | [northwind/q3_logistics.py:493](northwind/q3_logistics.py:493) | Add a confidence column; bootstrap opportunities on few orders. |
| `robustness` | [northwind/q3_logistics.py:530](northwind/q3_logistics.py:530) | Check whether the top 3 opportunities of each type stay in the top 5. |
| `run` | [northwind/q3_logistics.py:568](northwind/q3_logistics.py:568) | Run the full Q3 analysis. |
| `<module>` | [northwind/report.py:1](northwind/report.py:1) | Assemble the self-contained HTML report (plan.md section 5). |
| `pct` | [northwind/report.py:21](northwind/report.py:21) | Format a fraction as a percentage. |
| `money` | [northwind/report.py:38](northwind/report.py:38) | Format dollars compactly. |
| `num` | [northwind/report.py:55](northwind/report.py:55) | Format a number with thousands separators. |
| `table` | [northwind/report.py:68](northwind/report.py:68) | Build table data for the template. |
| `join_names` | [northwind/report.py:87](northwind/report.py:87) | Join names as plain English: "A", "A and B", "A, B and C". |
| `q1_section` | [northwind/report.py:104](northwind/report.py:104) | Build the Q1 section context. |
| `q1_section.flags` | [northwind/report.py:131](northwind/report.py:131) | Return the flag labels for one market, or a dash. |
| `q1_section.tentative` | [northwind/report.py:169](northwind/report.py:169) | Say whether a market's action should be marked tentative. |
| `market_action` | [northwind/report.py:230](northwind/report.py:230) | Write one specific action for a market: who to contact and why. |
| `metrics_text` | [northwind/report.py:265](northwind/report.py:265) | Return the generic description of an action. |
| `rescue_detail` | [northwind/report.py:277](northwind/report.py:277) | Explain a Rescue market from the data rather than assuming the cause. |
| `q1_interpretation` | [northwind/report.py:321](northwind/report.py:321) | Turn the Q1 results into business implications, one per market group. |
| `q1_interpretation.biggest` | [northwind/report.py:333](northwind/report.py:333) | Return the account with the largest change in one direction. |
| `q1_interpretation.share` | [northwind/report.py:349](northwind/report.py:349) | Return a market's share of revenue before and after. |
| `shortfall_range` | [northwind/report.py:400](northwind/report.py:400) | Return the top products' shortfall to one month of demand. |
| `q2_interpretation` | [northwind/report.py:417](northwind/report.py:417) | Turn the Q2 results into business implications. |
| `wilson` | [northwind/report.py:450](northwind/report.py:450) | Return the Wilson 95% interval for a proportion. |
| `q3_facts` | [northwind/report.py:469](northwind/report.py:469) | Collect the Q3 figures the page text is built from. |
| `q3_interpretation` | [northwind/report.py:511](northwind/report.py:511) | Turn the Q3 results into business implications. |
| `q1_flag_text` | [northwind/report.py:555](northwind/report.py:555) | Return short flag labels for one Q1 market. |
| `q2_section` | [northwind/report.py:574](northwind/report.py:574) | Build the Q2 section context. |
| `buy_list` | [northwind/report.py:637](northwind/report.py:637) | Return the top products with how many units to order. |
| `q3_actions` | [northwind/report.py:659](northwind/report.py:659) | Write the Q3 actions, each naming what to look at first. |
| `q3_section` | [northwind/report.py:681](northwind/report.py:681) | Build the Q3 section context. |
| `_regression_text` | [northwind/report.py:737](northwind/report.py:737) | Add formatted effect and interval columns to the regression table. |
| `_regression_text.fmt` | [northwind/report.py:746](northwind/report.py:746) | Format a regression effect in its model's unit. |
| `appendix` | [northwind/report.py:764](northwind/report.py:764) | Build the appendix context. |
| `load_review` | [northwind/report.py:870](northwind/report.py:870) | Read the independent review's objections and resolutions, if any. |
| `summary_cards` | [northwind/report.py:889](northwind/report.py:889) | Build the summary cards and the ranked management priorities. |
| `build_context` | [northwind/report.py:961](northwind/report.py:961) | Assemble everything the template needs. |
| `render` | [northwind/report.py:997](northwind/report.py:997) | Render the report HTML. |
| `write_site` | [northwind/report.py:1011](northwind/report.py:1011) | Write the page for GitHub Pages. |
| `<module>` | [run_analysis.py:1](run_analysis.py:1) | Build every output from the workbook. |
| `write_table` | [run_analysis.py:21](run_analysis.py:21) | Write a table as UTF-8 CSV, creating the folder if needed. |
| `main` | [run_analysis.py:35](run_analysis.py:35) | Run the pipeline and write tables and the run manifest. |
| `<module>` | [verification/check_docstrings.py:1](verification/check_docstrings.py:1) | Check docstrings against the course SKILL.md rules. |
| `_params` | [verification/check_docstrings.py:32](verification/check_docstrings.py:32) | Return a function's parameter names in signature order. |
| `_documented_args` | [verification/check_docstrings.py:52](verification/check_docstrings.py:52) | Return parameter names listed in a Google-style Args section. |
| `check_node` | [verification/check_docstrings.py:85](verification/check_docstrings.py:85) | Check one module, class or function docstring. |
| `main` | [verification/check_docstrings.py:127](verification/check_docstrings.py:127) | Check every Python file under the given paths. |
| `<module>` | [verification/check_public_site.py:1](verification/check_public_site.py:1) | Check the published page and repository anonymously. |
| `fetch` | [verification/check_public_site.py:36](verification/check_public_site.py:36) | Fetch a URL anonymously. |
| `main` | [verification/check_public_site.py:56](verification/check_public_site.py:56) | Run every check, print a report and save it. |
| `main.record` | [verification/check_public_site.py:67](verification/check_public_site.py:67) | Add one check result. |
| `<module>` | [verification/check_site_current.py:1](verification/check_site_current.py:1) | Check that the committed page matches a fresh build (used by CI). |
| `normalise` | [verification/check_site_current.py:26](verification/check_site_current.py:26) | Reduce a page to the parts that must match exactly. |
| `main` | [verification/check_site_current.py:41](verification/check_site_current.py:41) | Compare the built page with the committed one. |
| `<module>` | [verification/sql_crosscheck.py:1](verification/sql_crosscheck.py:1) | Recalculate headline figures in SQL and compare with the model. |
| `load_into_sqlite` | [verification/sql_crosscheck.py:29](verification/sql_crosscheck.py:29) | Copy the needed sheets into an in-memory SQLite database. |
| `product_checks` | [verification/sql_crosscheck.py:139](verification/sql_crosscheck.py:139) | Recompute recent demand and risk tier per active product in SQL. |
| `logistics_checks` | [verification/sql_crosscheck.py:223](verification/sql_crosscheck.py:223) | Recompute carrier medians and opportunities per size band in SQL. |
| `pandas_figures` | [verification/sql_crosscheck.py:255](verification/sql_crosscheck.py:255) | Compute the same figures from the pandas model. |
| `compare` | [verification/sql_crosscheck.py:283](verification/sql_crosscheck.py:283) | Compare one figure from each path. |
| `market_checks` | [verification/sql_crosscheck.py:317](verification/sql_crosscheck.py:317) | Recompute Q1 window revenue and growth per market in SQL. |
| `run_checks` | [verification/sql_crosscheck.py:351](verification/sql_crosscheck.py:351) | Run every cross-check and save the results as JSON. |
| `main` | [verification/sql_crosscheck.py:386](verification/sql_crosscheck.py:386) | Run the cross-check and print a report. |
| `<module>` | [tests/conftest.py:1](tests/conftest.py:1) | Shared fixtures: a small made-up workbook with known answers. |
| `synthetic_sheets` | [tests/conftest.py:23](tests/conftest.py:23) | Return the eight sheets of a tiny Northwind-shaped workbook. |
| `<module>` | [tests/unit/test_load_clean.py:1](tests/unit/test_load_clean.py:1) | Unit tests for loading and cleaning. |
| `<module>` | [tests/unit/test_metrics.py:1](tests/unit/test_metrics.py:1) | Unit tests for the metric definitions in plan.md section 3. |
| `<module>` | [tests/unit/test_model.py:1](tests/unit/test_model.py:1) | Unit tests for the joined model, using the synthetic workbook. |
| `<module>` | [tests/unit/test_q1_markets.py:1](tests/unit/test_q1_markets.py:1) | Unit tests for the Q1 market analysis on hand-built order lines. |
| `<module>` | [tests/unit/test_q3_logistics.py:1](tests/unit/test_q3_logistics.py:1) | Unit tests for the Q3 logistics analysis. |
| `<module>` | [tests/unit/test_report.py:1](tests/unit/test_report.py:1) | Unit tests for report wording that must follow the data. |
| `<module>` | [tests/integration/test_q1_real.py:1](tests/integration/test_q1_real.py:1) | Integration tests for Q1 on the real workbook. |
| `<module>` | [tests/integration/test_q2_real.py:1](tests/integration/test_q2_real.py:1) | Integration tests for Q2 on the real workbook. |
| `<module>` | [tests/integration/test_q3_real.py:1](tests/integration/test_q3_real.py:1) | Integration tests for Q3 on the real workbook. |
| `_run_copy` | [tests/e2e/test_pipeline.py:26](tests/e2e/test_pipeline.py:26) | Copy the project into ``dest`` and run the pipeline there. |

## Assumptions to check

1. `test_decomposition_adds_up_exactly` / `r0`, `o0`, `r1`, `o1`: assumed
   prior revenue, prior orders, current revenue and current orders. They
   are passed positionally to `metrics.decompose_change(rev_prior,
   orders_prior, rev_current, orders_current)`.
2. `_tier` and `test_risk_tier_rules` / `reorder`: documented as the
   reorder level with 0 meaning no reorder rule. It is passed as
   `reorder_level` to `metrics.risk_tier`, whose docstring says so, and the
   test comments say "no reorder rule" for the 0 cases.
3. `_tier` and `test_risk_tier_rules` / `demand`, `cv`: documented as
   recent monthly demand in units and its coefficient of variation. They
   map to `monthly_demand` and `variability` in `metrics.risk_tier`.
4. `_orders` (test_q3_logistics) / `groups`: each value is documented as
   both the processing days and the freight per unit of one order, because
   the helper copies it into both columns.
5. `scored` fixture (test_q1_markets): company totals documented as a
   `dict`, following `q1_markets.scorecard`'s Returns section.
6. `runs` fixture (e2e): documented as two (folder, finished process)
   pairs, from `return (first, _run_copy(first)), (second, ...)`.
7. `test_regression_uses_best_carrier_as_baseline`: `regression_reason is
   None` is read as "the regression did not run", because `run()` sets
   `regression` to an empty table whenever there is no reason
   (`q3_logistics.py`, `regression = carrier_regression(...) if reason
   else pd.DataFrame()`). Corrected after review: the test's docstring
   now says it checks that both models are present, that each carrier is
   compared with a different baseline carrier, and that each effect lies
   inside its interval. It does not check that the baseline is the best
   carrier. (The baseline is the lowest median freight per unit for the
   freight model and the lowest mean processing days for the dispatch
   model, per `carrier_regression`.) The `Q3Result.regression_reason`
   docstring now also says None means it didn't run.
8. `result` and `model` fixtures in the integration tests: documented as
   shared by the module because they use `scope="module"`.
9. `synthetic_model` fixture: documented with a cutoff of 6 May 1998,
   from `Config(cutoff=pd.Timestamp("1998-05-06"))` in its body.

Carried over from the earlier pass (these docstrings were not changed now):

10. `metrics.top_share_of_increase`: documented as able to exceed 1,
    because a single account's gain can exceed a market's net increase
    when other accounts fell (`max / sum` with no cap).
11. `metrics.risk_tier`: products with no recent demand are documented as
    "No recent demand" even when out of stock, because that condition is
    checked first.
12. `metrics.recent_monthly_demand`: the 90-day window is documented as
    inclusive at both ends (6 Feb–6 May 1998), matching `>=` and `<=`.
13. `metrics.demand_variability`: documented as using the population
    standard deviation (`ddof=0`), with zero-sales months counted.
14. `q2_inventory.average_net_price`: products with no sales in the
    window fall back to their all-time average, via `combine_first`.
15. `q3_logistics.group_gaps`: when several groups tie for the lowest
    median, the first in alphabetical order is the benchmark, because
    `idxmin` returns the first label.
16. Freight (corrected after review): no docstring says who pays.
    `metrics.freight_per_unit` and `metrics.freight_share` describe
    `Freight` as "freight cost" or "freight per order" only. The
    assumption that freight is a cost to Northwind is stated in the
    page caveat (`q3_logistics.CAVEAT`) and the plan, not in a
    docstring, because the data doesn't say who pays.
17. `q2_inventory.assess_products` `FlagPossibleShortage`: documented as a
    screening flag, not a confirmed backorder.

## Also noticed

- `test_q3_real.test_regression_uses_best_carrier_as_baseline`: the name
  says "best carrier", but the test doesn't check that; only its
  docstring was corrected (names are left unchanged).
- `test_q1_real.test_quarterly_table_matches_total_revenue` calls
  `load_model()` again instead of reusing the module's data, which only
  costs time.
- `test_q3_real.test_regression_without_slow_orders_runs_when_triggered`
  only checks that the carriers' slow-order shares don't sum to zero, a
  weak check of that table.
- `test_metrics.test_account_contributions_sum_to_change` compares dicts,
  so it doesn't check the sort order `account_contributions` produces.
- `q1_markets.summarise` (carried over) produces per-market sentences the
  page no longer shows; it is kept for the console and tests.

Reply with numbered corrections (for example "2: 0 means unlimited") or ask for any docstring to be rewritten.
