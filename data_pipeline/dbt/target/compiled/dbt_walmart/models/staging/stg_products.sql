

SELECT
    product_id,
    category,
    unit_price,
    stock,
    lead_days,
    ordering_cost,
    holding_cost_per_unit,
    eoq,
    created_at,
    updated_at
FROM "ecommerce_cloud"."walmart"."products"
WHERE product_id IS NOT NULL