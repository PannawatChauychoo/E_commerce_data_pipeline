

SELECT
    customer_id,
    cust1_id,
    cust2_id,
    segment_id,
    run_id
FROM "ecommerce_cloud"."walmart"."customers_lookup"
WHERE cust1_id IS NOT NULL OR cust2_id IS NOT NULL