{{ config(materialized='table') }}

WITH calendar AS (
  SELECT * FROM (
    {{ dbt_utils.date_spine(
         datepart   = "day",
         start_date = "cast('01/01/2023' as date)",
         end_date   = "current_date"
    ) }}
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
