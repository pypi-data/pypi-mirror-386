import pandas as pd
import numpy as np
from feature_engineering_rs import (
    catch22_all_f,
    extract_catch22_features_cumulative_f
)
import pycatch22
from concurrent.futures import ThreadPoolExecutor, as_completed
from python.helpers import NUM_WORKERS

def compute_features_cumulative(series, end_idx, df, value_column, date_column):
    """Compute catch22 features for cumulative window from start to end_idx"""
    # Extract data from beginning up to current index
    window_data = series.iloc[: end_idx + 1].values

    # Get catch22 feature names for consistency
    dummy_features = pycatch22.catch22_all([1, 2, 3], catch24=True, short_names=True)

    # Start with DATE and original_value
    features_dict = {
        date_column: df.iloc[end_idx][date_column],
        value_column: series.iloc[end_idx],
    }

    # Calculate features if we have enough data points
    if len(window_data) >= 1:
        try:
            features = pycatch22.catch22_all(
                window_data, catch24=True, short_names=True
            )
            # Add catch22 features
            for name, value in zip(features["names"], features["values"]):
                features_dict[name] = value
        except Exception as e:
            print(f"Error computing features for index {end_idx}: {e}")
            # Handle cases where catch22 fails
            for name in dummy_features["names"]:
                features_dict[name] = np.nan
    else:
        # Not enough data - fill with NaN
        for name in dummy_features["names"]:
            features_dict[name] = np.nan

    return end_idx, features_dict


def extract_catch22_features_parallel(
    series, df, value_column="VALUE", date_column="DATE"
):
    """Extract catch22 features using cumulative windows with multithreading"""

    # Dictionary to store results with their original index
    results = {}

    # Run parallel processing using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        # Submit all tasks
        futures = {
            executor.submit(
                compute_features_cumulative, series, i, df, value_column, date_column
            ): i
            for i in range(len(series))
        }

        # Process completed tasks
        for future in as_completed(futures):
            try:
                idx, features_dict = future.result()
                results[idx] = features_dict
            except Exception as e:
                print(f"Error processing index {futures[future]}: {e}")

    # Sort results by index to maintain original order
    sorted_results = [results[i] for i in sorted(results.keys())]

    # Convert to DataFrame
    features_df = pd.DataFrame(sorted_results)

    # Ensure DATE and original_value are first
    cols = features_df.columns.tolist()
    priority_cols = [date_column, value_column]
    other_cols = [col for col in cols if col not in priority_cols]
    ordered_cols = priority_cols + other_cols

    return features_df[ordered_cols]

def compute_features_cumulative_rs(series, end_idx, df, value_column, date_column):
    """Compute catch22 features for cumulative window from start to end_idx"""
    # Extract data from beginning up to current index
    window_data = series.iloc[: end_idx + 1].values

    # Get catch22 feature names for consistency
    dummy_features = catch22_all_f([1, 2, 3], catch24=True, normalize=True)

    # Start with DATE and original_value
    features_dict = {
        date_column: df.iloc[end_idx][date_column],
        value_column: series.iloc[end_idx],
    }

    # Calculate features if we have enough data points
    if len(window_data) >= 1:
        try:
            features = catch22_all_f(
                window_data, catch24=True, normalize=True
            )
            # Add catch22 features
            for name, value in zip(features.names, features.values):
                features_dict[name] = value
        except Exception as e:
            print(f"Error computing features for index {end_idx}: {e}")
            # Handle cases where catch22 fails
            for name in dummy_features.names:
                features_dict[name] = np.nan
    else:
        # Not enough data - fill with NaN
        for name in dummy_features.names:
            features_dict[name] = np.nan

    return end_idx, features_dict

def extract_catch22_features_parallel_rs(
    series, df, value_column="VALUE", date_column="DATE"
):
    """Extract catch22 features using cumulative windows with multithreading"""

    # Dictionary to store results with their original index
    results = {}

    # Run parallel processing using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        # Submit all tasks
        futures = {
            executor.submit(
                compute_features_cumulative_rs, series, i, df, value_column, date_column
            ): i
            for i in range(len(series))
        }

        # Process completed tasks
        for future in as_completed(futures):
            try:
                idx, features_dict = future.result()
                results[idx] = features_dict
            except Exception as e:
                print(f"Error processing index {futures[future]}: {e}")

    # Sort results by index to maintain original order
    sorted_results = [results[i] for i in sorted(results.keys())]

    # Convert to DataFrame
    features_df = pd.DataFrame(sorted_results)

    # Ensure DATE and original_value are first
    cols = features_df.columns.tolist()
    priority_cols = [date_column, value_column]
    other_cols = [col for col in cols if col not in priority_cols]
    ordered_cols = priority_cols + other_cols

    return features_df[ordered_cols]

def extract_catch22_features_cumulative_rust(series, df, value_column="VALUE", date_column="DATE", normalize=True, catch24=True):
    """Extract catch22 features using cumulative windows with Rust - optimized version"""
    
    # Convert pandas series to list if needed
    if hasattr(series, 'values'):
        data = series.values.tolist()
    else:
        data = list(series)
    
    # Call Rust function with configurable column name
    result = extract_catch22_features_cumulative_f(
        data, normalize=normalize, catch24=catch24, value_column_name=value_column
    )
    
    # Convert to DataFrame
    features_df = pd.DataFrame(result.values, columns=result.feature_names)
    
    # Add the DATE column back from the original dataframe
    if date_column in df.columns:
        features_df.insert(0, date_column, df[date_column].values)
    
    # Reorder columns to match the Python version (DATE, VALUE, then features)
    if date_column in features_df.columns and value_column in features_df.columns:
        # Get all other columns
        other_cols = [col for col in features_df.columns if col not in [date_column, value_column]]
        # Reorder: DATE, VALUE, then all other features
        ordered_cols = [date_column, value_column] + other_cols
        features_df = features_df[ordered_cols]
    
    return features_df
