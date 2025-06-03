
  
    

  create  table "ecommerce_cloud"."dev_walmart_analytics"."kpi_clv__dbt_tmp"
  
  
    as
  
  (
    

WITH customer_clv AS (
    SELECT 
    customer_id,
    SUM(total_amount) as total_amount,
    COUNT(DISTINCT transaction_id) AS total_orders,
    MIN(d.real_date) as first_purchase_date,
    MAX(d.real_date) as last_purchase_date

    FROM "ecommerce_cloud"."dev_walmart"."fct_order" ft JOIN "ecommerce_cloud"."dev_walmart"."dim_date" d ON ft.date_key = d.date_key
    GROUP BY customer_id
)

SELECT
customer_id,
total_amount,
total_orders,
EXTRACT(DAY FROM AGE(last_purchase_date, first_purchase_date)) AS lifetime_days
FROM customer_clv
  );
  