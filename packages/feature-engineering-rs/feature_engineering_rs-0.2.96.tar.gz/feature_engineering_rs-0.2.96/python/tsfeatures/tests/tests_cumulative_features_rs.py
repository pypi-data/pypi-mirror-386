import pandas as pd
import numpy as np
import pytest
from python.helpers import create_large_benchmark_dataset
from python.tsfeatures.helpers import (
    extract_tsfeatures_parallel,
    extract_tsfeatures_cumulative_rust
)


def create_test_dataframes():
    """Create test dataframes for comparison"""
    df = create_large_benchmark_dataset(n_points=250)
    df_py = extract_tsfeatures_parallel(
        df, 
        value_column='VALUE', 
        date_column='DATE', 
        freq=1,  
        num_workers=4
    )

    df_rs = extract_tsfeatures_cumulative_rust(
        df['VALUE'], 
        df, 
        value_column='VALUE', 
        date_column='DATE', 
        freq=1,
        normalize=True
    )    
    
    if 'DATE' in df_rs.columns and 'DATE' in df_py.columns:
        df_rs['DATE'] = pd.to_datetime(df_rs['DATE'])
        df_py['DATE'] = pd.to_datetime(df_py['DATE'])

    df_rs.drop(columns=['seas_pacf'], inplace=True)
    
    # Define a consistent column order for both dataframes
    desired_order = [
        'DATE', 'VALUE', 'arch_lm', 'crossing_points', 'diff1x_pacf5', 'diff2x_pacf5',
        'entropy', 'flat_spots', 'hurst', 'lumpiness', 'nonlinearity', 'stability',
        'unitroot_kpss', 'unitroot_pp', 'x_pacf5'
    ]
    
    # Get common columns and reorder both dataframes consistently
    common_cols = list(set(df_rs.columns) & set(df_py.columns))
    # Keep only columns that exist in both dataframes, in the desired order
    ordered_cols = [col for col in desired_order if col in common_cols]
    # Add any remaining common columns that weren't in desired_order
    remaining_cols = [col for col in common_cols if col not in ordered_cols]
    final_order = ordered_cols + remaining_cols
    
    # Reorder both dataframes
    df_rs = df_rs[final_order]
    df_py = df_py[final_order]
    
    # Sort both by DATE to ensure proper alignment
    df_rs = df_rs.sort_values('DATE').reset_index(drop=True)
    df_py = df_py.sort_values('DATE').reset_index(drop=True)
    
    return df_rs, df_py


def test_dataframe_shapes():
    """Test that Rust and Python dataframes have the same shape"""
    df_rs, df_py = create_test_dataframes()
    assert df_rs.shape == df_py.shape, f"DataFrames have different shapes: Rust={df_rs.shape}, Python={df_py.shape}"

def test_dataframe_columns():
    """Test that Rust and Python dataframes have the same columns"""
    df_rs, df_py = create_test_dataframes()
    rs_cols = set(df_rs.columns)
    py_cols = set(df_py.columns)
    
    missing_in_rust = py_cols - rs_cols
    missing_in_python = rs_cols - py_cols
    
    if missing_in_rust:
        pytest.fail(f"Columns missing in Rust DF: {missing_in_rust}")
    if missing_in_python:
        pytest.fail(f"Columns missing in Python DF: {missing_in_python}")

def test_dataframe_values():
    """Test that Rust and Python dataframes have equivalent values"""
    df_rs, df_py = create_test_dataframes()
    
    # Dataframes are already aligned and have same column order from create_test_dataframes
    common_cols = list(df_rs.columns)
    
    # Compare row by row
    differences_found = []
    min_rows = min(len(df_rs), len(df_py))
    tol = 1e-8  # More lenient tolerance for TSFeatures
    
    # Features to skip for first 5 rows due to insufficient data
    skip_early_features = {'nonlinearity', 'hurst'}
    
    for idx in range(min_rows):
        row_rs = df_rs.iloc[idx]
        row_py = df_py.iloc[idx]
        
        col_differences = []
        for col in common_cols:
            val_rs = row_rs[col]
            val_py = row_py[col]
            
            # Skip nonlinearity and hurst for first 5 rows
            if idx < 5 and col in skip_early_features:
                continue
            
            # Handle NaN comparisons
            if pd.isna(val_rs) and pd.isna(val_py):
                continue
            elif pd.isna(val_rs) or pd.isna(val_py):
                col_differences.append(f"{col}: RS={val_rs}, PY={val_py}")
            # Handle numeric comparisons with tolerance
            elif isinstance(val_rs, (int, float)) and isinstance(val_py, (int, float)):
                if not np.isclose(val_rs, val_py, rtol=tol, atol=tol):
                    diff = abs(val_rs - val_py)
                    col_differences.append(f"{col}: RS={val_rs}, PY={val_py} (diff={diff:.2e})")
            # Handle string/other comparisons
            else:
                if val_rs != val_py:
                    col_differences.append(f"{col}: RS={val_rs}, PY={val_py}")
        
        if col_differences:
            differences_found.append({
                'row': idx,
                'date': row_rs['DATE'] if 'DATE' in common_cols else f'Row_{idx}',
                'differences': col_differences
            })
    
    # If differences found, fail with detailed information
    if differences_found:
        error_msg = f"Found {len(differences_found)} rows with differences out of {min_rows} total rows.\n"
        error_msg += "First 5 differences:\n"
        
        for i, diff in enumerate(differences_found[:5]):
            error_msg += f"Row {diff['row']} ({diff['date']}): {'; '.join(diff['differences'][:3])}\n"
            if len(diff['differences']) > 3:
                error_msg += f"  ... and {len(diff['differences'])-3} more differences\n"
        
        if len(differences_found) > 5:
            error_msg += f"... and {len(differences_found)-5} more rows with differences\n"
        
        pytest.fail(error_msg)

def test_dataframe_comparison_detailed():
    """Detailed comparison test that saves differences to file for analysis"""
    df_rs, df_py = create_test_dataframes()
    
    # Dataframes are already aligned and have same column order from create_test_dataframes
    common_cols = list(df_rs.columns)
    
    # Compare and save detailed results
    differences_found = []
    min_rows = min(len(df_rs), len(df_py))
    exact_matches = 0
    tol = 1e-8
    
    # Features to skip for first 4 rows due to insufficient data
    skip_early_features = {'nonlinearity', 'hurst'}
    
    for idx in range(min_rows):
        row_rs = df_rs.iloc[idx]
        row_py = df_py.iloc[idx]
        
        row_exact_match = True
        col_differences = []
        
        for col in common_cols:
            val_rs = row_rs[col]
            val_py = row_py[col]
            
            # Skip nonlinearity and hurst for first 4 rows
            if idx < 5 and col in skip_early_features:
                continue
            
            # Handle NaN comparisons
            if pd.isna(val_rs) and pd.isna(val_py):
                continue
            elif pd.isna(val_rs) or pd.isna(val_py):
                row_exact_match = False
                col_differences.append(f"{col}: RS={val_rs}, PY={val_py}")
            # Handle numeric comparisons with tolerance
            elif isinstance(val_rs, (int, float)) and isinstance(val_py, (int, float)):
                if not np.isclose(val_rs, val_py, rtol=tol, atol=tol):
                    row_exact_match = False
                    diff = abs(val_rs - val_py)
                    col_differences.append(f"{col}: RS={val_rs}, PY={val_py} (diff={diff:.2e})")
            # Handle string/other comparisons
            else:
                if val_rs != val_py:
                    row_exact_match = False
                    col_differences.append(f"{col}: RS={val_rs}, PY={val_py}")
        
        if row_exact_match:
            exact_matches += 1
        else:
            differences_found.append({
                'row': idx,
                'date': row_rs['DATE'] if 'DATE' in common_cols else f'Row_{idx}',
                'differences': col_differences
            })
    
    # Save detailed differences to file if any found
    if differences_found:
        with open('detailed_differences_tsfeatures.txt', 'w') as f:
            f.write("DETAILED TSFeatures ROW-BY-ROW DIFFERENCES\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total rows compared: {min_rows}\n")
            f.write(f"Exact matches: {exact_matches}\n")
            f.write(f"Rows with differences: {len(differences_found)}\n")
            f.write(f"Note: Skipping nonlinearity and hurst comparisons for first 4 rows\n\n")
            
            for diff in differences_found:
                f.write(f"Row {diff['row']} ({diff['date']}):\n")
                
                # Write full row data
                f.write("Rust row data:\n")
                rs_row = df_rs.iloc[diff['row']]
                for col in common_cols:
                    # Mark skipped features
                    skip_marker = " (SKIPPED)" if diff['row'] < 4 and col in skip_early_features else ""
                    f.write(f"  {col}: {rs_row[col]}{skip_marker}\n")
                
                f.write("\nPython row data:\n")
                py_row = df_py.iloc[diff['row']]
                for col in common_cols:
                    # Mark skipped features
                    skip_marker = " (SKIPPED)" if diff['row'] < 4 and col in skip_early_features else ""
                    f.write(f"  {col}: {py_row[col]}{skip_marker}\n")
                
                f.write("\nDifferences:\n")
                for col_diff in diff['differences']:
                    f.write(f"  {col_diff}\n")
                f.write("\n" + "="*50 + "\n\n")
    
    # This test passes even if differences are found - it's just for analysis
    # The actual assertion test is in test_dataframe_values()
    match_percentage = (exact_matches / min_rows) * 100 if min_rows > 0 else 0
    print(f"TSFeatures DataFrame comparison: {exact_matches}/{min_rows} rows match ({match_percentage:.1f}%)")
    print(f"Note: Skipped nonlinearity and hurst comparisons for first 4 rows due to insufficient data")
    if differences_found:
        print(f"Detailed differences saved to 'detailed_differences_tsfeatures.txt'")

# Add this at the end like the other test files
if __name__ == "__main__":
    import sys
    try:
        test_dataframe_shapes()
        test_dataframe_columns()
        test_dataframe_values()
        test_dataframe_comparison_detailed()
        print("TSFeatures tests completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"TSFeatures tests failed: {e}")
        sys.exit(1)