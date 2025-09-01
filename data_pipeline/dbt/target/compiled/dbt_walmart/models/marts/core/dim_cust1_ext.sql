

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
FROM "ecommerce_cloud"."dev_walmart"."stg_cust1" AS c
INNER JOIN "ecommerce_cloud"."dev_walmart"."stg_customers_lookup" AS l
    ON c.unique_id = l.cust1_id