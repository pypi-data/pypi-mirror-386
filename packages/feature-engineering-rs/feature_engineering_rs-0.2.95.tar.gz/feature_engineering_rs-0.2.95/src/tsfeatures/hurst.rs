use crate::helpers::common::linreg_f;

/// Estimates the Hurst exponent via rescaled range (R/S) analysis.
///
/// # What it does
/// - Builds the cumulative sum, evaluates R/S statistics for every prefix, and fits `log(R/S)` versus `log(n)`.
/// - Returns the slope of that regression, i.e. the Hurst exponent.
///
/// # In simple terms
/// 1. Compare how the running range grows relative to the standard deviation.
/// 2. Fit a line in log–log space.
/// 3. Interpret the result: ≈0.5 → random walk, >0.5 → persistence, <0.5 → mean reversion.
///
/// # Why it matters
/// - **Long-memory detection**: Classifies persistence in financial and demand series.
/// - **Model choice**: Guides whether ARIMA, fractional differencing, or mean-reverting processes are appropriate.
/// - **Feature benchmarking**: Reproduces the classic tsfeatures Hurst measure.
///
/// # Parameters
/// - `x`: Time-series samples; any NaN or ±∞ short-circuits to `NaN`.
///
/// # Returns
/// Hurst exponent in `(0, 1)` when computable, `0.0` when the series has fewer than two points, or `NaN` for invalid input.
pub fn hurst(x: &[f64]) -> f64 {
    // Fast path for NaN/infinite check
    let n = x.len();

    // If n < 2, return 0.0
    if n < 2 {
        return 0.0;
    }
    
    // Combined NaN/infinite check with cumsum calculation
    let mut y = Vec::with_capacity(n);
    let mut running_sum = 0.0;
    for &val in x {
        if val.is_nan() || val.is_infinite() {
            return f64::NAN;
        }
        running_sum += val;
        y.push(running_sum);
    }
    
    // Pre-allocate all needed space
    let mut valid_log_t = Vec::with_capacity(n - 1);
    let mut valid_log_r_s = Vec::with_capacity(n - 1);
    
    // Variables for incremental standard deviation
    let mut sum_x = 0.0;
    let mut sum_x2 = 0.0;
    
    // Skip first iteration since we skip it anyway in R/S calculation
    sum_x = x[0];
    sum_x2 = x[0] * x[0];
    
    // Start from i=1 since we skip the first R/S value anyway
    for i in 1..n {
        let i_plus_1 = i + 1;
        let t_i = i_plus_1 as f64;
        
        // Incremental update for standard deviation
        sum_x += x[i];
        sum_x2 += x[i] * x[i];
        
        // Standard deviation with ddof=0
        let mean = sum_x / t_i;
        let variance = (sum_x2 / t_i) - (mean * mean);
        
        if variance <= 0.0 {
            continue; // Skip this iteration if std_dev would be 0
        }
        
        let std_dev = variance.sqrt();
        
        // Calculate range efficiently
        let mean_t_i = y[i] / t_i;
        
        // Find min and max in single pass
        let mut min_val = y[0] - mean_t_i;
        let mut max_val = min_val;
        
        for j in 1..i_plus_1 {
            let x_t_j = y[j] - (j + 1) as f64 * mean_t_i;
            if x_t_j < min_val {
                min_val = x_t_j;
            }
            if x_t_j > max_val {
                max_val = x_t_j;
            }
        }
        
        let range = max_val - min_val;
        let r_s = range / std_dev;
        
        if r_s > 0.0 {
            valid_log_t.push(t_i.ln());
            valid_log_r_s.push(r_s.ln());
        }
    }
    
    if valid_log_t.is_empty() {
        return f64::NAN;
    }
    
    // Linear regression for Hurst exponent
    match linreg_f(&valid_log_t, &valid_log_r_s) {
        Ok((hurst_exponent, _intercept)) => hurst_exponent,
        Err(_) => f64::NAN,
    }
}
