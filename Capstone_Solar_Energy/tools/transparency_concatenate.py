# This script concatenates the electricity production data files downloaded from entso-e's transparency platform

import pandas as pd
import os

def concatenate_csv_files(input_folder, output_file):
    # Initialize an empty list to store the DataFrames
    dfs = []

    # Get the list of CSV files in the input folder and sort them
    csv_files = sorted([f for f in os.listdir(input_folder) if f.endswith('.csv')])

    # Read the first CSV file to get its column names
    first_file_path = os.path.join(input_folder, csv_files[0])
    first_df = pd.read_csv(first_file_path)

    # Loop through each CSV file
    for idx, csv_file in enumerate(csv_files):
        file_path = os.path.join(input_folder, csv_file)

        # Read the CSV file and append it to the list of DataFrames
        df = pd.read_csv(file_path)

        print(df.columns[19])

        # Ensure column names are consistent with the first DataFrame
        if not df.columns.equals(first_df.columns):
            # Only for debug
            print(first_df.columns)
            print(df.columns)

            df = df.reindex(columns=first_df.columns, fill_value=None)

        dfs.append(df)

    # Concatenate the DataFrames along rows
    result_df = pd.concat(dfs, ignore_index=True)

    # Save the concatenated data to the output file
    result_df.to_csv(output_file, index=False)

input_folder = '/Users/shuxu_ds/workspace/neuefische_DS_bootcamp/capstone_solar/capstone_solar_energy/data/transparency/raw/'
output_file = '/Users/shuxu_ds/workspace/neuefische_DS_bootcamp/capstone_solar/capstone_solar_energy/data/transparency/result_20150101-20230716.csv'

concatenate_csv_files(input_folder, output_file)
