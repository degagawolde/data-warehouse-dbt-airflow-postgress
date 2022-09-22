# data-warehouse-dbt-airflow-postgres-redash

[![Contributors][contributors-shield]][contributors-url][![Forks][forks-shield]][forks-url][![Stargazers][stars-shield]][stars-url][![Issues][issues-shield]][issues-url][![MIT License][license-shield]][license-url][![LinkedIn][linkedin-shield]][linkedin-url]
A data-warehouse built for the pNEUMA open dataset of naturalistic trajectories of half a million vehicles collected by a swarm of drones in a congested downtown area of Athens, Greece. 

# Data

The data is initially a video feed of drones tracking different vehicles on the road. Then this was turned into a trajectory describing format. In our data the vehicles are described with 4 columns, and the trajectories are described with 6 repeating columns that change with approximately 4 second time interval.

For each .csv file the following apply:

- Each row represents the data of a single vehicle
- The first 10 columns in the 1st row include the columns’ names (track_id; type; traveled_d; avg_speed; lat; lon; speed; lon_acc; lat_acc; time)
- The first 4 columns include information about the trajectory like the unique trackID, the type of vehicle, the distance traveled in meters and the average speed of the vehicle in km/h
- The last 6 columns are then repeated every 6 columns based on the time frequency. For example, column_5 contains the latitude of the vehicle at time column_10, and column_11 contains the latitude of the vehicle at time column_16.
- Speed is in km/h, Longitudinal and Lateral Acceleration in m/sec2 and time in second

# Installation and Steps

## Airflow
- Create the data extraction and loading module
- Containerize the module
- Run Airflow in a container
-  Modify the compose file to use multiple database users
-  Create an Airflow DAG with a DockerOperator
-  Test that the workflow actually populates the 
containerized database

 ## DBT
-  Locally install dbt
-  Connect dbt to the db and run models
-  Generate dbt docs with Airflow
-  Run dbt models as Airflow DAGs
-  Containerized dbt with the rest

## Redash
- Install and connect Redash
- Create sample visualization
- Containerized Redash with the rest

## dev,stage, prod
 Create a dev, staging, and production area for the database.

### Contributors
