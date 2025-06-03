with relation_columns as (

        
        select
            cast('REAL_DATE' as TEXT) as relation_column,
            cast('TIMESTAMP WITHOUT TIME ZONE' as TEXT) as relation_column_type
        union all
        
        select
            cast('DATE_KEY' as TEXT) as relation_column,
            cast('INTEGER' as TEXT) as relation_column_type
        union all
        
        select
            cast('YEAR' as TEXT) as relation_column,
            cast('INTEGER' as TEXT) as relation_column_type
        union all
        
        select
            cast('MONTH' as TEXT) as relation_column,
            cast('INTEGER' as TEXT) as relation_column_type
        union all
        
        select
            cast('DAY' as TEXT) as relation_column,
            cast('INTEGER' as TEXT) as relation_column_type
        union all
        
        select
            cast('WEEKDAY_NAME' as TEXT) as relation_column,
            cast('TEXT' as TEXT) as relation_column_type
        
        
    ),
    test_data as (

        select
            *
        from
            relation_columns
        where
            relation_column = 'DATE_DAY'
            and
            relation_column_type not in ('DATE', 'DATETIME')

    )
    select *
    from test_data