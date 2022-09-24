import sys
from typing_extensions import Self

from scripts.data_reader import DataReader
from scripts.postgress_manager import create_tables, insert_data

from datetime import datetime, timedelta
import pandas as pd
import os

dag_path = os.getcwd()

TRAJECTORY_SCHEMA = os.path.join(
    dag_path, "dags/scripts/trajectory_info_schema.sql")
VEHICLE_SCHEMA = os.path.join(dag_path, "dags/scripts/vehicle_info_schema.sql")

class ELT:
    def __init__(self, read_dag_path,save_dag_path):
        self.read_dag_path = read_dag_path
        self.save_dag_path = save_dag_path

    def extract_data(self,file_path=None,) -> None:
        if file_path is not None:
            self.read_dag_path = file_path
            
        reader = DataReader()
        vehicle_df, trajectories_df = reader.get_dfs(
            file_path=self.read_dag_path, v=0)
        
        vehicle_df.to_csv(os.path.join(self.save_dag_path,'vehicle_info.csv'),index=False)
        trajectories_df.to_csv(os.path.join(self.save_dag_path,'trajectories_info.csv'), index=False)

    def load_trajectory_data(self):
        trajectories_df = pd.read_csv(os.path.join(self.save_dag_path, 'trajectories_info.csv'))
        create_tables(TRAJECTORY_SCHEMA)
        print('create trajectory table')
        insert_data(trajectories_df[:10000], "trajectories")
    
    def load_vehicle_data(self):
        vehicle_df = pd.read_csv(os.path.join(
            self.save_dag_path, 'vehicle_info.csv'))
        create_tables(VEHICLE_SCHEMA)
        print('create vehicle table')
        insert_data(vehicle_df, "vehicles")
        
    def execution_date_to_millis(self, execution_date):
        """converts execution date (in DAG timezone) to epoch millis

        Args:
            date (execution date): %Y-%m-%d

        Returns:
            milliseconds
        """
        date = datetime.strptime(execution_date, "%Y-%m-%d")
        epoch = datetime.utcfromtimestamp(0)
        return (date - epoch).total_seconds() * 1000.0
