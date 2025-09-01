select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select unique_id
from "ecommerce_cloud"."dev_walmart"."dim_cust1_ext"
where unique_id is null



      
    ) dbt_internal_test