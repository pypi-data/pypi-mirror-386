import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

NUM_WORKERS = os.cpu_count() - 2

def create_large_benchmark_dataset(n_points=10000, save_path='benchmarks/large_df.csv'):
    """
    Create a large time series dataset for benchmarking
    
    Args:
        n_points: Number of time series points to generate
        save_path: Path to save the CSV file
    """
    
    # Set seed for reproducibility
    np.random.seed(42)
    
    # Generate date range - weekly intervals
    start_date = datetime(2017, 1, 1)
    dates = [start_date + timedelta(weeks=i) for i in range(n_points)]
    
    # Generate realistic time series data with trends, seasonality, and noise
    t = np.arange(n_points)
    
    # Base trend (slight upward)
    trend = 15000 + 0.5 * t
    
    # Seasonal component (annual cycle)
    seasonal = 2000 * np.sin(2 * np.pi * t / 52)  # 52 weeks in a year
    
    # Random walk component
    random_walk = np.cumsum(np.random.normal(0, 100, n_points))
    
    # Short-term noise
    noise = np.random.normal(0, 300, n_points)
    
    # Occasional jumps/spikes (market events)
    jumps = np.zeros(n_points)
    jump_indices = np.random.choice(n_points, size=n_points//100, replace=False)
    jumps[jump_indices] = np.random.normal(0, 1500, len(jump_indices))
    
    # Combine all components
    values = trend + seasonal + random_walk + noise + jumps
    
    # Ensure no negative values (like stock prices)
    values = np.maximum(values, 1000)
    
    # Create DataFrame
    df = pd.DataFrame({
        'DATE': [date.strftime('%m/%d/%y') for date in dates],
        'VALUE': values
    })

    return df