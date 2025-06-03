select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select signup_date
from "ecommerce_cloud"."dev_walmart"."dim_cust1"
where signup_date is null



      
    ) dbt_internal_test