
  
    

  create  table "ecommerce_cloud"."dev_walmart"."dim_cust2_ext__dbt_tmp"
  
  
    as
  
  (
    

SELECT
    l.customer_id,
    c.segment_id,
    c.branch,
    c.city,
    c.customer_type,
    c.gender,
    c.payment_method,
    c.signup_date,
    c.last_purchase_date
FROM "ecommerce_cloud"."dev_walmart"."stg_cust2" AS c
INNER JOIN "ecommerce_cloud"."dev_walmart"."stg_customers_lookup" AS l
    ON c.unique_id = l.cust2_id
  );
  