
    
    

select
    order_id as unique_field,
    count(*) as n_records

from "ecommerce_cloud"."dev_walmart"."fct_order"
where order_id is not null
group by order_id
having count(*) > 1


