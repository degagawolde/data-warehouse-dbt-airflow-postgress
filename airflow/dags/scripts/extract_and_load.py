import sys
sys.path.append("/scritps")
from data_reader import DataReader
from postgress_manager import create_tables, insert_data


def extract_load(file_path=None) -> None:
    file_path = file_path
    reader = DataReader()
    vehicle_df, trajectories_df = reader.get_dfs(file_path=file_path, v=0)
    create_tables()
    insert_data(trajectories_df, "trajectories")
    insert_data(vehicle_df, "vehicles")
    


extract_load("/scripts/data/20181030_d1_0830_0900.csv")