{{ config(materialized='view') }}

SELECT
unique_id AS customer_id, segment_id,
branch, city, customer_type, gender, payment_method,
created_at AS signup_date, updated_at AS last_purchase_date
FROM {{ source('walmart', 'cust2_demographics') }}
WHERE unique_id IS NOT NULL