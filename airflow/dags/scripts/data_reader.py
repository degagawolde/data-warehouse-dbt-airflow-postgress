import pandas as pd


class DataReader:
    def __init__(self, file_path=None) -> None:
        self.filepath = file_path

    def get_uid(self, filename, row_num):

        return f"{filename}_{row_num}"

    def read_file(self, path: str) -> list:
        """Read a file from path and returns list of the lines in the file

        Parameters
        ----------
        path : str
            file location path

        Returns:
        list
            the file content in a list
        """
        with open(path, 'r') as f:
            lines = f.readlines()[1:]
            lines = list(map(lambda l: l.strip('\n'), lines))
            return lines

    def parse(self, lines: list, filename: str) -> tuple:
        """parses the lines into 5 columns and returns a pandas DataFrame

        Parameters
        ----------
        lines : list
            a list of lines from the source file
        filename : str
            the filename, used for generating unique identifiers

        Returns
        -------
        tuple
            contains two dataframes. one for the vehicle info and another
            for their trajectories.
        """

        veh_info = {
            "unique_id": [],
            "track_id": [],
            "veh_type": [],
            "traveled_distance": [],
            "avg_speed": [],
        }
        trajectories = {
            "unique_id": [],
            "lat": [],
            "lon": [],
            "speed": [],
            "lon_acc": [],
            "lat_acc": [],
            "time": [],
        }
        for row_num, line in enumerate(lines):
            uid = self.get_uid(filename, row_num)
            line = line.split("; ")[:-1]
            # assert len(line[4:]) % 6 == 0, f"row number {row_num} caused the error: len(line[4:]) % 6 = {len(line[4:]) % 6}"
            assert len(line[4:]) % 6 == 0, f"{line}"
            veh_info["unique_id"].append(uid)
            veh_info["track_id"].append(int(line[0]))
            veh_info["veh_type"].append(line[1])
            veh_info["traveled_distance"].append(float(line[2]))
            veh_info["avg_speed"].append(float(line[3]))
            for i in range(0, len(line[4:]), 6):
                trajectories["unique_id"].append(uid)
                trajectories["lat"].append(float(line[4+i+0]))
                trajectories["lon"].append(float(line[4+i+1]))
                trajectories["speed"].append(float(line[4+i+2]))
                trajectories["lon_acc"].append(float(line[4+i+3]))
                trajectories["lat_acc"].append(float(line[4+i+4]))
                trajectories["time"].append(float(line[4+i+5]))

        vehicle_df = pd.DataFrame(veh_info).reset_index(drop=True)
        trajectories_df = pd.DataFrame(trajectories).reset_index(drop=True)
        return vehicle_df, trajectories_df

    def get_dfs(self, file_path: str = None, v=0) -> tuple:
        """This calls the above two function. It takes the files path
        and returns a pandas dataframe object

        Parameters
        ----------
        file_path : str
            raw csv file path
        v: int
            verbosity selector

        Returns
        -------
        tuple
            transformed version of csv as two pd.DataFrame
        """
        if not file_path and self.filepath:
            file_path = self.filepath

        lines = self.read_file(file_path)
        filename = file_path.split("/")[-1].strip(".csv")
        vehicle_df, trajectories_df = self.parse(lines, filename)
        if v > 0:
            print("vehicle dataframe")
            print(vehicle_df.head())
            print(vehicle_df.info())
            print("trajectories dataframe")
            print(trajectories_df.head())
            print(trajectories_df.info())
        return vehicle_df, trajectories_df


if __name__ == "__main__":
    DataReader(file_path="../data/20181030_d1_0830_0900.csv").get_dfs(v=1)
