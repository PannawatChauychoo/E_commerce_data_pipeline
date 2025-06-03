select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select transaction_id
from "ecommerce_cloud"."dev_walmart"."fct_order"
where transaction_id is null



      
    ) dbt_internal_test