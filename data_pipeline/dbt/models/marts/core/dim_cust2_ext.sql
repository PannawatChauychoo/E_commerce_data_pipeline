{{ config(materialized='table') }}

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
FROM {{ ref('stg_cust2') }} AS c
INNER JOIN {{ ref('stg_customers_lookup') }} AS l
    ON c.unique_id = l.cust2_id
