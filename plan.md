# Northwind Analysis Plan

**Status:** Revision 3. Gates 0–6 approved. Gate 7 done: published at https://alamergt.github.io/northwind-analysis/ (repository https://github.com/alamergt/northwind-analysis); awaiting the owner's private-window check.
**Input:** `Northwind Database.xlsx` (8 sheets, read-only)
**Audience:** a manager who wants to understand the organization and act on the findings
**Deliverables:**
1. A **public webpage** (GitHub Pages) answering three business questions.
2. A **public GitHub repository** with reproducible Python code, tests and verification.

**Changes in revision 2**
- The page is now published as a public GitHub Pages site backed by a public GitHub repository. This replaces the private artifact.
- The analysis uses descriptive comparisons by default. Advanced statistics are used only when a specific condition says they would change the business conclusion (§4.4).
- Each question gets **one main chart and one supporting chart**. Technical detail moves to an appendix.
- Q3 is reworded to cover logistics efficiency more broadly.
- A check of the public URL in a private (incognito) browser window and a fresh-clone reproduction test are added.

**Question 1 wording (after publication review):** Q1 is now phrased as *How should Northwind prioritize its sales markets based on revenue performance and customer concentration risk?* The analysis, charts, findings and recommendations are unchanged, because they already answer it. Each question also now shows a short, visible *Analytical approach* paragraph right before its main chart.

**Changes in revision 3 (Q1 only)**
- The single Q1 label is replaced by two separate measures: **relative performance** (how a market's share of company revenue changed) and **concentration risk** (how much of the market depends on its largest customer). Together they map to one of six **recommended actions**.
- Actions are recommendations to discuss, not final decisions.
- There's no "Medium" concentration level. Markets within 5 percentage points of the 50% concentration line are flagged instead.
- Reason for the change: the whole company grew 80%, so fixed growth thresholds labelled a +152% market "Maintain" and a market losing share "Maintain". Mixing performance and risk into one label also hid the strongest performer (Germany) behind "Investigate".

---

## 0. Overview

### The three approved questions

| # | Question | Who decides |
|---|---|---|
| Q1 | How should Northwind prioritize its sales markets based on revenue performance and customer concentration risk? | Sales leadership (VP Sales, Sales Manager) |
| Q2 | Which active products should purchasing restock first, given current stock relative to recent demand and what's already on order? | Purchasing / operations |
| Q3 | How do order processing times and freight costs vary across shipments, and where are the greatest opportunities to improve logistics efficiency? | Operations / logistics |

### Scope
- **Orders:** 830 orders and 2,155 order lines, from **4 Jul 1996 to 6 May 1998**.
- **Analysis cutoff:** the last order date, **6 May 1998**. All "recent" windows end here, never on today's date.
- **Full calendar quarters:** Q3 1996 to Q1 1998. Q2 1998 has only 36 days and is shown separately as incomplete.

### Main caveats (repeated wherever they apply)
1. 1996 and 1998 are part-years, so calendar-year totals are never compared directly.
2. Most countries average about 1 order per month. Trends are reported only for markets with enough orders.
3. Only 5 customers placed their first order after mid-1997, so changes in revenue come from existing accounts.
4. The stock snapshot has no date and there are no supplier lead times. Q2 produces a priority list, not a forecast.
5. `ShippedDate` is the day Northwind dispatched the order, not the day it was delivered. "Processing time" in Q3 means order-to-dispatch, which Northwind controls. Delivery performance can't be measured.
6. There are no product costs, so all results are about revenue, not profit.

---

## 1. Goals and management decisions

### Q1: Market performance
- **Goal:** identify which markets are gaining or losing ground relative to the company, how much each depends on one customer, and why.
- **Decision:** where sales leadership puts its attention. Each market gets a **recommended action** (one of six, §3.2) for management to discuss. The analysis informs the decision; it doesn't make it.
- **A useful answer:** a market scorecard showing growth compared with the company, what drove the change (number of orders vs order size), the accounts that moved most, dependence on the largest customer, the recommended action, and any warning flags.
- **What the data can support:** individual trends for USA, Germany, Brazil and France. Other countries are grouped by region.
- **What it can't support:** forecasts, trends for small single countries, or conclusions about winning new customers.

### Q2: Restocking priorities
- **Goal:** rank active products by how soon stock is likely to run short.
- **Decision:** which products purchasing reorders or speeds up first, and which reorder levels need resetting.
- **A useful answer:** a ranked watch list with a risk tier and a recommended action for each product, plus the 16 active products with no reorder rule.
- **What the data can support:** comparing current stock and on-order quantities with recent demand.
- **What it can't support:** a date when stock runs out, or a history of past stockouts.

### Q3: Logistics efficiency
- **Goal:** describe how processing time (order to dispatch) and freight cost vary by carrier, destination, order size, the employee handling the order, and over time. Then find where the biggest improvements are.
- **Decision:** which 2 or 3 logistics improvements operations should pursue first. Typical examples:
  - speed up processing for a slow group of orders;
  - consolidate small, high-freight orders;
  - review freight terms for costly destinations;
  - clear the 21 unshipped orders.
- **A useful answer:** a ranked list of opportunities, each with its size (dispatch days or freight dollars that would be saved if the group matched a realistic benchmark), how many orders it affects, and a suggested action.
- **What the data can support:** processing days, days of slack before the required date, late dispatches, unshipped orders, and freight per order, per unit and as a share of order revenue.
- **What it can't support:** delivery times, or who pays the freight (assumed to be a cost to Northwind, and flagged as an assumption).

---

## 2. Data: tables, joins and cleaning

### 2.1 Sheets and columns used

| Sheet | Rows | Columns used | Used by |
|---|---|---|---|
| Orders Details | 2,155 | OrderID, ProductID, UnitPrice, Quantity, Discount | Q1, Q2, Q3 |
| Orders | 830 | OrderID, CustomerID, EmployeeID, OrderDate, RequiredDate, ShippedDate, ShipVia, Freight, ShipCountry | Q1, Q2, Q3 |
| Customers | 91 | CustomerID, CompanyName, Country | Q1 |
| Product | 77 | ProductID, ProductName, SupplierID, CategoryID, UnitsInStock, UnitsOnOrder, ReorderLevel, Discontinued | Q2 |
| Categories | 8 | CategoryID, CategoryName | Q2 |
| Suppliers | 29 | SupplierID, CompanyName, Country | Q2 (context only) |
| Shippers | 3 | ShipperID, CompanyName | Q3 |
| Employees | 9 | EmployeeID, FirstName, LastName | Q3 |

### 2.2 Joins

```
Orders Details ──OrderID──▶ Orders ──CustomerID──▶ Customers
      │                       ├──EmployeeID──▶ Employees
      │                       └──ShipVia = ShipperID──▶ Shippers
      └──ProductID──▶ Product ──CategoryID──▶ Categories
                              └──SupplierID──▶ Suppliers
```

All joins are many-to-one left joins. Each one must keep the row count unchanged and leave no unmatched keys (all of this was checked during inspection).

| Derived table | Grain | Expected rows | Built from |
|---|---|---|---|
| `order_lines` | one product line on an order | 2,155 | Details + Orders + Customers + Product + Categories |
| `orders` | one order | 830 | Orders + summed lines (units, net revenue, number of lines) + Shippers + Customers + Employees |
| `products` | one product | 77 (69 active) | Product + Categories + Suppliers + demand measures |

**Control totals** (the integration tests fail if any of these don't match):
- Net revenue ≈ **$1,265,793** and gross revenue ≈ **$1,354,459**, both to the nearest dollar.
- Orders: 830 (809 shipped, 21 not shipped). Customers who ordered: 89.

### 2.3 Cleaning rules
1. **Round discounts** to 2 decimals. They're stored as numbers like 0.0499999.
2. **Use the price on each order line** (`Orders Details.UnitPrice`) for all revenue. `Product.Price` is today's list price, about 25% higher than what was charged in 1996 and part of 1997, so it's never used for revenue.
3. **Drop the leftover Product columns:** `Cheap`, `Cheap.1`, `IsCheap`, `NewPrice`, `NewPrice.1`, `Unnamed: 14`, and the empty `Categories.Picture`.
4. **Parse dates** and keep missing `ShippedDate` values as missing. They mean "not shipped", not zero.
5. **Market of an order** is the customer's country for Q1. For Q3 it's the ship-to country, because freight depends on the physical destination. The two differ on 4 orders, and §8 checks that this doesn't change the results.
6. **Keep text exactly as stored.** Accented names are fine; they only display oddly in the Windows console.
7. **Customers with no orders** (FISSA, PARIS) are kept in the customer list and excluded from revenue measures.

### 2.4 Region groups

**Q1 markets**

| Group | Countries |
|---|---|
| USA, Germany, Brazil, France | each analyzed on its own (focus markets) |
| UK & Ireland | UK, Ireland |
| Nordics | Sweden, Denmark, Finland, Norway |
| Central Europe | Austria, Switzerland, Belgium, Poland |
| Southern Europe | Spain, Italy, Portugal |
| Other North America | Canada, Mexico |
| Other South America | Venezuela, Argentina |

**Q3 destination regions** (fewer, larger groups, since freight comparisons need enough orders in each)

| Region | Countries |
|---|---|
| North America | USA, Canada, Mexico |
| South America | Brazil, Venezuela, Argentina |
| Western Europe | Germany, France, Belgium, Switzerland, Austria |
| UK & Ireland | UK, Ireland |
| Nordics | Sweden, Denmark, Finland, Norway |
| Southern & Eastern Europe | Spain, Italy, Portugal, Poland |

A unit test checks that all 21 countries map to exactly one group in each scheme.

---

## 3. Metric definitions

Each definition is coded once in `northwind/metrics.py` and used everywhere else.

### 3.1 Revenue
| Measure | Formula | Notes |
|---|---|---|
| Net revenue per line | `UnitPrice × Quantity × (1 − Discount)` | The main revenue measure |
| Gross revenue per line | `UnitPrice × Quantity` | Used only to show how much discounts cost |
| Order revenue | sum of net revenue over the order's lines | Freight is **not** included |
| Average order value | net revenue ÷ number of orders | |
| Time period | the quarter of `OrderDate` | Revenue counts when the order is placed, not when it ships |

**Edge cases:** unshipped orders still count as revenue. Q2 1998 is incomplete and is never compared with a full quarter.

### 3.2 Market performance and concentration (Q1)

**Windows**
- **Growth:** the latest two full quarters (Q4 1997 + Q1 1998) compared with the same two quarters a year earlier (Q4 1996 + Q1 1997). Shown for context.

**Dimension 1: relative performance**
- **Share of company revenue:** the market's revenue ÷ company revenue in the same window.
- **Relative growth:** `share in later window ÷ share in earlier window − 1`. This equals `(1 + market growth) ÷ (1 + company growth) − 1`. A market growing exactly as fast as the company scores 0.
- **Performance level** (thresholds in `config.py`):

| Level | Rule |
|---|---|
| Outperforming | relative growth ≥ +15% |
| In line | between −10% and +15% |
| Underperforming | relative growth ≤ −10% |

- **Consistency check:** the change in share for Q1 1998 vs Q1 1997, and the direction of the quarterly share trend. A performance level is called **consistent** when all three point the same way.

**Dimension 2: concentration risk**
- **Dependence:** the largest customer's share of the market's revenue over the latest 4 full quarters (Q2 1997 to Q1 1998).
- **Concentration risk:** **High** if dependence > 50%, otherwise **Low**. There's no middle level.

**Recommended action** (a suggestion for management to discuss, not a decision)

| | Low concentration risk | High concentration risk |
|---|---|---|
| **Outperforming** | **Invest:** consider adding sales coverage and targeting similar accounts | **Broaden:** growth looks real but rests on one account; consider protecting it and developing the next accounts |
| **In line** | **Maintain:** current coverage looks adequate | **Protect:** consider account management focused on the key customer |
| **Underperforming** | **Diagnose:** broad slippage; review coverage, pricing and competition | **Rescue:** the market depends on one account and is losing share. The page checks whether that account's own revenue rose or fell: if it fell, review that relationship first; if it rose (as with Ernst Handel in Central Europe, +$14.8K), the cause is the rest of the market, so keep the account close and work on the others (corrected after review) |

A market with fewer than 8 orders in either window gets **"Insufficient data"** and no recommended action.

**Warning flags** (shown next to the action; they don't change it)
- **Near the concentration line:** dependence between 45% and 55%. A small change in one account could move the market across the 50% line.
- **Narrow growth:** one account supplied more than 60% of the market's net revenue increase. Only applies when revenue increased.
- **Not conclusive:** the bootstrap check (§4.4) shows the performance level could plausibly be different.

**Supporting measures (explain why a market is where it is)**
- **Splitting the change:** revenue = number of orders × average order value. The change in each factor is calculated on a log scale, so the two parts add up exactly to the total change.
- **Account contribution:** the change in revenue for each customer between the two windows. These add up exactly to the market's total change.

### 3.3 Demand (Q2)
- **Demand** is the quantity **ordered** (by `OrderDate`), including unshipped orders.
- **Recent monthly demand:** units ordered from 6 Feb to 6 May 1998 (90 days), × 30.44 / 90.
- **Long-run monthly demand:** units ordered from the product's first sale to 6 May 1998, converted to a monthly rate.
- **Demand trend ratio:** recent ÷ long-run. Above 1.25 means demand is speeding up.
- **Demand variability:** standard deviation ÷ mean of monthly units over full months (Jul 1996 to Apr 1998), with months of no sales counted as 0.

### 3.4 Inventory risk (Q2)
- **Months of stock left (on hand):** `UnitsInStock ÷ recent monthly demand`
- **Months of stock left (including stock on order):** `(UnitsInStock + UnitsOnOrder) ÷ recent monthly demand`
- **Below reorder level:** `UnitsInStock < ReorderLevel`
- **No reorder rule:** `ReorderLevel == 0` and the product is active
- **Revenue at risk:** recent monthly demand × average net price per unit over the last 90 days. Used to break ties within a tier.
- **Risk tiers** (thresholds in `config.py`):

| Tier | Rule |
|---|---|
| Critical | out of stock, **or** stock including on-order lasts < 0.5 months |
| High | on-hand stock lasts < 1 month **and** (nothing on order **or** stock including on-order lasts < 1 month) |
| Watch | below reorder level, **or** no reorder rule with on-hand stock lasting < 1.5 months, **or** variability > 1.5 with on-hand stock lasting < 1.5 months |
| OK | everything else |
| No recent demand | recent demand = 0; listed separately |

- **Edge cases:** the 8 discontinued products are excluded from the ranking and listed separately as stock to sell off. A product is flagged as a **possible shortage to verify** when units waiting on unshipped orders exceed its stock. It's a screening flag, not a confirmed backorder: the orders may be unshipped for other reasons, and stock on order may arrive in time (wording corrected after review). A product with no recent demand is listed under "No recent demand" even if it's out of stock (decided at gate 1).
- **Ranking:** by tier (Critical first), then by monthly revenue at stake.
- **Presentation (gate 3, approved):** 32 of 69 active products came out Critical or High. The cause is genuinely thin stock, not only the early-1998 demand surge: using long-run demand, 25 of the 32 stay Critical/High. The main page therefore shows a catalogue-wide headline plus the **top 10** of the ranking; the full ranking moves to the appendix.
- **Actions:** Critical → "Order now", or "Expedite the open order" if one exists; High → "Order this purchasing cycle"; Watch → "Review the reorder level", or "Set a reorder level" if there's none; No recent demand → "Review whether to keep stocking"; OK → "No action needed", plus "set a reorder level" if there's none.
- **Suggested reorder level:** recent monthly demand × an assumed lead time, shown for 0.5, 1 and 2 months because there's no lead-time data.

### 3.5 Processing time (Q3)
| Measure | Formula | Notes |
|---|---|---|
| Processing days | `ShippedDate − OrderDate` | Only the 809 shipped orders |
| Allowed window | `RequiredDate − OrderDate` | Checked for its typical values (for example 14, 28 or 42 days) |
| Slack days | `RequiredDate − ShippedDate` | A negative value means dispatched late |
| Late dispatch | slack < 0 | 37 in total |
| Slow order | processing days above the 90th percentile of all shipped orders | Defines the "slow tail" |
| Not shipped | `ShippedDate` is missing | 21 orders, analyzed separately and never treated as 0 days |

### 3.6 Freight (Q3)
| Measure | Formula | Notes |
|---|---|---|
| Freight per order | `Orders.Freight` | Assumed to be a cost to Northwind (flagged as an assumption) |
| Freight per unit | Freight ÷ total units on the order | |
| Freight share | Freight ÷ order net revenue | How much freight eats into revenue |
| Size band | which quarter of the distribution the order's total units fall into (Q1–Q4) | Band edges fixed from all orders |

### 3.7 Opportunity size (Q3)
- **Benchmark:** the median of the best-performing comparable group. Comparable means the same size band, so small orders are never compared with large ones.
- **Processing excess:** Σ max(0, the order's processing days − the benchmark) across the group's orders, giving total excess days. Also reported per order.
- **Freight excess:** Σ max(0, the order's freight per unit − the benchmark) × the order's units, giving excess freight dollars.
- **Opportunity (clarified at gate 4):** typical processing is 6–7 days everywhere, so the benchmark group also has excess from its own slow orders. A group's opportunity is therefore its excess per order **minus the benchmark group's excess per order**, times its orders, summed over size bands. The benchmark group scores zero; the figure reads "order-days (or dollars) saved if this group's orders behaved like the best comparable group's". Opportunities from different dimensions overlap (an order has a carrier, an employee and a destination), so they are never added together.
- **Carrier adjustment:** when the §4.4 regression runs, a carrier opportunity is shown as supported only if the regression finds a material gap to the best carrier; otherwise it's marked "not supported after adjustment".
- **Consolidation opportunity:** freight dollars spent on orders in the smallest size band whose freight share is above a threshold (default 15%). These are candidates for combining or for a minimum order value.
- Opportunities are ranked by dollars (freight) or days (processing) and reported side by side. They are never added together.

---

## 4. Analysis approach for each question

**Principle:** answer each question with clear descriptive comparisons (totals, medians, shares, rankings, and like-for-like groups). Use an advanced technique only when a specific condition in §4.4 is met, and put it in the technical appendix, not the main page.

### Q1: Markets
1. Table of net revenue, number of orders and active customers for each market and quarter, Q3 1996 to Q1 1998 (Q2 1998 kept separately).
2. Company growth, then each market's growth, share of company revenue and relative growth, plus the two consistency checks (§3.2).
3. Performance level, concentration risk, recommended action and warning flags for each market.
4. Split each market's change into "number of orders" vs "order size".
5. Each market's 3 biggest gaining and 3 biggest losing accounts.
6. **Output:** market scorecard, account-movers table, and one plain-language summary per market, worded as a recommendation.

### Q2: Restocking
1. Demand measures for each active product (§3.3).
2. Months of stock left, reorder status and risk tier (§3.4).
3. Rank by tier, then by revenue at risk.
4. Assign an action:
   - **Critical:** order now or speed up an existing order.
   - **High:** order in this purchasing cycle.
   - **Watch:** review the reorder level.
   - **No reorder rule:** set one, using the suggested level.
5. Cross-check against unshipped orders.
6. **Output:** the ranked watch list, a table of products without a reorder rule, and a list of discontinued products still holding stock.

### Q3: Logistics efficiency
1. Build the order-level table with processing measures, freight measures, size band and destination region.
2. **Describe the variation:** median and 90th percentile of processing days, plus median freight per unit and freight share, broken down by:
   - carrier, destination region, size band, employee, and order quarter.
   - Carrier and region comparisons are always shown **within size bands**, so they compare like with like.
3. **Find the problem groups:** the slow tail (>90th percentile), late dispatches, unshipped orders, and orders where freight is a large share of revenue. For each: how many orders, what share of the total, and what they have in common. Also check whether orders with the shortest allowed window (14 days) are processed faster than the rest, and what share of late orders come from the slow tail.
4. **Size the opportunities** (§3.7) and rank them.
5. **Turn each top opportunity into an action**, for example "orders handled by X take N days longer than the benchmark" → review that order-handling process.
6. **Output:** a ranked opportunity table (top 3–5) with size, orders affected and suggested action, plus the descriptive breakdown tables for the appendix.

### 4.4 When advanced methods are used, and only then

| Condition | Method | Why it would change the conclusion | Where it goes |
|---|---|---|---|
| Q1: a market's relative growth is within ±5 points of a performance threshold, **or** its consistency checks disagree | Bootstrap interval on relative growth: all company orders in each window are resampled (2,000 times, seed 561) and the market's share is recomputed each time | Decides whether the performance level is reliable or should carry a "not conclusive" flag | Appendix; the flag appears on the main page |
| Q3: a carrier or employee difference persists within size bands **but** that group also handles a different mix of destinations | A simple regression adjusting for size band and region | Separates "this carrier/employee is slower" from "they get harder orders" before recommending an action | Appendix; the main page states the adjusted conclusion in plain words |
| Q3: a top opportunity rests on fewer than 30 orders | Bootstrap interval on the benchmark gap | Avoids recommending action based on noise | Appendix |
| Q2 | None planned | The tiers are rules applied to the stock snapshot; statistics wouldn't make them more reliable | — |

If no condition is met, no advanced method is run, and the appendix says so.

**Q1 outcome (gate 2, approved):** when the bootstrap was run for all 10 markets as a diagnostic, every interval crossed at least one performance threshold, even Germany's (+85%, interval +4% to +236%). With about 13–42 orders per market per window, the exact level can't be established statistically. Decision:
- keep the triggered "not conclusive" flags as defined above;
- state on the page that Q1 performance levels are **directional**;
- show the intervals for all markets in the appendix (`q1_uncertainty.csv`).

---

## 5. Visualizations and webpage structure

Charts follow the `dataviz` skill (loaded before any chart code is written): one consistent colour scheme, colours that keep the same meaning throughout, works in light and dark mode, and charts plus captions readable without hover.

### 5.1 Charts on the main page: one main and one supporting chart per question

| Question | Role | Chart | What it shows |
|---|---|---|---|
| Q1 | **Main** | Scatter plot: relative growth across, largest customer's share up, bubble size = market revenue, lines at the thresholds marking the six areas, the 45–55% band shaded, each bubble labelled with its market and recommended action | Where each market sits on both dimensions, and the suggested focus |
| Q1 | Supporting | Horizontal bars of account contributions for the 4 focus markets | Which accounts drove each change, so the reader knows who to call |
| Q2 | **Main** | Scatter plot: recent monthly demand vs months of stock left (log scale), reference lines at 0.5 and 1 month. Colours: Critical, High, and "Watch or OK" sharing a neutral, with marker shape as a second cue (four tier colours failed the colour-blind checks for scatter plots; changed at gate 5) | Urgency and demand volume together; the bottom-right corner is where to act |
| Q2 | Supporting | Dumbbell chart for the top 10: units available (in stock + on order) vs one month of recent demand, labelled with the shortfall (changed at gate 5: none of the top 10 has stock on order, so the planned months-of-cover version showed overlapping dots) | How much each top product is short of one month's demand |
| Q3 | **Main** | Ranked horizontal bars of the top opportunities, freight $ and processing days shown in separate panels | Where the biggest gains are, and how big they are |
| Q3 | Supporting | Column chart of the late-dispatch rate by allowed window (14 / 28 / 42 days) (changed at gate 5: consolidation turned out not to be material, so the planned freight-share scatter no longer supports the answer) | Short-deadline orders aren't prioritised: the clearest operational fix |

Each question section also has **one compact decision table**: the market scorecard, the top 10 of the watch list, or the opportunity list. Tables aren't counted as charts.

### 5.2 Technical appendix (charts and tables not on the main page)
- Quarterly revenue small-multiple charts for every market; full account-movers tables.
- Full watch list; products without a reorder rule; discontinued stock; demand-window sensitivity.
- Breakdown tables of processing time and freight by carrier, region, size band, employee and quarter; box plots of processing days.
- Results of any §4.4 method that was triggered, or a note that none were.
- Robustness results (§8.3) and the independent cross-check results (§8.1).

### 5.3 Webpage structure
1. **Header:** title, one-paragraph summary of the dataset, the analysis cutoff, and links to the GitHub repository.
2. **Executive summary:** three findings and three recommended actions.
3. **Data and caveats:** what the data covers and the six caveats.
4. **Q1, Q2 and Q3 sections** (redesigned for executives at gate 5), each laid out the same way: **question → why it matters** (one sentence) **→ key finding** (highlighted) **→ one primary chart** (visible title, labelled axes with units, legends) **→ business interpretation** (one or two sentences) **→ recommended action** (highlighted, 2–3 items). Three expandable sections follow: *supporting chart and detailed table*, *full interpretation*, and *how this was analysed* (method and caveat). The summary at the top reuses each section's key finding and actions, so the two never disagree.
   - **Executive revisions (after publication review):**
     - Summary cards show one large metric, one finding and one action each.
     - A "Top three management priorities" section ranks actions across departments by certainty of evidence, money at stake and speed. It uses only confirmed actions.
     - Every action is labelled *Confirmed*, *Tentative* or *To verify*, and names the first account or item to look at and the next step.
     - Q1 has a "How to read this chart" guide for the axes and the six categories.
     - Q2 shows the top 5 products with order quantities directly under the chart, plus how the list is chosen: urgency tier first, then monthly revenue at stake.
     - A plain-English glossary is added, and chart text is about 2 points larger.
     - A Q1 action is tentative if the market's share direction flips between periods, if the bootstrap check isn't conclusive, or if its concentration label depends on how dependence is measured.
   - **Q3 primary chart** became the late-dispatch rate by allowed window; the opportunity chart moved to the expandable section and shows processing only. Freight gaps that don't survive adjustment are labelled "No action" everywhere, so the page never recommends reviewing carrier rates while also saying the gap isn't supported.
5. **Limitations and data needed next** (§11).
6. **Technical appendix** (§5.2), collapsed by default.
7. **Methods and reproducibility:** definitions in plain language, how to rebuild the page from the repository, the input file fingerprint, and the version or commit the page was built from.

The page is a single self-contained HTML file with charts embedded as SVG and inline styling. It loads no external scripts, works at phone width and in dark mode, and has alt text for every chart.

---

## 6. Implementation and file organization

**Python only.** Python 3.13. Core libraries: pandas, numpy, openpyxl, matplotlib, jinja2, pytest. scipy or statsmodels are added **only if** a §4.4 condition triggers. Exact versions are pinned in `requirements.txt`.

### Repository layout (this folder becomes the public repository)

```
northwind-analysis/                  # public GitHub repository
├── README.md                        # purpose, findings summary, link to the page, how to reproduce
├── LICENSE                          # code licence (MIT by default)
├── plan.md                          # this plan
├── requirements.txt                 # pinned versions
├── .gitignore                       # .venv, __pycache__, local scratch files
├── data/
│   └── Northwind Database.xlsx      # input; never modified (licence checked, see §9)
├── run_analysis.py                  # single entry point: python run_analysis.py
├── northwind/
│   ├── __init__.py
│   ├── config.py                    # paths, cutoff, windows, thresholds, region maps, seed
│   ├── load.py                      # read sheets, check expected columns, fingerprint the input
│   ├── clean.py                     # cleaning rules (§2.3)
│   ├── model.py                     # build order_lines, orders, products (§2.2)
│   ├── metrics.py                   # definitions (§3)
│   ├── q1_markets.py
│   ├── q2_inventory.py
│   ├── q3_logistics.py
│   ├── charts.py                    # one function per chart, returns SVG
│   └── report.py                    # assembles the HTML page
├── templates/
│   └── report.html.j2
├── verification/
│   ├── sql_crosscheck.py            # independent recalculation (§8.1)
│   ├── robustness.py                # alternative definitions (§8.3)
│   ├── check_public_site.py         # automated public-URL check (§8.5)
│   └── hand_checks.md               # manual checks against Excel, and the private-window checklist
├── tests/
│   ├── conftest.py                  # small made-up workbook used as test data
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                            # what GitHub Pages serves; generated, never edited by hand
│   ├── index.html
│   └── .nojekyll
├── outputs/                         # generated tables and manifest, committed for transparency
│   ├── tables/*.csv
│   └── run_manifest.json
└── .github/workflows/
    └── ci.yml                       # on each push: install, run tests, rebuild, check docs/ is up to date
```

`SKILL.md` stays in the folder but is **not** committed (it's a personal tool configuration, not part of the analysis). It will be added to `.gitignore`.

### Conventions
- Each analysis module exposes a function like `run(model, config) -> Q1Result`: data in, tables out, no file writing. All file writing happens in `run_analysis.py` and `report.py`.
- Every threshold and window lives in `config.py`.
- Google-style docstrings following `SKILL.md`.
- Script names avoid clashing with Python's own modules. (A scratch script named `inspect.py` broke pandas earlier for this reason.)

---

## 7. Testing

The test framework is `pytest`, run with `python -m pytest`. The same tests run on GitHub Actions on every push.

### 7.1 Unit tests (small made-up data, fast)
- **Revenue:** discount rounding, net vs gross, an order with several lines.
- **Market performance:** the two-window calculation, relative growth equal to the change in share, the orders-vs-size split adding up exactly to the total, account contributions adding up to the market's change, each performance level at its threshold edges, concentration risk at exactly 50%, all six actions, the "insufficient data" rule, each warning flag at its edges, the consistency flag.
- **Demand:** 90-day window boundaries, monthly conversion, unshipped orders counted as demand, zero-sales months included in variability.
- **Inventory:** zero demand gives "no recent demand" rather than a division error, out-of-stock gives Critical, each tier rule at its boundary, discontinued products excluded.
- **Processing time and freight:** unshipped orders give missing values rather than 0, negative slack counts as late, size bands at their edges, the slow-tail cutoff.
- **Opportunity sizing:** benchmark chosen within the same size band, orders better than the benchmark contribute 0 (not negative), freight and processing opportunities are never added together.
- **Regions:** all 21 countries map to exactly one group in each scheme, and an unknown country raises an error.
- **Loading:** a missing sheet or column raises a clear error.

### 7.2 Integration tests (on the real workbook)
- Row counts after every join match §2.2, with no missing keys.
- Control totals: net revenue ≈ $1,265,793 and gross ≈ $1,354,459.
- Q1: all markets add up to total revenue, market shares add up to 100% in each window, and account contributions add up to each market's change.
- Q2: exactly 69 active products ranked, 16 flagged as having no reorder rule.
- Q3: 809 orders in the processing analysis, 21 unshipped, 37 late. Opportunity totals reproduce from the order-level table.
- Every output table has the expected columns and no unexpected missing values.

### 7.3 End-to-end tests
- `python run_analysis.py` runs on a copy of the repository in a temporary folder and finishes without errors.
- `docs/index.html` exists, has the Q1, Q2, Q3 and appendix sections, exactly 2 charts in each question section, and no "NaN", "None" or "inf" text.
- Headline numbers shown on the page match the CSV tables.
- The page references no external files (fully self-contained).
- **Determinism:** two runs give identical tables and an identical page, apart from the build timestamp.
- The input workbook's fingerprint is unchanged after a run.

---

## 8. Independent verification of findings

### 8.1 Recalculating key numbers a second way
`verification/sql_crosscheck.py` reads the workbook with **openpyxl only (no pandas)**, loads it into an in-memory SQLite database, and recalculates the key numbers in plain SQL:
- total net revenue, revenue by market and quarter, and each market's window revenue, growth and relative growth;
- recent demand, months of stock left and tier for each product;
- median processing days and freight per unit by carrier and size band, and the top opportunity totals.

**Pass:** every number matches to within $0.01 or 0.01 units, and every product gets the same tier.

### 8.2 Manual checks against Excel
`verification/hand_checks.md` records a check in Excel of: 3 orders (one with a discount, one unshipped, one with many lines), 2 products from the watch list, 1 market's quarterly total, and the freight total for the top Q3 opportunity.

### 8.3 Robustness: does the finding survive a different reasonable definition?

| Finding | Alternative tested | Holds if |
|---|---|---|
| Q1 performance levels | Ship-to country instead of customer country; Q1-only comparison; largest customer removed | Each focus market keeps its performance level in ≥2 of 3 alternatives, or the change is explained on the page. (Concentration risk is a direct measurement, so it isn't re-tested.) |
| Q2 ranking | 60-day and 120-day demand windows | ≥80% of products in the Critical and High tiers stay in those tiers |
| Q3 opportunities | Size bands based on revenue instead of units; leaving out the top 1% of freight values; benchmark = overall median instead of best group | The top 3 opportunities stay in the top 5 |

### 8.4 Fresh review
Before publishing, a separate reviewer that hasn't seen my conclusions gets the code and output tables and is asked to challenge the three headline findings. Its objections, and how each was resolved, are listed in the appendix.

**Outcome (gate 6):** 14 objections, 5 high; every high one was confirmed by an independent re-run and fixed (`verification/fresh_review.md` and `.json`). Additions to the method as a result: a three-period share-direction check for Q1 (actions for markets that flip are marked tentative), dependence reported over both the last four quarters and the compared periods, a Q2 shortfall range using long-run and recent demand, and a Q3 carrier regression repeated without the slowest 10% of orders. Approved thresholds and labels are unchanged.

### 8.5 Checking the public URL and the public repository
After publishing, the public site and repository are checked as an anonymous visitor:

**Automated** (`verification/check_public_site.py`, uses only the Python standard library, no cookies or logins):
1. The page URL returns HTTP 200 over HTTPS without any authentication.
2. The page served online is byte-for-byte the same as `docs/index.html` in the repository (comparing SHA-256 fingerprints).
3. The page contains the expected section headings and headline numbers.
4. The repository's main page and the raw `README.md` return HTTP 200 without logging in, and the GitHub API reports the repository as public.

**Fresh-clone reproduction:**
5. Clone the public repository anonymously over HTTPS into an empty temporary folder, create a new virtual environment, install `requirements.txt`, run the tests and `python run_analysis.py`.
6. **Pass:** all tests pass and the rebuilt `docs/index.html` matches the published page.

**Private-window check** (`verification/hand_checks.md` has the checklist):
7. Open the page URL and the repository URL in a **private/incognito window** with no logins. Confirm that:
   - both load with no sign-in prompt;
   - all 6 charts render;
   - the appendix opens;
   - links to the repository work;
   - the layout works at phone width and in dark mode.
8. **Who does this:** my built-in browser can't open a true incognito session, and it may carry the GitHub login from your session. I'll do the automated checks (1–6) and a cookie-free browser check. **You** do the final incognito check in your own browser using the checklist, and record the result in `hand_checks.md`.

---

## 9. Reproducibility and publication

### Reproducibility
1. **Environment:** a virtual environment (`.venv`) with exact versions in `requirements.txt`. Python 3.13 is stated in the README and in CI.
2. **Input fingerprint:** the workbook's SHA-256 hash is recorded in `run_manifest.json` and checked at the start of each run.
3. **Fixed randomness:** seed 561 for any resampling that's triggered.
4. **One command:** `python run_analysis.py` rebuilds every table, chart and the page. Nothing in `docs/` or `outputs/` is edited by hand.
5. **Manifest:** run time, input hash, Python and library versions, config values, the git commit used, and the verification results.
6. **CI:** GitHub Actions runs the tests and rebuilds the page on every push, and fails if the committed `docs/index.html` doesn't match a fresh build. This proves the published page comes from the committed code.
7. **README:** a short "Reproduce in 4 commands" section (clone, create environment, install, run).

### Publication steps (each step that goes public requires your confirmation at gate G6)
1. Run the full pipeline, tests and verification locally. Publication is blocked if anything fails.
2. You review `docs/index.html` locally.
3. **Pre-publication privacy check:**
   - No personal details in the code, page, README or commit history.
   - Commit author email set to your GitHub "noreply" address, not your university email.
   - `SKILL.md`, `.venv` and scratch files excluded.
   - The workbook's licence checked. Northwind is a widely used Microsoft sample database whose customer and employee details are fictional; I'll confirm it may be redistributed. If that can't be confirmed, the workbook stays out of the repository and the README explains how to obtain it.
4. `git init`, the first commit, and creation of the **public** repository under your GitHub account with `gh` (you authenticate `gh` yourself if it isn't already).
5. Push, and enable GitHub Pages to serve `/docs` from the `main` branch.
6. Run the checks in §8.5. If anything fails, fix it, push again and re-check.
7. Record the public URLs and the verified commit in the README and the manifest.

---

## 10. Work sequence and review gates

| Step | Work | Gate: you review |
|---|---|---|
| G0 | This plan | **Approve plan.md** before anything is implemented |
| 1 | Environment, `load` / `clean` / `model` / `metrics`, unit and integration tests, SQL cross-check of control totals | Foundation and tests pass |
| 2 | Q1 analysis, tests, robustness checks | Q1 findings |
| 3 | Q2 analysis, tests, robustness checks | Q2 findings |
| 4 | Q3 analysis, tests, robustness checks | Q3 findings |
| 5 | Charts, webpage, appendix, end-to-end tests | Page draft (local) |
| 6 | Full verification (§8.1–8.4), fresh review, README, CI workflow, privacy check | **Approval to make the repository and page public** |
| 7 | Create the public repository, push, enable Pages, public-URL checks (§8.5) | Your incognito check; final sign-off |

---

## 11. Limitations and data needed next

### What the conclusions can't claim
- **Profit:** there are no product costs or margins, so everything is about revenue.
- **Cause and effect:** Q1 explains *where* revenue changed, not *why* customers behaved as they did. Q3 compares like-for-like groups but can't prove that a given carrier or employee *causes* a difference.
- **Future:** nothing here is a forecast. There are 22 months of history, two of them part-years.
- **Delivery:** processing time ends at dispatch. What happens after that is unknown.
- **Inventory timing:** "months of stock left" assumes the stock snapshot was taken at the analysis cutoff.

### Data the manager would need to go further
| Data | Would allow |
|---|---|
| Delivery dates from carriers | End-to-end delivery time and choosing carriers on performance |
| Dated stock records over time | Stockout history and real days-of-stock |
| Supplier lead times | Correct reorder levels and run-out dates |
| Sales territory assignments | Fair comparisons of sales rep performance |
| Product costs | Profit by market and product |
| Freight terms (who pays, rate cards) | Whether freight is a cost to cut or a price to set, and the true value of consolidating orders |

---

## 12. Decisions (defaults applied unless you change them)

| Decision | Default | Alternatives |
|---|---|---|
| Hosting | GitHub Pages serving `/docs` from `main` | GitHub Pages deployed by a GitHub Actions workflow |
| Repository name | `northwind-analysis` | Your choice |
| GitHub account | Your personal account (authenticated through `gh`) | An organization or class account |
| Commit email | Your GitHub noreply address | Another address you choose |
| Code licence | MIT | Another licence, or none |
| Data in the repository | Included if the licence allows redistribution; otherwise excluded with instructions to obtain it | Always excluded |
| `plan.md` in the repository | Included | Excluded |
| Market definition (Q1) | Customer's country | Ship-to country (tested as a robustness check either way) |
| Chart style | Static matplotlib charts embedded as SVG | Interactive Plotly (adds a JavaScript dependency) |
| Thresholds | As in §3–§4, all adjustable in `config.py` | Your preferred values |
