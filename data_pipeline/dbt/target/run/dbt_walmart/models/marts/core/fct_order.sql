
      
  
    

  create  table "ecommerce_cloud"."dev_walmart"."fct_order__dbt_tmp"
  
  
    as
  
  (
    

with source_data as (

  select
    /* your source columns, renamed to match your fact */
    to_char(date_purchased, 'YYYYMMDD')::int  AS date_key,
    t.customer_id,
    dl.segment_id,                                 
    t.product_id,
    t.transaction_id,
    t.quantity,
    t.total_amount
  from "ecommerce_cloud"."dev_walmart"."stg_transactions" t
  JOIN "ecommerce_cloud"."dev_walmart"."dim_customers" dl ON t.customer_id = dl.customer_id

)

select * from source_data


  );
  
  