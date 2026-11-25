# Northwind: markets, stock and logistics

An analysis of the Northwind sample database (830 orders, July 1996 – May 1998) that answers three questions a manager can act on. Everything is built from the workbook by one Python command, tested, and recalculated independently in SQL.

**Read the results:** https://alamergt.github.io/northwind-analysis/

## The three questions

| # | Question | Key finding | Recommended action |
|---|---|---|---|
| 1 | Which markets grew or declined, which accounts drove it, and where should sales attention go? | Revenue grew +80% (+42% to +116% depending on the quarters compared). Germany clearly gained share; Central Europe, France and Other North America clearly lost it; Brazil, UK & Ireland and the Nordics change direction depending on the period. | Confirmed: call Mère Paillarde (Other North America) and Blondel père et fils (France) to find out why orders fell. Tentative: actions for Germany, Brazil, UK & Ireland, Central Europe and the Nordics (listed with reasons on the page). |
| 2 | Which active products should purchasing restock first? | Stock covers less than a month of recent demand for 38 of 69 active products; 32 are Critical or High (assuming the undated stock count reflects 6 May 1998). | Order the top 10 now (roughly 215–606 units); set reorder levels for 16 products; verify 13 possible shortages. |
| 3 | How do processing times and freight costs vary across shipments, and where are the biggest opportunities? | Dispatch takes 6–7 days for nearly every order; 14-day orders aren't processed faster, so 18% go out late (95% range 10–28%) vs 4%. Freight comparisons between carriers are inconclusive. | Sort dispatch by required date; find out why United Package and Speedy Express shipments more often wait over 18 days. |

**Top three management priorities** (ranked on the page by certainty, money at stake and speed):
1. **Purchasing:** restock the top 10 products, starting with the top 5 and the quantities shown under the stock chart.
2. **Operations:** put short-deadline orders first in the dispatch queue.
3. **Sales:** call Mère Paillarde and Blondel père et fils to find out why their orders fell.

The page is the source of truth; these figures are copied from it at publication. Recommendations are directional: order volumes per market are small, the stock snapshot is undated, and dates record dispatch rather than delivery.

## Reproduce

Requires Python 3.13.

```bash
git clone https://github.com/alamergt/northwind-analysis.git
cd northwind-analysis
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_analysis.py             # rebuilds outputs/ and docs/index.html
python -m pytest                   # unit, integration and end-to-end tests
```

`run_analysis.py` exits with an error if any independent SQL cross-check fails.

## How it's checked

- **Tests** (`tests/`): unit tests on a small made-up workbook with hand-worked answers, integration tests against known totals of the real workbook, and end-to-end tests that rebuild the whole page twice and confirm identical output.
- **Independent recalculation** (`verification/sql_crosscheck.py`): reads the workbook cell by cell with openpyxl and recomputes every headline figure in plain SQL, sharing no code with the pandas pipeline.
- **Hand checks** (`verification/hand_checks.md`): sample orders, products and totals worked out from raw cells.
- **Independent review** (`verification/fresh_review.md`): a reviewer that hadn't seen the conclusions tried to break the headline claims; objections and how each was resolved are listed there and in the page's appendix.
- **CI** (`.github/workflows/ci.yml`): on every push, installs the pinned versions, runs the tests, rebuilds everything and fails if the committed page differs from the rebuild.

## Repository layout

```
data/            input workbook (never modified) and its licence notice
northwind/       analysis package: load, clean, model, metrics, q1/q2/q3, charts, report
templates/       HTML template for the page
run_analysis.py  single entry point
tests/           unit, integration and end-to-end tests
verification/    SQL cross-check, hand checks, review notes, CI page check
outputs/         generated tables and run manifest (not edited by hand)
docs/            the published page (generated)
plan.md          the analysis plan, including every decision made along the way
```

## Licences

Code: MIT (see `LICENSE`). Data: Microsoft's Northwind sample, MIT-licensed; see `data/NOTICE.md`.
