{{ config(materialized='view') }}


with fastest_and_longest_distance as (
    select *

        from {{ref('fastest_veh_dbt_model')}} 
        
        order by 
            traveled_distance DESC
)

select *
from fastest_and_longest_distance
