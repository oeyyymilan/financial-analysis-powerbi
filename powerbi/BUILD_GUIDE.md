# Power BI Build Guide (Power BI Desktop — free)

## 1. Connect data
- Get Data → **MySQL database** (server `localhost`, db `financial_analysis`) → select view `vw_transactions` (+ `vw_monthly_pnl`).
- No MySQL? Get Data → Text/CSV → load `data/dim_date.csv` and build the same model, or export `vw_transactions` to CSV.
- Create a `Date` table: use `data/dim_date.csv` or `Date = CALENDARAUTO()`. Mark as Date table (column `full_date`).
- Relationship: `Date[full_date]` 1 → * `vw_transactions[full_date]`.

## 2. Add measures
New table `_Measures` → paste each measure from `measures.dax` (12 total).

## 3. Page 1 — Executive Overview (6 visuals)
1. Card — Total Revenue
2. Card — Total Expenses
3. Card — Net Profit
4. Card — Profit Margin %
5. Card — Avg Transaction Value
6. Line chart — Revenue vs Expenses by `period`
7. Clustered bar — Revenue by `segment`
8. Donut — Expenses by `category_name`
9. Slicers — Year, Region, Segment

## 4. Page 2 — Transaction Analysis (drill-through)
1. Matrix — `category_name` × `year` → Total Revenue (with drill down to month)
2. Column chart — Failed Txn Rate % by `payment_mode`
3. Table — customer_name, Total Revenue, Transaction Count (Top 10 filter)
4. Line — Revenue YTD and Revenue LY
5. Gauge/Card — Revenue YoY %
6. Drill-through: right-click `segment` or `customer_name` → set as drill-through target on Page 2
- Add Back button, sync slicers across pages (View → Sync slicers).

## 5. Export
Save as `powerbi/Financial_Analysis.pbix`, take screenshots into `/screenshots`, commit.
