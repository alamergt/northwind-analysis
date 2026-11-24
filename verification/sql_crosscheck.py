"""Recalculate control totals with openpyxl + SQLite and compare with the model.

This path shares no code with the pandas pipeline: the workbook is read
cell by cell with openpyxl and every figure is computed in plain SQL.

Usage:
    python verification/sql_crosscheck.py

Exits with status 1 if any figure disagrees.
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from northwind import Config, load_model, q1_markets, q2_inventory, q3_logistics  # noqa: E402

SHEETS = ["Orders Details", "Orders", "Customers", "Product", "Shippers"]
MONEY_TOL = 0.01


def load_into_sqlite(path):
    """Copy the needed sheets into an in-memory SQLite database.

    Args:
        path (pathlib.Path): Workbook to read.

    Returns:
        sqlite3.Connection: Database with one table per sheet; dates are
        stored as ISO 8601 text.
    """
    con = sqlite3.connect(":memory:")
    workbook = load_workbook(path, read_only=True, data_only=True)
    for name in SHEETS:
        rows = workbook[name].iter_rows(values_only=True)
        # Keep every column position; blank or repeated headers (the Product
        # sheet has both) get a unique placeholder name.
        header, seen = [], set()
        for i, h in enumerate(next(rows)):
            name_i = str(h) if h is not None and str(h) not in seen else f"_col{i}"
            seen.add(name_i)
            header.append(name_i)
        cols = ", ".join(f'"{h}"' for h in header)
        con.execute(f'CREATE TABLE "{name}" ({cols})')
        marks = ", ".join("?" for _ in header)
        for row in rows:
            # Read-only mode drops trailing empty cells, so pad short rows.
            row = (tuple(row) + (None,) * len(header))[: len(header)]
            values = [v.isoformat() if isinstance(v, datetime) else v for v in row]
            if all(v is None for v in values):
                continue
            con.execute(f'INSERT INTO "{name}" VALUES ({marks})', values)
    workbook.close()
    return con


SQL = {
    "order_lines": 'SELECT COUNT(*) FROM "Orders Details"',
    "orders": "SELECT COUNT(*) FROM Orders",
    "orders_shipped": "SELECT COUNT(*) FROM Orders WHERE ShippedDate IS NOT NULL",
    "orders_late": "SELECT COUNT(*) FROM Orders WHERE ShippedDate > RequiredDate",
    "customers_with_orders": "SELECT COUNT(DISTINCT CustomerID) FROM Orders",
    "active_products": "SELECT COUNT(*) FROM Product WHERE Discontinued = 0",
    "active_without_reorder_rule":
        "SELECT COUNT(*) FROM Product WHERE Discontinued = 0 AND ReorderLevel = 0",
    "net_revenue":
        'SELECT SUM(UnitPrice * Quantity * (1 - ROUND(Discount, 2))) FROM "Orders Details"',
    "gross_revenue": 'SELECT SUM(UnitPrice * Quantity) FROM "Orders Details"',
}

SQL_BY_QUARTER = """
SELECT substr(o.OrderDate, 1, 4) || 'Q' || ((CAST(substr(o.OrderDate, 6, 2) AS INTEGER) + 2) / 3),
       SUM(d.UnitPrice * d.Quantity * (1 - ROUND(d.Discount, 2)))
FROM "Orders Details" d JOIN Orders o ON o.OrderID = d.OrderID
GROUP BY 1
"""

SQL_BY_COUNTRY = """
SELECT c.Country, SUM(d.UnitPrice * d.Quantity * (1 - ROUND(d.Discount, 2)))
FROM "Orders Details" d
JOIN Orders o ON o.OrderID = d.OrderID
JOIN Customers c ON c.CustomerID = o.CustomerID
GROUP BY 1
"""


SQL_PRODUCT_TIERS = """
WITH recent AS (
  SELECT d.ProductID, SUM(d.Quantity) AS qty
  FROM "Orders Details" d JOIN Orders o ON o.OrderID = d.OrderID
  WHERE substr(o.OrderDate, 1, 10) BETWEEN :start AND :cutoff
  GROUP BY d.ProductID
),
monthly AS (
  SELECT d.ProductID, substr(o.OrderDate, 1, 7) AS month, SUM(d.Quantity) AS qty
  FROM "Orders Details" d JOIN Orders o ON o.OrderID = d.OrderID
  GROUP BY 1, 2
),
grid AS (
  SELECT p.ProductID, m.month, COALESCE(mo.qty, 0) AS qty
  FROM Product p CROSS JOIN months m
  LEFT JOIN monthly mo ON mo.ProductID = p.ProductID AND mo.month = m.month
),
var AS (
  SELECT ProductID, AVG(qty) AS mean, AVG(qty * qty) - AVG(qty) * AVG(qty) AS variance
  FROM grid GROUP BY ProductID
),
base AS (
  SELECT p.ProductID, p.UnitsInStock AS stock, p.UnitsOnOrder AS on_order,
         p.ReorderLevel AS reorder, p.Discontinued AS discontinued,
         COALESCE(r.qty, 0) * :dpm / :window AS demand,
         v.mean, v.variance
  FROM Product p
  LEFT JOIN recent r ON r.ProductID = p.ProductID
  LEFT JOIN var v ON v.ProductID = p.ProductID
)
SELECT ProductID, demand,
  CASE
    WHEN demand <= 0 THEN 'No recent demand'
    WHEN stock <= 0 OR (stock + on_order) / demand < :critical THEN 'Critical'
    WHEN stock / demand < :high AND (on_order <= 0 OR (stock + on_order) / demand < :high) THEN 'High'
    WHEN stock < reorder
      OR (reorder <= 0 AND stock / demand < :watch)
      -- coefficient of variation > v  <=>  variance > v^2 * mean^2 (mean > 0)
      OR (mean > 0 AND variance > :hv * :hv * mean * mean AND stock / demand < :watch) THEN 'Watch'
    ELSE 'OK'
  END AS tier
FROM base WHERE discontinued = 0
"""


def product_checks(con, config, watch_list):
    """Recompute recent demand and risk tier per active product in SQL.

    Args:
        con (sqlite3.Connection): Database from ``load_into_sqlite``.
        config (northwind.config.Config): Window and tier thresholds.
        watch_list (pandas.DataFrame): Q2 watch list from the pipeline.

    Returns:
        list[dict]: One demand comparison per product, one tier
        comparison per product, and a summary check of tier agreement.
    """
    import pandas as pd  # only to build the month list from the config

    months = [str(m) for m in pd.period_range(*config.demand_months, freq="M")]
    con.execute("CREATE TABLE months (month)")
    con.executemany("INSERT INTO months VALUES (?)", [(m,) for m in months])
    start = config.cutoff - pd.Timedelta(days=config.demand_window_days - 1)
    params = {
        "start": start.strftime("%Y-%m-%d"), "cutoff": config.cutoff.strftime("%Y-%m-%d"),
        "dpm": config.days_per_month, "window": float(config.demand_window_days),
        "critical": config.critical_cover, "high": config.high_cover,
        "watch": config.watch_cover, "hv": config.high_variability,
    }
    sql = {pid: (demand, tier) for pid, demand, tier in con.execute(SQL_PRODUCT_TIERS, params)}
    pandas_side = watch_list.set_index("ProductID")
    results, mismatched = [], []
    for pid, row in pandas_side.iterrows():
        demand, tier = sql[pid]
        results.append(compare(f"Q2 recent demand product {pid}", demand,
                               row["RecentMonthlyDemand"], tol=0.01))
        same = tier == row["Tier"]
        results.append({"check": f"Q2 tier product {pid}", "sql": tier, "pandas": row["Tier"],
                        "abs_diff": 0 if same else 1, "pass": same})
        if not same:
            mismatched.append(pid)
    results.append({"check": "Q2 every active product has the same tier",
                    "sql": len(sql), "pandas": len(pandas_side),
                    "abs_diff": len(mismatched),
                    "pass": not mismatched and set(sql) == set(pandas_side.index)})
    return results


SQL_CARRIER_BASE = """
WITH units AS (SELECT OrderID, SUM(Quantity) AS units FROM "Orders Details" GROUP BY OrderID),
o AS (
  SELECT o.OrderID, s.CompanyName AS grp, u.units,
         julianday(substr(o.ShippedDate, 1, 10)) - julianday(substr(o.OrderDate, 1, 10)) AS days,
         o.Freight * 1.0 / u.units AS fpu,
         CASE WHEN u.units <= :e1 THEN 'Small' WHEN u.units <= :e2 THEN 'Medium'
              WHEN u.units <= :e3 THEN 'Large' ELSE 'Very large' END AS band
  FROM Orders o
  JOIN units u ON u.OrderID = o.OrderID
  JOIN Shippers s ON s.ShipperID = o.ShipVia
  WHERE o.ShippedDate IS NOT NULL
),
v AS (SELECT band, grp, {value} AS val, {weight} AS w FROM o),
ranked AS (
  SELECT band, grp, val,
         ROW_NUMBER() OVER (PARTITION BY band, grp ORDER BY val) AS rn,
         COUNT(*) OVER (PARTITION BY band, grp) AS n
  FROM v
),
med AS (
  SELECT band, grp, AVG(val) AS median, MAX(n) AS n
  FROM ranked WHERE rn IN ((n + 1) / 2, (n + 2) / 2) GROUP BY band, grp
),
best AS (
  SELECT band, grp AS best_grp, median AS level FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY band ORDER BY median, grp) AS r
    FROM med WHERE n >= :min_n) WHERE r = 1
),
exc AS (SELECT v.band, v.grp, MAX(0, v.val - b.level) * v.w AS e FROM v JOIN best b ON b.band = v.band),
pg AS (SELECT band, grp, AVG(e) AS mean_e, COUNT(*) AS n FROM exc GROUP BY band, grp),
ref AS (SELECT pg.band, pg.mean_e AS ref_e FROM pg JOIN best b ON b.band = pg.band AND b.best_grp = pg.grp)
"""

SQL_CARRIER_MEDIANS = SQL_CARRIER_BASE + "SELECT band, grp, median FROM med"
SQL_CARRIER_OPPORTUNITY = SQL_CARRIER_BASE + """
SELECT pg.grp, SUM(pg.n * MAX(0, pg.mean_e - ref.ref_e))
FROM pg JOIN ref ON ref.band = pg.band GROUP BY pg.grp
"""


def logistics_checks(con, config, model, q3_result):
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
    edges = model.size_band_edges
    params = {"e1": float(edges[1]), "e2": float(edges[2]), "e3": float(edges[3]),
              "min_n": config.min_group_orders_per_band}
    within = q3_result.within_bands["Carrier"].set_index(["SizeBand", "ShipperName"])
    opps = q3_result.opportunities
    results = []
    for kind, value, weight, col in (("Processing", "days", "1.0", "MedianDays"),
                                     ("Freight", "fpu", "units", "MedianFreightPerUnit")):
        for band, grp, median in con.execute(SQL_CARRIER_MEDIANS.format(value=value, weight=weight), params):
            results.append(compare(f"Q3 median {value} {band} / {grp}", median,
                                   within.loc[(band, grp), col], tol=1e-9))
        pipeline = opps[(opps["Type"] == kind) & (opps["Dimension"] == "Carrier")].set_index("Group")["Size"]
        for grp, size in con.execute(SQL_CARRIER_OPPORTUNITY.format(value=value, weight=weight), params):
            results.append(compare(f"Q3 {kind.lower()} opportunity {grp}", size,
                                   pipeline.get(grp, 0.0), tol=0.01))
    return results


def pandas_figures(model):
    """Compute the same figures from the pandas model.

    Args:
        model (northwind.model.Model): Model built by the pipeline.

    Returns:
        tuple[dict, dict, dict]: Scalar totals, revenue by quarter and
        revenue by customer country.
    """
    lines, orders, products = model.order_lines, model.orders, model.products
    active = products[~products["Discontinued"]]
    scalars = {
        "order_lines": len(lines),
        "orders": len(orders),
        "orders_shipped": int(orders["IsShipped"].sum()),
        "orders_late": int(orders["IsLate"].sum()),
        "customers_with_orders": orders["CustomerID"].nunique(),
        "active_products": len(active),
        "active_without_reorder_rule": int((active["ReorderLevel"] == 0).sum()),
        "net_revenue": float(lines["NetRevenue"].sum()),
        "gross_revenue": float(lines["GrossRevenue"].sum()),
    }
    by_quarter = lines.groupby(lines["Quarter"].astype(str))["NetRevenue"].sum().to_dict()
    by_country = lines.groupby("CustomerCountry")["NetRevenue"].sum().to_dict()
    return scalars, by_quarter, by_country


def compare(name, sql_value, pandas_value, tol=MONEY_TOL):
    """Compare one figure from each path.

    Args:
        name (str): Figure name.
        sql_value (float | int): Value from SQL.
        pandas_value (float | int): Value from the pandas model.
        tol (float): Largest allowed absolute difference.

    Returns:
        dict: Name, both values, absolute difference and pass flag.
    """
    diff = abs(float(sql_value) - float(pandas_value))
    return {"check": name, "sql": sql_value, "pandas": pandas_value,
            "abs_diff": diff, "pass": diff <= tol}


SQL_MARKET_WINDOWS = """
WITH lines AS (
  SELECT m.Market,
         substr(o.OrderDate, 1, 4) || 'Q' || ((CAST(substr(o.OrderDate, 6, 2) AS INTEGER) + 2) / 3) AS q,
         d.UnitPrice * d.Quantity * (1 - ROUND(d.Discount, 2)) AS rev
  FROM "Orders Details" d
  JOIN Orders o ON o.OrderID = d.OrderID
  JOIN Customers c ON c.CustomerID = o.CustomerID
  JOIN market_map m ON m.Country = c.Country
)
SELECT Market,
       SUM(CASE WHEN q IN ({prior}) THEN rev ELSE 0 END),
       SUM(CASE WHEN q IN ({current}) THEN rev ELSE 0 END)
FROM lines GROUP BY Market
"""


def market_checks(con, config, scorecard):
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
    con.execute("CREATE TABLE market_map (Country, Market)")
    con.executemany("INSERT INTO market_map VALUES (?, ?)", config.market_groups.items())
    quote = lambda qs: ", ".join(f"'{q}'" for q in qs)  # noqa: E731
    query = SQL_MARKET_WINDOWS.format(prior=quote(config.prior_window),
                                      current=quote(config.current_window))
    card = scorecard.set_index("Market")
    rows = con.execute(query).fetchall()
    total_prior = sum(r[1] for r in rows)
    total_current = sum(r[2] for r in rows)
    results = []
    for market, prior, current in rows:
        relative = (current / total_current) / (prior / total_prior) - 1
        results.append(compare(f"Q1 prior revenue {market}", prior, card.loc[market, "RevenuePrior"]))
        results.append(compare(f"Q1 current revenue {market}", current, card.loc[market, "RevenueCurrent"]))
        results.append(compare(f"Q1 growth {market}", current / prior - 1, card.loc[market, "Growth"], tol=1e-6))
        results.append(compare(f"Q1 relative growth {market}", relative,
                               card.loc[market, "RelativeGrowth"], tol=1e-6))
    return results


def run_checks(config=None, model=None):
    """Run every cross-check and save the results as JSON.

    Args:
        config (northwind.config.Config | None): Settings; None uses
            the defaults.
        model (northwind.model.Model | None): Pipeline model; None
            builds it.

    Returns:
        list[dict]: One result per check, each with a pass flag.
    """
    config = config or Config()
    con = load_into_sqlite(config.workbook)
    model = model or load_model(config)
    scalars, by_quarter, by_country = pandas_figures(model)

    results = [compare(k, con.execute(q).fetchone()[0], scalars[k]) for k, q in SQL.items()]
    for label, query, reference in (("quarter", SQL_BY_QUARTER, by_quarter),
                                    ("country", SQL_BY_COUNTRY, by_country)):
        sql_rows = dict(con.execute(query).fetchall())
        if set(sql_rows) != set(reference):
            results.append({"check": f"net_revenue by {label}: same keys", "pass": False})
        for key in sorted(sql_rows):
            results.append(compare(f"net_revenue {label}={key}", sql_rows[key], reference.get(key, 0)))
    results += market_checks(con, config, q1_markets.run(model, config).scorecard)
    results += product_checks(con, config, q2_inventory.run(model, config).watch_list)
    results += logistics_checks(con, config, model, q3_logistics.run(model, config))

    out = config.output_dir / "verification" / "sql_crosscheck.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    return results


def main():
    """Run the cross-check and print a report.

    Args:
        None.

    Returns:
        int: 0 if every figure matches, otherwise 1.
    """
    config = Config()
    results = run_checks(config)
    out = config.output_dir / "verification" / "sql_crosscheck.json"
    failed = [r for r in results if not r["pass"]]
    width = max(len(r["check"]) for r in results)
    for r in results:
        if "sql" in r:
            show = lambda v: f"{v:>14,.2f}" if isinstance(v, (int, float)) else f"{v:>14}"  # noqa: E731
            print(f"{'PASS' if r['pass'] else 'FAIL'}  {r['check']:<{width}}  "
                  f"sql={show(r['sql'])}  pandas={show(r['pandas'])}")
        else:
            print(f"FAIL  {r['check']}")
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed. Report: {out}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
