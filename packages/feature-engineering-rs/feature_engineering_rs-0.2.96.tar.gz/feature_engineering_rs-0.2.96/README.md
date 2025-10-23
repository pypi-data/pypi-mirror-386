# Feature Engineering RS

A high-performance feature engineering package built with Rust and exposed to Python via PyO3. Leverages Rust's memory safety and parallelization capabilities to efficiently compute time series features.

## Purpose

This repository creates a framework for implementing feature engineering algorithms in Rust, providing:
- **Performance**: Rust's zero-cost abstractions and parallel processing
- **Safety**: Memory safety guarantees without garbage collection overhead
- **Extensibility**: Modular framework for adding new features
- **Python Integration**: Seamless Python API through PyO3 bindings

## Architecture

- **Core Engine**: Rust implementation of feature computation algorithms
- **Parallel Processing**: Multi-threaded execution for large datasets
- **Feature Framework**: Extensible system for adding new feature types
- **Python Wrapper**: PyO3-based interface for easy integration

## Use Cases

- Time series feature extraction
- High-frequency data processing
- Batch feature computation
- Real-time feature engineering pipelines

## Development Workflow

This repository follows a two-branch development model:
- **`develop`**: Active development branch where new features and improvements are implemented and tested
- **`main`**: Stable release branch that receives tested and validated code from the develop branch

## Benchmarks

Performance tests were conducted on a MacBook Pro with M3 Max and 32GB of RAM. All benchmarks use 10 runs with averaged results.

### Catch22 Features

```
time python3 python/catch22/benchmark/benchmark.py
```

#### Individual Feature Computation
**Test Parameters:** 100,000 data points
```
Python average time: 2.3904 seconds
Rust average time:   1.9421 seconds
Rust is 1.23x faster
```

#### Cumulative Feature Computation

```
time python3 -m python.catch22.benchmark.cumulative_benchmark.py
```

**Test Parameters:** 1,000 data points across multiple time series
```
Python/C average time:       1.0544 seconds
Rust average time:           0.4249 seconds
Rust optimized average time: 0.0866 seconds

Rust is 2.48x faster than Python/C
Rust optimized is 12.17x faster than Python/C
Rust optimized is 4.90x faster than regular Rust
```

### TSFeatures

```
time python3 python/tsfeatures/benchmark/benchmark.py
```

#### Overall Performance (100,000 data points, sequential execution)
**Test Parameters:** All TSFeatures functions run sequentially

```
Python average time: 18.0449 seconds
Rust average time:   2.7539 seconds
Rust is 6.55x faster
python3 python/tsfeatures/benchmark/benchmark.py  243.78s user 44.30s system 136% cpu 3:31.55 total
```

#### Large Dataset Performance (1,000,000 data points)

| Feature | Python (sec) | Rust (sec) | Speedup |
|---------|-------------|------------|---------|
| flat_spots | 0.1934 | 0.0235 | **8.22x faster** |
| lumpiness | 1.5706 | 0.0366 | **42.96x faster** |
| stability | 0.6777 | 0.0354 | **19.14x faster** |
| arch_stat | 0.9059 | 0.5439 | **1.67x faster** |
| nonlinearity | 1.6565 | 0.0580 | **28.56x faster** |
| unitroot_pp | 0.0814 | 0.0606 | **1.34x faster** |
| crossing_points | 0.0104 | 0.0351 | *3.38x slower* |
| entropy | 0.0150 | 0.0474 | *3.16x slower* |
| unitroot_kpss | 0.0180 | 0.0540 | *3.01x slower* |

#### Medium Dataset Performance (100,000 data points)

| Feature | Python (sec) | Rust (sec) | Speedup |
|---------|-------------|------------|---------|
| hurst | 5.8631 | 2.6627 | **2.20x faster** |
| pacf_features | 10.8167 | 0.0040 | **2,688.26x faster** |

#### Cumulative Feature Computation

```
time python3 -m python.tsfeatures.benchmark.cumulative_benchmark
```

**Test Parameters:** 1,000 data points across multiple time series
```
Python TSFeatures average time:    13.1117 seconds
Rust optimized average time:       0.0575 seconds
Rust optimized is 227.99x faster than Python TSFeatures
```