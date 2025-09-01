{{  
  config(
    materialized = 'incremental',
    unique_key   = ['date_key','customer_id','product_id','transaction_id']
  )  
}}

with source_data as (

    select
    /* your source columns, renamed to match your fact */
        to_char(t.date_purchased, 'YYYYMMDD')::int as date_key,
        t.customer_id,
        dl.segment_id,
        t.product_id,
        t.transaction_id,
        t.quantity,
        t.unit_price,
        t.category
    from {{ ref('stg_transactions') }} as t
    inner join
        {{ ref('dim_customers') }} as dl
        on t.customer_id = dl.customer_id

)

select * from source_data

{% if is_incremental() %}

    -- only bring in rows newer than your last loaded batch
    where
        (date_key, customer_id, product_id, transaction_id)
        not in (
            select
                date_key,
                customer_id,
                product_id,
                transaction_id
            from {{ this }}
        )

{% endif %}
