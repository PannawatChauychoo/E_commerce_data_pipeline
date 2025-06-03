{{ config(materialized='table') }}

SELECT
product_id, category, unit_price, stock, 
lead_days, ordering_cost, holding_cost_per_unit,
EOQ, created_at, updated_at
FROM {{ ref('stg_products') }} 