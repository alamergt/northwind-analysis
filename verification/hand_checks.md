# Hand checks (plan.md §8.2)

Each figure below was read cell by cell from `data/Northwind Database.xlsx` (openpyxl, no pandas), worked out by hand, and compared with the pipeline's output. All seven match.

To repeat a check in Excel: filter `Orders Details` by `OrderID` (or `Orders` by `ShipVia`), and use `UnitPrice × Quantity × (1 − Discount)` with the discount rounded to 2 decimals.

| # | Item | Worked by hand from raw cells | Pipeline | Match |
|---|---|---|---|---|
| 1 | Order 10264 (discounted line) | 15.20 × 35 = 532.00; 7.70 × 25 × (1 − 0.15) = 163.63; **net $695.62**, 2 lines, 60 units, freight $3.67, shipped 23 Aug 1996 | $695.62, 2 lines, 60 units, $3.67, 23 Aug 1996 | Yes |
| 2 | Order 11008 (unshipped) | 3 lines, 181 units, **net $4,680.90**, freight $79.46, no ship date | $4,680.90, 3 lines, 181 units, $79.46, not shipped | Yes |
| 3 | Order 11077 (most lines) | 25 lines, 72 units, **net $1,255.72**, freight $8.53, no ship date | $1,255.72, 25 lines, 72 units, $8.53, not shipped | Yes |
| 4 | Côte de Blaye (Q2 rank 1) | 17 in stock, 0 on order; 130 units ordered 6 Feb–6 May 1998 → 130 × 30.44 / 90 = **43.97 / month**; 17 / 43.97 = **0.387 months** | 43.97 / month, 0.387 months, rank 1, Critical | Yes |
| 5 | Camembert Pierrot (Q2 rank 2) | 19 in stock, 0 on order, no reorder level; 386 units → **130.55 / month**; **0.146 months** | 130.55 / month, 0.146 months, rank 2, Critical | Yes |
| 6 | Germany, Q1 1998 net revenue (customer country) | **$54,893.31** | $54,893.3 (`q1_quarterly.csv`, 6 significant digits) | Yes |
| 7 | United Package, shipped orders and freight (largest raw freight gap in Q3) | **315 orders, $27,556.76** | 315 orders, $27,556.76 | Yes |

## Public site check in a private window (gate 7, to be completed by you)

Open the page URL and the repository URL in a private / incognito window with no sign-ins, and tick each:

- [ ] The page loads with no sign-in prompt
- [ ] All three primary charts render, and each supporting chart renders when its section is expanded
- [ ] The technical appendix sections open
- [ ] The link to the repository works
- [ ] The layout works at phone width (no sideways page scroll)
- [ ] The page follows dark mode when the device is in dark mode
- [ ] The repository page and README load without signing in

Result and date: _to be filled in_
