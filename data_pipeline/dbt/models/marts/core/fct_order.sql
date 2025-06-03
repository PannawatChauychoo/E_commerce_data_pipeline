{{  
  config(
    materialized = 'incremental',
    unique_key   = ['date_key','customer_id','product_id','transaction_id']
  )  
}}

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
  from {{ ref('stg_transactions') }} t
  JOIN {{ ref('dim_customers') }} dl ON t.customer_id = dl.customer_id

)

select * from source_data

{% if is_incremental() %}

  -- only bring in rows newer than your last loaded batch
    where (date_key, customer_id, product_id, transaction_id)
    not in (
        select date_key, customer_id, product_id, transaction_id
        from {{ this }}
    )

{% endif %}