# Author -> Sevrus b25bs1304@iitj.ac.in, GITHUB -> sevruscorporations@gmail.com
import os
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from sklearn.linear_model import LinearRegression
from noise import pnoise1

def gsheet_load(url, as_df=False, max_workers=None):
    """
    Convert a Google Sheets, GitHub, or direct CSV link to a CSV-ready URL and optionally load as DataFrame(s).

    Parameters:
        url (str | list): URL(s) of CSV file(s).
        as_df (bool): If True, return pandas DataFrame(s) instead of URL(s).
        max_workers (int | None): Max threads for parallel downloading (only for list of URLs).

    Returns:
        str | list | pd.DataFrame | list[pd.DataFrame]
    """

    def convert_url(single_url):
        parsed = urlparse(single_url)
        netloc = parsed.netloc.lower()
        path = parsed.path.lower()

        # Google Sheets
        if "docs.google.com" in netloc and "/spreadsheets/" in path:
            if "/edit" in single_url:
                return single_url.split("/edit")[0] + "/gviz/tq?tqx=out:csv"
            else:
                return single_url

        # GitHub
        elif "github.com" in netloc:
            if "/blob/" in single_url:
                return single_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            return single_url  # Already raw URL

        # Direct CSV link
        else:
            return single_url

    def fetch_csv(single_url):
        csv_url = convert_url(single_url)
        try:
            return pd.read_csv(csv_url)
        except Exception as e:
            raise RuntimeError(f"Failed to read CSV from {single_url}: {e}")

    # Handle single URL vs list
    if isinstance(url, list):
        if as_df:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                return list(executor.map(fetch_csv, url))
        else:
            return [convert_url(u) for u in url]
    else:
        converted = convert_url(url)
        return pd.read_csv(converted) if as_df else converted

def gsheet_save(data_frames, auto_name=True, name_series="Sheet", save_dir=".", filename=None):
    """
    Save one or more DataFrames as CSV files.

    Parameters:
        data_frames (pd.DataFrame | list[pd.DataFrame]): Single dataframe or list of dataframes to save.
        auto_name (bool): If True, generates filenames automatically using name_series + index (only for multiple frames).
        name_series (str | list): Base name (str) or list of names (required if auto_name=False and multiple frames).
        save_dir (str): Directory to save CSV files. Defaults to current directory.
        filename (str | None): Filename for single dataframe. Required if saving a single DataFrame.
    """
    # Normalize input to list
    single_input = False
    if isinstance(data_frames, pd.DataFrame):
        data_frames = [data_frames]
        single_input = True

    assert data_frames, "DATA FRAMES must not be empty!"

    # Ensure absolute save directory path
    save_dir = os.path.abspath(save_dir)
    os.makedirs(save_dir, exist_ok=True)

    # Handle single dataframe case
    if single_input:
        assert filename, "Must provide 'filename' when saving a single DataFrame"
        if not filename.lower().endswith(".csv"):
            filename += ".csv"
        fpath = os.path.join(save_dir, filename)
        data_frames[0].to_csv(fpath, index=False)
        return  # Nothing to return

    # Handle multiple dataframes
    if auto_name:
        if isinstance(name_series, list):
            raise RuntimeError("Auto Name -> True but name_series is a list! Provide a string base name instead.")
    else:
        if not isinstance(name_series, list):
            raise RuntimeError("Auto Name -> False. Provide a list of filenames as name_series.")
        if len(name_series) < len(data_frames):
            raise ValueError("Number of filenames provided is less than number of data frames.")

    for idx, frame in enumerate(data_frames):
        if auto_name:
            fname = f"{name_series}{idx}.csv"
        else:
            fname = f"{name_series[idx]}.csv"
        fpath = os.path.join(save_dir, fname)
        frame.to_csv(fpath, index=False)

from sklearn.linear_model import LinearRegression
from opensimplex import OpenSimplex
import numpy as np
import pandas as pd

def fill_nans(df, column_name=None, method="opensimplex", seed=0, scale_factor=0.1, lim_min=0, lim_max=100):
    """
    Fill NaN values in a DataFrame column or all numeric columns using either OpenSimplex noise or linear regression.
    
    Parameters:
    - df : pandas.DataFrame
        Input DataFrame containing numeric columns.
    - column_name : str, optional
        Column to fill. If None, all numeric columns will be filled.
    - method : str, default "opensimplex"
        Filling method: "opensimplex" for OpenSimplex noise, "linear" for linear regression.
    - seed : int, default 0
        Seed for OpenSimplex noise generation.
    - scale_factor : float, default 0.1
        Step size for noise generation.
    - lim_min : float, default 0
        Minimum limit for filled values.
    - lim_max : float, default 100
        Maximum limit for filled values.
        
    Returns:
    - pandas.DataFrame
        A copy of the original DataFrame with NaNs filled, respecting user-defined limits.
    """
    df_copy = df.copy()
    if column_name is not None:
        if not np.issubdtype(df_copy[column_name].dtype, np.number):
            raise TypeError(f"Column '{column_name}' must be numeric.")
        cols_to_fill = [column_name]
    else:
        cols_to_fill = df_copy.select_dtypes(include=[np.number]).columns.tolist()

    for col in cols_to_fill:
        arr = df_copy[col].to_numpy(dtype=float)
        nan_mask = np.isnan(arr)

        if not nan_mask.any():
            continue

        if method == "opensimplex":
            mean_val = np.nanmean(arr)
            std_val = np.nanstd(arr)
            tmp = OpenSimplex(seed=seed)
            indices = np.arange(len(arr))
            noise_vals = np.array([tmp.noise2d(x=i*scale_factor, y=0) for i in indices])
            noise_scaled = noise_vals * 2 * std_val + mean_val
            noise_scaled = np.clip(noise_scaled, lim_min, lim_max)
            arr[nan_mask] = noise_scaled[nan_mask]

        elif method == "linear":
            indices_all = np.arange(len(arr)).reshape(-1, 1)
            X_train = indices_all[~nan_mask]
            y_train = arr[~nan_mask]
            X_pred = indices_all[nan_mask]

            model = LinearRegression()
            model.fit(X_train, y_train)
            arr[nan_mask] = model.predict(X_pred)
            arr = np.clip(arr, lim_min, lim_max)

        else:
            raise ValueError("Method must be 'opensimplex' or 'linear'")

        df_copy[col] = arr

    return df_copy