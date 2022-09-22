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
<table>
<tr>
    <td align="center" style="word-wrap: break-word; width: 150.0; height: 150.0">
        <a href=https://github.com/degagawolde>
            <img src=https://avatars.githubusercontent.com/u/39334921?v=4 width="100;"  style="border-radius:50%;align-items:center;justify-content:center;overflow:hidden;padding-top:10px" alt=Degaga Wolde/>
            <br />
            <sub style="font-size:14px"><b>Degaga Wolde</b></sub>
        </a>
    </td>
</tr>
</table>

[contributors-shield]: https://img.shields.io/github/contributors/Hen0k/data-warehouse-dbt-airflow-postgress.svg?style=for-the-badge
[my-profile]: https://github.com/degagawolde
[contributors-url]: https://github.com/degagawolde/data-warehouse-dbt-airflow-postgress/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/Hen0k/data-warehouse-dbt-airflow-postgress.svg?style=for-the-badge
[forks-url]: https://github.com/degagawolde/data-warehouse-dbt-airflow-postgress/network/members
[stars-shield]: https://img.shields.io/github/stars/Hen0k/data-warehouse-dbt-airflow-postgress.svg?style=for-the-badge
[stars-url]: https://github.com/degagawolde/data-warehouse-dbt-airflow-postgress/stargazers
[issues-shield]: https://img.shields.io/github/issues/Hen0k/data-warehouse-dbt-airflow-postgress.svg?style=for-the-badge
[issues-url]: https://github.com/degagawolde/data-warehouse-dbt-airflow-postgress/issues
[license-shield]: https://img.shields.io/github/license/Hen0k/data-warehouse-dbt-airflow-postgress.svg?style=for-the-badge
[license-url]: https://github.com/degagawolde/data-warehouse-dbt-airflow-postgress/blob/master/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/degagawolde/
[redash-install-blog]: https://www.techrepublic.com/article/how-to-deploy-redash-data-visualization-dashboard-help-docker/
[redash-basics]: https://hevodata.com/learn/redash/
[hosting-dbt-docs]: https://amchoi.medium.com/hosting-dbt-documentation-in-gcp-aa529d4f3bb8
