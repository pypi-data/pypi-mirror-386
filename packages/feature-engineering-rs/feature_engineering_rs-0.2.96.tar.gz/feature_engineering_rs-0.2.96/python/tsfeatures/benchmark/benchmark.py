import numpy as np
import time

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

from feature_engineering_rs import (
    flat_spots_f,
    crossing_points_f,
    entropy_f,
    lumpiness_f,
    stability_f,
    hurst_f,
    unitroot_pp_f,
    unitroot_kpss_f,
    arch_stat_f,
    nonlinearity_f,
    pacf_features_f,
)

# Set a fixed seed for reproducible results
np.random.seed(42)
y = np.random.rand(10_000)

# Initialize timing variables
python_total_time = 0
rust_total_time = 0
num_runs = 10

print("Running benchmarks...")

# Time Python implementation
print(f"\n=== Python TSFeatures ({num_runs} runs) ===")
for i in range(num_runs):
    start_time = time.time()
    
    # Run all TSFeatures functions individually (like Python tsfeatures)
    flat_spots_result = flat_spots(y)
    crossing_points_result = crossing_points(y)
    entropy_result = entropy(y)
    lumpiness_result = lumpiness(y)
    stability_result = stability(y)
    hurst_result = hurst(y)
    unitroot_pp_result = unitroot_pp(y)
    unitroot_kpss_result = unitroot_kpss(y)
    arch_stat_result = arch_stat(y)
    nonlinearity_result = nonlinearity(y)
    pacf_features_result = pacf_features(y)

    end_time = time.time()
    run_time = end_time - start_time
    python_total_time += run_time
    print(f"Run {i+1}: {run_time:.4f} seconds")

# Time Rust implementation  
print(f"\n=== Rust feature_engineering_rs TSFeatures ({num_runs} runs) ===")
for i in range(num_runs):
    start_time = time.time()
    
    # Use the combined Rust function that runs all TSFeatures in parallel
    flat_spots_result = flat_spots_f(y)
    crossing_points_result = crossing_points_f(y)
    entropy_result = entropy_f(y)
    lumpiness_result = lumpiness_f(y)
    stability_result = stability_f(y)
    hurst_result = hurst_f(y)
    unitroot_pp_result = unitroot_pp_f(y)
    unitroot_kpss_result = unitroot_kpss_f(y)
    arch_stat_result = arch_stat_f(y)
    nonlinearity_result = nonlinearity_f(y)
    pacf_features_result = pacf_features_f(y)
    
    end_time = time.time()
    run_time = end_time - start_time
    rust_total_time += run_time
    print(f"Run {i+1}: {run_time:.4f} seconds")

# Calculate and display averages
python_avg = python_total_time / num_runs
rust_avg = rust_total_time / num_runs

print("\n" + "="*50)
print("TSFEATURES BENCHMARK RESULTS")
print("="*50)
print(f"Python average time: {python_avg:.4f} seconds")
print(f"Rust average time:   {rust_avg:.4f} seconds")

if rust_avg < python_avg:
    speedup = python_avg / rust_avg
    print(f"Rust is {speedup:.2f}x faster")
else:
    slowdown = rust_avg / python_avg
    print(f"Rust is {slowdown:.2f}x slower")