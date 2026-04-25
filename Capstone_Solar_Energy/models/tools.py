import pandas as pd
import re
from bs4 import BeautifulSoup
import json
import chardet
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.inspection import permutation_importance


# Make a new function to display feature's unique information on top of the df.info()
def show_info(df, ret=False):
    # Create initial information DataFrame
    info_df = pd.DataFrame(df.dtypes, columns=["Dtype"])
    info_df["Non-Null Count"] = df.count()

    # Add N_unique column
    info_df["Unique Count"] = df.nunique()

    info_df["Unique Values"] = "..."

    # Check unique count for each column and add Unique Values column
    unique_values = df.nunique() < 10
    for col in df.columns[unique_values]:
        info_df.loc[col, "Unique Values"] = str(dict(df[col].value_counts()))

    # Add missing_pct column
    info_df["Missing%"] = df.isnull().mean().round(4) * 100

    # Reset the index
    info_df.reset_index(inplace=True)
    info_df.rename(columns={"index": "Column"}, inplace=True)

    new_column_order = [
        "Column",
        "Dtype",
        "Non-Null Count",
        "Missing%",
        "Unique Count",
        "Unique Values",
    ]

    info_df = info_df[new_column_order]

    if ret:
        # Filter out columns having large missing values
        filter = info_df["Missing%"] > 90
        return info_df, info_df[filter]["Column"].to_list()

    return info_df


# Get alerts from profiling
def get_alerts(report):
    # Open the report file
    with open(report) as fp:
        soup = BeautifulSoup(fp, "html.parser")

    # Find the Alerts table
    alerts_section = soup.find(id="overview-alerts")

    # Initialize a list to store alter information
    alerts = []
    # Iterate over tr
    for row in alerts_section.find_all("tr"):
        # Get the columns
        td_elements = row.find_all("td")
        # Get the texts in each column
        alert_info = td_elements[0].text.strip()
        alert_type = td_elements[1].text.strip()
        # Append them to the alerts list
        alerts.append((alert_info, alert_type))

    # Output the information in the alters list
    for alert in alerts:
        print(f"{alert[1]}: {alert[0]}")


# Check the missing values
def dump_missing(df):
    missing = pd.DataFrame(
        {"Amount": df.isnull().sum(), "Percentage": df.isnull().mean().round(4) * 100}
    )
    print(f"Out of {df.shape[0]} entries:")
    return missing[missing["Amount"] != 0]


def get_encoding(input_file):
    """Guess the encoding of the input file"""
    with open(input_file, "rb") as f:
        result = chardet.detect(f.read())
        encoding = result["encoding"]
    return encoding


def parse_xml(input_file):
    # Define a list of dictionaries to hold the data
    data = []

    tree = ET.parse(input_file)
    root = tree.getroot()
    tag = root.tag
    # print(tag)

    # Iterate over all tag elements in the file
    # for tag in root.findall(tag):
    for tag in root:
        # Each tag is a dictionary
        # print(tag)
        tag_data = {}

        # Iterate over all children elements of tag
        for child in tag:
            # Use the tag name as a dictionary key and the text as the value
            tag_data[child.tag] = child.text

        # Append this tag to the list
        data.append(tag_data)

    return pd.DataFrame(data)


def plot_correlation(df, cols_corr):
    plt.figure(figsize=(8, 7))
    corr_df = df[cols_corr].corr()

    # Heat map
    filter = (corr_df >= 0.2) | (corr_df <= -0.2)
    sns.heatmap(
        corr_df[filter],
        cmap="RdYlGn",
        vmax=1.0,
        vmin=-1.0,
        linewidths=0.1,
        annot=True,
        annot_kws={"size": 10},
        square=True,
        cbar=False,
    )

    plt.show()


def drop_na_and_zeros(df, col):
    # Drop rows with NaN values in the specified column
    df = df.dropna(subset=[col])

    # Get the index of the first non-zero value in the specified column
    first_non_zero_index = df[col].ne(0).idxmax()

    # Drop the initial rows with zeros in the specified column
    df = df.loc[first_non_zero_index:]

    # Reset index after drop
    # df.reset_index(drop=True, inplace=True)

    return df


def get_common_index(df_dict):
    df_list = []

    for name, df in df_dict.items():
        df = df.add_suffix("_" + name)
        df_list.append(df)

        # Concatenate the dataframes
        df_merged = pd.concat(df_list, axis=1)

        # Drop NA
        df_merged = df_merged.dropna()

    return df_merged.index


def add_date_features(df, hr=False):
    df = df.copy()

    df["year"] = df.index.year
    df["month"] = df.index.month
    df["week"] = df.index.isocalendar().week
    df["weekday"] = df.index.dayofweek
    # df["day"] = df.index.day  # month day
    df["day_of_year"] = df.index.dayofyear  # day of year

    # Deal with non-daily data
    if hr:
        df["hour"] = df.index.hour

    return df


def compute_importance(model, X_test, y_test, rseed=42, top=5):
    result = permutation_importance(
        model, X_test, y_test, n_repeats=10, random_state=rseed
    )

    df_importance = pd.DataFrame()
    df_importance["features"] = X_test.columns
    df_importance["importances"] = result.importances_mean
    df_importance["std"] = result.importances_std

    df_importance.sort_values("importances", ascending=False, inplace=True)

    df_importance_top = df_importance.head(top)

    df_importance_top["importances"].plot(
        kind="barh", legend=False, xerr=df_importance_top["std"].tolist()
    )

    plt.gca().set_yticklabels(df_importance_top["features"].tolist())
    plt.gca().invert_yaxis()
    plt.title(f"Top-{top} Most Important Features of the Model")
    plt.show()
