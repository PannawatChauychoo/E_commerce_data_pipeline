select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select visit_prob
from "ecommerce_cloud"."dev_walmart"."dim_cust1"
where visit_prob is null



      
    ) dbt_internal_test