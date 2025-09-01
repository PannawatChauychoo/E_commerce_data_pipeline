
  create view "ecommerce_cloud"."dev_walmart"."dim_customers__dbt_tmp"
    
    
  as (
    with lkp as (select * from "ecommerce_cloud"."dev_walmart"."stg_customers_lookup"),

c1 as (select * from "ecommerce_cloud"."dev_walmart"."stg_cust1"),

c2 as (select * from "ecommerce_cloud"."dev_walmart"."stg_cust2")

select
    lkp.customer_id,
    lkp.segment_id,
    lkp.run_id,
    case when c1.unique_id is not null then 'cust1' else 'cust2' end
        as source_system,
    coalesce(c1.signup_date, c2.signup_date) as signup_date,
    current_timestamp as record_loaded_at
from lkp
left join c1 on lkp.cust1_id = c1.unique_id
left join c2 on lkp.cust2_id = c2.unique_id
  );