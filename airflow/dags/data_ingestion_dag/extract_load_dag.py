# We'll start by importing the DAG object
from datetime import timedelta, datetime
from pathlib import Path

from airflow import DAG
# We need to import the operators used in our tasks
from airflow.operators.python_operator import PythonOperator
# We then import the days_ago function
from airflow.utils.dates import days_ago

import pandas as pd
import sqlite3
import os,sys

# get dag directory path
dag_path = os.getcwd()
sys.path.append('./scripts')

from scripts.extract_load import ELT

elt = ELT(read_dag_path=f"{dag_path }/raw_data/20181024_d1_0830_0900.csv",
         save_dag_path=f"{dag_path }/processed_data/")

# initializing the default arguments that we'll pass to our DAG
default_args = {
    'owner': 'airflow',
    'start_date': days_ago(5)
}

ingestion_dag = DAG(
    'traffic_data_ingestion',
    default_args=default_args,
    description='Aggregates booking records for data analysis',
    schedule_interval=timedelta(hours=1),
    catchup=False,
    user_defined_macros={'date_to_millis': elt.execution_date_to_millis}
)

task_1 = PythonOperator(
    task_id='etract_data',
    python_callable=elt.extract_data,
    # op_args=["{{ ds }} {{ execution_date.hour }}"],
    dag=ingestion_dag,
)

task_2 = PythonOperator(
    task_id='load_vehicle_data',
    python_callable=elt.load_vehicle_data,
    # op_args=["{{ ds }} {{ execution_date.hour }}"],
    dag=ingestion_dag,
)

task_3 = PythonOperator(
    task_id='load_trajectory_data',
    python_callable=elt.load_trajectory_data,
    # op_args=["{{ ds }} {{ execution_date.hour }}"],
    dag=ingestion_dag,
)

task_1 >> task_2 
task_1 >> task_3
