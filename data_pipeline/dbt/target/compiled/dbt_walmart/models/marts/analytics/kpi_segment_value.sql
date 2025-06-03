-- Calculate lifetime total value for each segment: Sum of purchases for each segment



SELECT
    segment_id,
    SUM(total_amount) AS total_spent,
    COUNT(DISTINCT transaction_id) AS total_orders,
    RANK () OVER (ORDER BY SUM(total_amount) DESC) AS rank
FROM "ecommerce_cloud"."dev_walmart"."fct_order"
GROUP BY segment_id
ORDER BY rank