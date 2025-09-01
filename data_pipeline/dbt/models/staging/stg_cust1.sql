{{ config(materialized='view') }}

SELECT
    unique_id,
    segment_id,
    age,
    gender,
    city_category,
    stay_in_current_city_years,
    marital_status,
    visit_prob,
    created_at AS signup_date,
    updated_at AS last_purchase_date
FROM {{ source('walmart', 'cust1') }}
WHERE unique_id IS NOT NULL
