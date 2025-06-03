
  
    

  create  table "ecommerce_cloud"."dev_walmart"."dim_customers__dbt_tmp"
  
  
    as
  
  (
    


select customer_id, segment_id, signup_date, last_purchase_date
from "ecommerce_cloud"."dev_walmart"."stg_cust1"

UNION ALL

select customer_id, segment_id, signup_date, last_purchase_date
from "ecommerce_cloud"."dev_walmart"."stg_cust2"
  );
  