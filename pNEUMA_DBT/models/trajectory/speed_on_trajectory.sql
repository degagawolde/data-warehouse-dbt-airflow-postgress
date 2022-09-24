{{ config(materialized='view') }}

with source_data as (

    select * from trajectories where speed>40

)

select *
from source_data