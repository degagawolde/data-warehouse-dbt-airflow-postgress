{{ config(materialized='view') }}


with avg_speed_at_each_time as (
    select *
        from {{ref('speed_on_trajectory')}}   
        group by time
        order by speed DESC
)

select *
from avg_speed_at_each_time
