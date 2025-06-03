
  create view "ecommerce_cloud"."dev_walmart"."stg_customers_lookup__dbt_tmp"
    
    
  as (
    

SELECT
customer_id, external_id, cust_type, segment_id
FROM "ecommerce_cloud"."walmart"."customers_lookup"
WHERE external_id IS NOT NULL AND cust_type IS NOT NULL
  );