{{ config(materialized='table') }}


select customer_id, segment_id, signup_date, last_purchase_date
from {{ ref('stg_cust1') }}

UNION ALL

select customer_id, segment_id, signup_date, last_purchase_date
from {{ ref('stg_cust2') }}

