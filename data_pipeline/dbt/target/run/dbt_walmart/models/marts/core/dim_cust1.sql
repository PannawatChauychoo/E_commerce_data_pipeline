
  
    

  create  table "ecommerce_cloud"."dev_walmart"."dim_cust1__dbt_tmp"
  
  
    as
  
  (
    

SELECT
l.customer_id, c.segment_id, c.visit_prob,
c.signup_date, c.last_purchase_date
FROM "ecommerce_cloud"."dev_walmart"."stg_cust1" AS c JOIN "ecommerce_cloud"."dev_walmart"."stg_customers_lookup" AS l
ON c.customer_id = l.external_id
WHERE l.cust_type = 'Cust1'
  );
  