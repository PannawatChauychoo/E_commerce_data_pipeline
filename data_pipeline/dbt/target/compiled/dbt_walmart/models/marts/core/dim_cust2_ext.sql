

SELECT
l.customer_id, c.segment_id,
branch, city, customer_type, gender, payment_method,
c.signup_date, c.last_purchase_date
FROM "ecommerce_cloud"."dev_walmart"."stg_cust2" AS c JOIN "ecommerce_cloud"."dev_walmart"."stg_customers_lookup" AS l
ON c.customer_id = l.external_id
WHERE l.cust_type = 'Cust2'