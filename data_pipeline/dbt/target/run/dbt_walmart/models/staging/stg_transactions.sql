
  create view "ecommerce_cloud"."dev_walmart"."stg_transactions__dbt_tmp"
    
    
  as (
    

SELECT
    transaction_id,
    unique_id AS customer_id,
    product_id,
    unit_price,
    quantity,
    date_purchased,
    category,
    unit_price * quantity AS total_amount,
    created_at
FROM "ecommerce_cloud"."walmart"."transactions"
WHERE transaction_id IS NOT NULL
  );