
    
    

select
    unique_id as unique_field,
    count(*) as n_records

from "ecommerce_cloud"."dev_walmart"."dim_cust1_ext"
where unique_id is not null
group by unique_id
having count(*) > 1


