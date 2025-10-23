import time

from python.helpers import create_large_benchmark_dataset
from python.tsfeatures.helpers import (
    extract_tsfeatures_parallel,
    extract_tsfeatures_cumulative_rust,
)

# Create a large benchmark dataset to test the performance of the Rust and Python versions for the cumulative version of the TSFeatures
df = create_large_benchmark_dataset(n_points=1000)

# Initialize timing variables
python_total_time = 0
rust_optimized_total_time = 0
num_runs = 10

print(f"Running TSFeatures cumulative benchmarks with {num_runs} runs...")

# Time Python TSFeatures version
print(f"\n=== Python TSFeatures version ({num_runs} runs) ===")
for i in range(num_runs):
    start_time = time.time()
    df_py = extract_tsfeatures_parallel(
        df, 
        value_column='VALUE', 
        date_column='DATE', 
        freq=12,  
        num_workers=4
    )
    
    end_time = time.time()
    run_time = end_time - start_time
    python_total_time += run_time
    print(f"Run {i+1}: {run_time:.4f} seconds")

# Time Rust optimized version
print(f"\n=== Rust optimized version ({num_runs} runs) ===")
for i in range(num_runs):
    start_time = time.time()
    df_rs_optimized = extract_tsfeatures_cumulative_rust(
        df['VALUE'], 
        df, 
        value_column='VALUE', 
        date_column='DATE', 
        freq=12,
        normalize=False
    )
    
    end_time = time.time()
    run_time = end_time - start_time
    rust_optimized_total_time += run_time
    print(f"Run {i+1}: {run_time:.4f} seconds")

# Calculate and display averages
python_avg = python_total_time / num_runs
rust_optimized_avg = rust_optimized_total_time / num_runs
print("\n" + "="*50)
print("TSFEATURES CUMULATIVE BENCHMARK RESULTS")
print("="*50)
print(f"Python TSFeatures average time:    {python_avg:.4f} seconds")
print(f"Rust optimized average time:       {rust_optimized_avg:.4f} seconds")

# Calculate speedups
if rust_optimized_avg < python_avg:
    speedup = python_avg / rust_optimized_avg
    print(f"Rust optimized is {speedup:.2f}x faster than Python TSFeatures")
else:
    slowdown = rust_optimized_avg / python_avg
    print(f"Rust optimized is {slowdown:.2f}x slower than Python TSFeatures")

print("\n" + "="*50)
print("FEATURE COMPARISON")
print("="*50)

