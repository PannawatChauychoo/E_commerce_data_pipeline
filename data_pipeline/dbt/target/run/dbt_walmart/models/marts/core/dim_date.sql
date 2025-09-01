
  
    

  create  table "ecommerce_cloud"."dev_walmart"."dim_date__dbt_tmp"
  
  
    as
  
  (
    

WITH calendar AS (
  SELECT * FROM (
    





with rawdata as (

    

    

    with p as (
        select 0 as generated_number union all select 1
    ), unioned as (

    select

    
    p0.generated_number * power(2, 0)
     + 
    
    p1.generated_number * power(2, 1)
     + 
    
    p2.generated_number * power(2, 2)
     + 
    
    p3.generated_number * power(2, 3)
     + 
    
    p4.generated_number * power(2, 4)
     + 
    
    p5.generated_number * power(2, 5)
     + 
    
    p6.generated_number * power(2, 6)
     + 
    
    p7.generated_number * power(2, 7)
     + 
    
    p8.generated_number * power(2, 8)
     + 
    
    p9.generated_number * power(2, 9)
    
    
    + 1
    as generated_number

    from

    
    p as p0
     cross join 
    
    p as p1
     cross join 
    
    p as p2
     cross join 
    
    p as p3
     cross join 
    
    p as p4
     cross join 
    
    p as p5
     cross join 
    
    p as p6
     cross join 
    
    p as p7
     cross join 
    
    p as p8
     cross join 
    
    p as p9
    
    

    )

    select *
    from unioned
    where generated_number <= 974
    order by generated_number



),

all_periods as (

    select (
        

    cast('01/01/2023' as date) + ((interval '1 day') * (row_number() over (order by 1) - 1))


    ) as date_day
    from rawdata

),

filtered as (

    select *
    from all_periods
    where date_day <= current_date

)

select * from filtered


  ) AS date_spine
)


SELECT
  date_day                                   AS real_date,          -- 2025‑05‑04
  TO_CHAR(date_day, 'YYYYMMDD')::int         AS date_key,
  EXTRACT(YEAR  FROM date_day)::int          AS year,
  EXTRACT(MONTH FROM date_day)::int          AS month,
  EXTRACT(DAY   FROM date_day)::int          AS day,
  TO_CHAR(date_day, 'Day')                   AS weekday_name   

FROM calendar
  );
  