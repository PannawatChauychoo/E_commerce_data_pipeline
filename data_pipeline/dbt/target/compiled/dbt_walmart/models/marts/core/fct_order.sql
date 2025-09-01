

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
    from "ecommerce_cloud"."dev_walmart"."stg_transactions" as t
    inner join
        "ecommerce_cloud"."dev_walmart"."dim_customers" as dl
        on t.customer_id = dl.customer_id

)

select * from source_data

