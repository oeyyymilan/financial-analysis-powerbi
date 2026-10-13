-- Run from repo root: mysql -u root -p --local-infile=1 financial_analysis < sql/02_load_data.sql
SET GLOBAL local_infile = 1;
LOAD DATA LOCAL INFILE 'data/dim_date.csv' INTO TABLE dim_date
  FIELDS TERMINATED BY ',' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/dim_category.csv' INTO TABLE dim_category
  FIELDS TERMINATED BY ',' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/dim_customer.csv' INTO TABLE dim_customer
  FIELDS TERMINATED BY ',' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'data/fact_transactions.csv' INTO TABLE fact_transactions
  FIELDS TERMINATED BY ',' IGNORE 1 LINES;
