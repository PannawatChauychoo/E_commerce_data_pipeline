{{ config(materialized='table') }}

SELECT
    l.customer_id,
    c.segment_id,
    c.visit_prob,
    c.age,
    c.gender,
    c.city_category,
    c.stay_in_current_city_years,
    c.marital_status,
    c.signup_date,
    c.last_purchase_date
FROM {{ ref('stg_cust1') }} AS c
INNER JOIN {{ ref('stg_customers_lookup') }} AS l
    ON c.unique_id = l.cust1_id
