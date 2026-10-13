USE financial_analysis;

-- Flat view for Power BI (single clean source)
CREATE OR REPLACE VIEW vw_transactions AS
SELECT t.transaction_id, d.full_date, d.year, d.quarter, d.month_num, d.month_name, d.period,
       t.customer_id, c.customer_name, c.segment, t.region,
       k.category_name, k.category_type, t.amount, t.payment_mode, t.status
FROM fact_transactions t
JOIN dim_date d     ON d.date_key = t.date_key
JOIN dim_category k ON k.category_id = t.category_id
LEFT JOIN dim_customer c ON c.customer_id = t.customer_id;

-- Monthly P&L
CREATE OR REPLACE VIEW vw_monthly_pnl AS
SELECT period,
       SUM(CASE WHEN category_type='Revenue' THEN amount ELSE 0 END) AS revenue,
       SUM(CASE WHEN category_type='Expense' THEN amount ELSE 0 END) AS expenses,
       SUM(CASE WHEN category_type='Revenue' THEN amount ELSE -amount END) AS net_profit,
       ROUND(100*SUM(CASE WHEN category_type='Revenue' THEN amount ELSE -amount END)
             / NULLIF(SUM(CASE WHEN category_type='Revenue' THEN amount END),0), 2) AS profit_margin_pct
FROM vw_transactions
WHERE status = 'Completed'
GROUP BY period;

-- Revenue by segment & region
CREATE OR REPLACE VIEW vw_revenue_by_segment AS
SELECT segment, region, ROUND(SUM(amount),2) AS revenue, COUNT(*) AS txn_count
FROM vw_transactions
WHERE category_type='Revenue' AND status='Completed'
GROUP BY segment, region;
