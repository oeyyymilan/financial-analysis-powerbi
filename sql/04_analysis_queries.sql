USE financial_analysis;

-- 1. MoM revenue growth
SELECT period, revenue,
       ROUND(100*(revenue - LAG(revenue) OVER (ORDER BY period)) / LAG(revenue) OVER (ORDER BY period),2) AS mom_growth_pct
FROM vw_monthly_pnl;

-- 2. Top 10 customers by revenue
SELECT customer_name, segment, ROUND(SUM(amount),2) AS revenue
FROM vw_transactions WHERE category_type='Revenue' AND status='Completed'
GROUP BY customer_id, customer_name, segment ORDER BY revenue DESC LIMIT 10;

-- 3. Failed transaction rate by payment mode
SELECT payment_mode, COUNT(*) AS total,
       ROUND(100*SUM(status='Failed')/COUNT(*),2) AS failed_pct
FROM vw_transactions GROUP BY payment_mode ORDER BY failed_pct DESC;

-- 4. Expense breakdown
SELECT category_name, ROUND(SUM(amount),2) AS spend,
       ROUND(100*SUM(amount)/SUM(SUM(amount)) OVER (),2) AS share_pct
FROM vw_transactions WHERE category_type='Expense' AND status='Completed'
GROUP BY category_name ORDER BY spend DESC;
