

SELECT
    unique_id,
    segment_id,
    branch,
    city,
    customer_type,
    gender,
    payment_method,
    created_at AS signup_date,
    updated_at AS last_purchase_date
FROM "ecommerce_cloud"."walmart"."cust2"
WHERE unique_id IS NOT NULL