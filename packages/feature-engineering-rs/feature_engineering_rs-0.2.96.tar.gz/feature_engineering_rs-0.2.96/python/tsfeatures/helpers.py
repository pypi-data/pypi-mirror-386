import pandas as pd
import numpy as np
from feature_engineering_rs import (
    tsfeatures_all_f,
    extract_tsfeatures_cumulative_f
)
from concurrent.futures import ThreadPoolExecutor, as_completed
from python.helpers import NUM_WORKERS
import pytimetk as tk

from tsfeatures import (
    flat_spots, 
    crossing_points, 
    entropy,
    lumpiness, 
    stability, 
    hurst, 
    unitroot_pp,
    unitroot_kpss, 
    arch_stat,
    nonlinearity, 
    pacf_features, 
)

def extract_tsfeatures_rust(series, normalize=False):
    """Extract all TSFeatures using Rust - single window"""
    
    # Convert pandas series to list if needed
    if hasattr(series, 'values'):
        data = series.values.tolist()
    else:
        data = list(series)
    
    # Call Rust function
    result = tsfeatures_all_f(data, normalize=normalize)
    
    # Return as dict for easy access
    return dict(zip(result.names, result.values))

def extract_tsfeatures_cumulative_rust(series, df, value_column="VALUE", date_column="DATE", normalize=False, freq=12):
    """Extract TSFeatures using cumulative windows with Rust - optimized version"""
    
    # Convert pandas series to list if needed
    if hasattr(series, 'values'):
        data = series.values.tolist()
    else:
        data = list(series)
    
    # Call Rust function with configurable column name
    result = extract_tsfeatures_cumulative_f(
        data, normalize=normalize, value_column_name=value_column, freq=freq
    )
    
    # Convert to DataFrame
    features_df = pd.DataFrame(result.values, columns=result.feature_names)
    
    # Add the DATE column back from the original dataframe - CORRECTLY aligned
    if date_column in df.columns:
        # Get dates corresponding to each cumulative window endpoint (0, 1, 2, ..., n-1)
        date_values = df[date_column].iloc[:len(features_df)].values
        features_df.insert(0, date_column, date_values)
    
    # Reorder columns to match the Python version (DATE, VALUE, then features)
    if date_column in features_df.columns and value_column in features_df.columns:
        # Get all other columns
        other_cols = [col for col in features_df.columns if col not in [date_column, value_column]]
        # Reorder: DATE, VALUE, then all other features
        ordered_cols = [date_column, value_column] + other_cols
        features_df = features_df[ordered_cols]
    
    return features_df


def compute_tsfeatures_cumulative(
    series_df, end_idx, df, value_column, date_column, freq
):
    """Compute ts_features for cumulative window from start to end_idx"""
    # Extract data from beginning up to current index
    window_df = series_df.iloc[: end_idx + 1].copy()

    # Start with date_column and value_column
    features_dict = {
        date_column: df.iloc[end_idx][date_column],
        value_column: df.iloc[end_idx][value_column],
    }

    # Calculate features if we have enough data points
    if len(window_df) >= 1:
        try:
            # Extract numpy array like the Rust version does
            values_array = window_df[value_column].values
            
            # Call individual feature functions directly with numpy array
            features_dict['entropy'] = entropy(values_array)['entropy']
            features_dict['flat_spots'] = flat_spots(values_array)['flat_spots']
            features_dict['crossing_points'] = crossing_points(values_array)['crossing_points']
            features_dict['lumpiness'] = lumpiness(values_array, freq)['lumpiness']
            features_dict['stability'] = stability(values_array, freq)['stability']
            features_dict['nonlinearity'] = nonlinearity(values_array)['nonlinearity']
            features_dict['hurst'] = hurst(values_array)['hurst']
            features_dict['arch_lm'] = arch_stat(values_array)['arch_lm']
            features_dict['unitroot_kpss'] = unitroot_kpss(values_array)['unitroot_kpss']
            features_dict['unitroot_pp'] = unitroot_pp(values_array)['unitroot_pp']
            
            # PACF features return multiple values
            pacf_results = pacf_features(values_array, freq)
            if isinstance(pacf_results, dict):
                features_dict.update(pacf_results)
            else:
                # Handle case where pacf_features returns a single value or array
                features_dict['x_pacf5'] = pacf_results

        except Exception as e:
            print(f"Error computing features for index {end_idx}: {e}")

    return end_idx, features_dict


def extract_tsfeatures_parallel(
    df, value_column="VALUE", date_column="DATE", freq=12, num_workers=NUM_WORKERS
):
    """Extract ts_features using cumulative windows with multithreading"""

    # Prepare the dataframe
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column])
    df = df.sort_values(date_column).reset_index(drop=True)

    # Create a dataframe with just the columns we need for ts_features
    series_df = df[[date_column, value_column]].copy()

    # Dictionary to store results with their original index
    results = {}

    # Run parallel processing using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(
                compute_tsfeatures_cumulative,
                series_df,
                i,
                df,
                value_column,
                date_column,
                freq
            ): i
            for i in range(len(df))
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

    # Ensure date_column and value_column are first
    cols = features_df.columns.tolist()
    priority_cols = [date_column, value_column]
    other_cols = [col for col in cols if col not in priority_cols]
    ordered_cols = priority_cols + other_cols

    return features_df[ordered_cols]
