from datetime import timedelta, datetime
from pathlib import Path
import pandas as pd
import sqlite3

class ETL:
    def __init__(self,dag_path):
        self.dag_path = dag_path
        
    def transform_data(self,exec_date):
        try:
            print(f"Ingesting data for date: {exec_date}")
            date = datetime.strptime(exec_date, '%Y-%m-%d %H')
            file_date_path = f"{date.strftime('%Y-%m-%d')}/{date.hour}"

            # booking = pd.read_csv(f"{dag_path}/raw_data/{file_date_path}/booking.csv", low_memory=False)
            booking = pd.read_csv(f"{self.dag_path }/raw_data/booking.csv", low_memory=False)
            client = pd.read_csv(f"{self.dag_path }/raw_data/client.csv", low_memory=False)
            hotel = pd.read_csv(f"{self.dag_path }/raw_data/hotel.csv", low_memory=False)

            # merge booking with client
            data = pd.merge(booking, client, on='client_id')
            data.rename(columns={'name': 'client_name', 'type': 'client_type'}, inplace=True)

            # merge booking, client & hotel
            data = pd.merge(data, hotel, on='hotel_id')
            data.rename(columns={'name': 'hotel_name'}, inplace=True)

            # make date format consistent
            data.booking_date = pd.to_datetime(data.booking_date, infer_datetime_format=True)

            # make all cost in GBP currency
            data.loc[data.currency == 'EUR', ['booking_cost']] = data.booking_cost * 0.8
            data.currency.replace("EUR", "GBP", inplace=True)

            # remove unnecessary columns
            data = data.drop('address', 1)

            # load processed data
            output_dir = Path(f'{self.dag_path }/processed_data/{file_date_path}')
            output_dir.mkdir(parents=True, exist_ok=True)
            # processed_data/2021-08-15/12/2021-08-15_12.csv
            data.to_csv(output_dir / f"{file_date_path}.csv".replace("/", "_"), index=False, mode='a')

        except ValueError as e:
            print("datetime format should match %Y-%m-%d %H", e)
            raise e


    def load_data(self,exec_date):
        print(f"Loading data for date: {exec_date}")
        date = datetime.strptime(exec_date, '%Y-%m-%d %H')
        file_date_path = f"{date.strftime('%Y-%m-%d')}/{date.hour}"

        conn = sqlite3.connect("/usr/local/airflow/db/datascience.db")
        c = conn.cursor()
        c.execute('''
                    CREATE TABLE IF NOT EXISTS booking_record (
                        client_id INTEGER NOT NULL,
                        booking_date TEXT NOT NULL,
                        room_type TEXT(512) NOT NULL,
                        hotel_id INTEGER NOT NULL,
                        booking_cost NUMERIC,
                        currency TEXT,
                        age INTEGER,
                        client_name TEXT(512),
                        client_type TEXT(512),
                        hotel_name TEXT(512)
                    );
                ''')
        processed_file = f"{self.dag_path }/processed_data/{file_date_path}/{file_date_path.replace('/', '_')}.csv"
        records = pd.read_csv(processed_file)
        records.to_sql('booking_record', conn, index=False, if_exists='append')


    def execution_date_to_millis(self,execution_date):
        """converts execution date (in DAG timezone) to epoch millis

        Args:
            date (execution date): %Y-%m-%d

        Returns:
            milliseconds
        """
        date = datetime.strptime(execution_date, "%Y-%m-%d")
        epoch = datetime.utcfromtimestamp(0)
        return (date - epoch).total_seconds() * 1000.0
