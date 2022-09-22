from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.decorators import task, dag
from datetime import datetime
from docker.types import Mount

@dag(
    # owner="pneuma",
     start_date=datetime.now(),
     schedule_interval='@hourly',
     catchup=False)
def docker_dag():
    start_dag = DummyOperator(
        task_id='start_dag'
        )

    end_dag = DummyOperator(
        task_id='end_dag'
        )   
    el_task = DockerOperator(
        task_id='extract_and_load',
        image='pneuma/eltaskdag:v1.0.0',
        container_name="eltaskdag",
        docker_url='unix://var/run/docker.sock',
        network_mode='dwh-network',
        mounts=[
            Mount(
                target='/scripts/data', 
                source='/home/henok/dev-env/10academy/week-11/data-warehouse-dbt-airflow-postgress/data', 
                type="bind") # https://stackoverflow.com/questions/64947706/mounting-directories-using-docker-operator-on-airflow-is-not-working
            ],
    )
    start_dag >> el_task >> end_dag

dag = docker_dag()
