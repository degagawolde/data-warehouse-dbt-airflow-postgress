{{ config(materialized='view') }}

with source_data as (

    select * from vehicles where avg_speed>40

)

select *
from source_data