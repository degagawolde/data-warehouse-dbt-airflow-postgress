import os
from os.path import join, dirname
from pprint import pprint
from traceback import print_exc
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy import inspect
# from dotenv import load_dotenv

# dotenv_path = join(dirname(__file__), '.env')
# load_dotenv(dotenv_path)

# Connect to your PostgreSQL database on a remote server
HOST = os.getenv("DBHOST")
PORT = os.getenv("DBPORT")
USER = os.getenv("DBUSER")
PASS = os.getenv("DBPASS")
DB = os.getenv("DB")

dag_path = os.getcwd()


CONNECTION_STR = f"postgresql+psycopg2://airflow:airflow@postgres/airflow"
BANNER = "="*20

# Connect to the database
ENGINE = create_engine(CONNECTION_STR)

# Create the tables
def create_tables(name):
    try:
        with ENGINE.connect() as conn:
            with open(name) as file:
                query = text(file.read())
                conn.execute(query)
        print("Successfully created {} table".format(name.split(".")[-2]))
    except:
        print("Unable to create the Tables")
        print(print_exc())

# Populate the tables
def insert_data(df: pd.DataFrame, table_name):
    try:
        with ENGINE.connect() as conn:
            df.to_sql(name=table_name, con=conn,
                      if_exists='replace', index=False)
        print(f"Done inserting to {table_name}")
        print(BANNER)
    except:
        print("Unable to insert to table")
        print(print_exc())

# Implement Querying functions
def get_table_names():
    with ENGINE.connect() as conn:
        inspector = inspect(conn)
        names = inspector.get_table_names()
        return names

def get_vehicles():
    with ENGINE.connect() as conn:
        veh_df = pd.read_sql_table('vehicles', con=conn)

        return veh_df

def get_trajectories():
    with ENGINE.connect() as conn:
        trajectories_df = pd.read_sql_table('trajectories', con=conn)

        return trajectories_df

if __name__=="__main__":
    print(get_table_names())