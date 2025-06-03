
  
    

  create  table "ecommerce_cloud"."dev_walmart_analytics"."kpi_purchase_frequency__dbt_tmp"
  
  
    as
  
  (
    

WITH last_30_days AS (

  -- pick the calendar dates you want (using your dim_date model)
  SELECT
    date_key,
    real_date AS order_date
  FROM "ecommerce_cloud"."dev_walmart"."dim_date"
)

SELECT
  d.order_date,
  COALESCE(COUNT(o.transaction_id), 0) AS order_count

FROM last_30_days d LEFT JOIN "ecommerce_cloud"."dev_walmart"."fct_order" o
ON o.date_key = d.date_key     -- join via the integer surrogate key

GROUP BY d.order_date
ORDER BY d.order_date
  );
  