import os
from pprint import pprint
from traceback import print_exc
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy import inspect
from dotenv import load_dotenv

load_dotenv()


# Connect to your PostgreSQL database on a remote server
HOST = os.getenv("DBHOST")
PORT = os.getenv("DBPORT")
USER = os.getenv("DBUSER")
PASS = os.getenv("DBPASS")
DB = os.getenv("DB")

TRAJECTORY_SCHEMA = "trajectory_info_schema.sql"
VEHICLE_SCHEMA = "vehicle_info_schema.sql"
CONNECTION_STR = f"postgresql+psycopg2://{USER}:{PASS}@{HOST}/{DB}"
BANNER = "="*20

# Connect to the database
ENGINE = create_engine(CONNECTION_STR)


# Create the tables
def create_tables():
    try:
        with ENGINE.connect() as conn:
            for name in [VEHICLE_SCHEMA, TRAJECTORY_SCHEMA]:
                with open(name) as file:
                    query = text(file.read())
                    conn.execute(query)
        print("Successfully created 2 tables")
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