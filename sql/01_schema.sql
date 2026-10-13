-- MySQL 8+ | Run: mysql -u root -p --local-infile=1 < sql/01_schema.sql
CREATE DATABASE IF NOT EXISTS financial_analysis;
USE financial_analysis;

DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_category;
DROP TABLE IF EXISTS dim_date;

CREATE TABLE dim_date (
  date_key INT PRIMARY KEY, full_date DATE NOT NULL, year SMALLINT, quarter TINYINT,
  month_num TINYINT, month_name VARCHAR(12), period CHAR(7), day_name VARCHAR(10), is_weekend TINYINT
);
CREATE TABLE dim_category (
  category_id INT PRIMARY KEY, category_name VARCHAR(50) NOT NULL,
  category_type ENUM('Revenue','Expense') NOT NULL
);
CREATE TABLE dim_customer (
  customer_id INT PRIMARY KEY, customer_name VARCHAR(80), segment VARCHAR(20),
  region VARCHAR(10), join_date DATE
);
CREATE TABLE fact_transactions (
  transaction_id INT PRIMARY KEY, date_key INT NOT NULL, customer_id INT NULL,
  category_id INT NOT NULL, region VARCHAR(10), amount DECIMAL(12,2) NOT NULL,
  payment_mode VARCHAR(20), status ENUM('Completed','Pending','Failed') NOT NULL,
  FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
  FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
  FOREIGN KEY (category_id) REFERENCES dim_category(category_id),
  INDEX idx_date (date_key), INDEX idx_cat (category_id), INDEX idx_status (status)
);
