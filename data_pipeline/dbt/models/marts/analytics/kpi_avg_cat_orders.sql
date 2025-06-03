{{ config(materialized='table', schema='analytics') }}


SELECT
    category,
    SUM(total_amount) AS total_spent,
    COUNT(DISTINCT ft.transaction_id) AS total_orders,
    AVG(total_amount) AS avg_order_value
FROM {{ ref('fct_order') }} ft JOIN {{ ref('dim_products') }} p 
ON ft.product_id = p.product_id
GROUP BY category