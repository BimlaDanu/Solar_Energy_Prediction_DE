'''
This script carries out the following tasks:
1) Read in the concatenated energy generation data, and convert strings that look like floating-point numbers or integers to actual numbers (float or int)
2) Extract the date and hour information from the original 'MTU' feature
3) Condense data into hourly energy generation (unit: MWh)
4) Rename all the columns
5) Reformat the 'mtu' column to make it more easily comprehensible
Output: A comma-separated CSV file for hourly energy production of Germany from 20150101 onwards
TODO
'''


import pandas as pd

# Convert strings that look like floating-point numbers or integers to actual numbers (float or int)
def convert_to_number(x):
    if isinstance(x, str) and '.' in x:
        return float(x)
    elif isinstance(x, str) and x.isdigit():
        return int(x)
    else:
        return 0

# Read the CSV file with comma as the delimiter
csv_file_path = '/Users/shuxu_ds/workspace/neuefische_DS_bootcamp/capstone_solar/capstone_solar_energy/data/transparency/result_20150101-20230716.csv'
df = pd.read_csv(csv_file_path, delimiter=',', low_memory=False)

# Extract the date and hour information from the 'MTU' column
df['Date'] = df['MTU'].str[:10].str[-4:] + df['MTU'].str[:10].str[3:5] + df['MTU'].str[:10].str[:2]
df['Hour'] = df['MTU'].str[11:13]

# Apply conversion to all object-type columns except 'Area', 'MTU', 'Date', and 'Hour'
object_columns = df.select_dtypes(include=[object]).columns
for column in object_columns:
    if column not in ['Area', 'MTU', 'Date', 'Hour']:
        df[column] = df[column].apply(convert_to_number)

# Replace true strings in the data columns with 0
data_columns = df.select_dtypes(include=[int, float]).columns
df[data_columns] = df[data_columns].fillna(0)

# Group by index divided by 4 and aggregate using mean (energy production within an hour: MWh) for numeric columns
# df[data_columns] = df.groupby(df.index // 4)[data_columns].transform('sum')
df[data_columns] = df.groupby(df.index // 4)[data_columns].transform('mean')

# Group by index divided by 4 and take the first instance for 'Area', 'MTU', 'Date', and 'Hour' columns
non_numeric_columns = ['Area', 'MTU', 'Date', 'Hour']
df[non_numeric_columns] = df.groupby(df.index // 4)[non_numeric_columns].transform('first')

# Drop duplicated rows (keep the first instance for every 4 rows)
df = df.drop_duplicates(subset=df.columns.difference(['Area', 'MTU', 'Date', 'Hour']))

# Reset the index
df.reset_index(drop=True, inplace=True)

# Original column names
'''
['Area', 'MTU', 'Biomass  - Actual Aggregated [MW]',
       'Fossil Brown coal/Lignite  - Actual Aggregated [MW]',
       'Fossil Coal-derived gas  - Actual Aggregated [MW]',
       'Fossil Gas  - Actual Aggregated [MW]',
       'Fossil Hard coal  - Actual Aggregated [MW]',
       'Fossil Oil  - Actual Aggregated [MW]',
       'Fossil Oil shale  - Actual Aggregated [MW]',
       'Fossil Peat  - Actual Aggregated [MW]',
       'Geothermal  - Actual Aggregated [MW]',
       'Hydro Pumped Storage  - Actual Aggregated [MW]',
       'Hydro Pumped Storage  - Actual Consumption [MW]',
       'Hydro Run-of-river and poundage  - Actual Aggregated [MW]',
       'Hydro Water Reservoir  - Actual Aggregated [MW]',
       'Marine  - Actual Aggregated [MW]', 'Nuclear  - Actual Aggregated [MW]',
       'Other  - Actual Aggregated [MW]',
       'Other renewable  - Actual Aggregated [MW]', 'Solar  - Actual Aggregated [MW]',
       'Waste  - Actual Aggregated [MW]',
       'Wind Offshore  - Actual Aggregated [MW]',
       'Wind Onshore  - Actual Aggregated [MW]', 'Date', 'Hour']
'''

# List of new column names
new_column_names = ['area', 'mtu', 'biomass_mwh', 'fossil_brown_coal_mwh', 'fossil_coal_derived_gas_mwh', 'fossil_gas_mwh', 'fossil_hard_coal_mwh', 'fossil_oil_mwh', 'fossil_oil_shale_mwh', 'fossil_peat_mwh', 'geothermal_mwh', 'hydro_pumped_storage_aggregated_mwh', 'hydro_pumped_storage_consumption_mwh', 'hydro_run_of_river_and_poundage_mwh', 'hydro_water_reservoir_mwh', 'marine_mwh', 'nuclear_mwh', 'other_mwh', 'other_renewable_mwh', 'solar_mwh', 'waste_mwh', 'wind_offshore_mwh', 'wind_onshore_mwh', 'date', 'hour']

# Assign the new column names to the DataFrame
df.columns = new_column_names

# List of columns to be summed for total power generation (of all the production types)
# Note: 'hydro_pumped_storage_consumption_mwh' should be excluded when calculating total energy production per time unit
columns_to_sum = ['biomass_mwh', 'fossil_brown_coal_mwh',
       'fossil_coal_derived_gas_mwh', 'fossil_gas_mwh', 'fossil_hard_coal_mwh',
       'fossil_oil_mwh', 'fossil_oil_shale_mwh', 'fossil_peat_mwh',
       'geothermal_mwh', 'hydro_pumped_storage_aggregated_mwh',
       'hydro_run_of_river_and_poundage_mwh', 'hydro_water_reservoir_mwh',
       'marine_mwh', 'nuclear_mwh', 'other_mwh', 'other_renewable_mwh',
       'solar_mwh', 'waste_mwh', 'wind_offshore_mwh', 'wind_onshore_mwh'
       ]

# Create a new column 'total_energy_generation_mwh' as the sum of the specified columns
df['total_energy_generation_mwh'] = df[columns_to_sum].sum(axis=1)

# Make the 'mtu' column more easily comprehensible
df['date'] = df['date'].str.zfill(2)
df['hour'] = df['hour'].str.zfill(2)

# Calculate the end hour based on the start hour
df['hour_next_temp'] = (df['hour'].astype(int) + 1) % 24
df['hour_next_temp'] = df['hour_next_temp'].astype(str)
df['hour_next_temp'] = df['hour_next_temp'].str.zfill(2)

# Combine 'date' and 'hour' columns and update the 'mtu' column
df['mtu'] = df['date'] + ' ' + df['hour'] + ':00-' + df['hour_next_temp'] + ':00'

# Drop the column 'hour_next_temp'
df = df.drop(['hour_next_temp'], axis=1)

# Save the modified DataFrame to a new CSV file
new_csv_file_path = '/Users/shuxu_ds/workspace/neuefische_DS_bootcamp/capstone_solar/capstone_solar_energy/data/transparency/transparency_20150101-20230716_hourly.csv'
df.to_csv(new_csv_file_path, index=False)


