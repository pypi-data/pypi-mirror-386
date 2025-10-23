use crate::helpers::common::nan_variance_f;

/// Variance-of-variances across equal-width windows—how “lumpy” the volatility is.
///
/// # What it does
/// - Splits the series into contiguous windows whose width is `freq` (or 10 when `freq` is 1/None).
/// - Computes the variance inside each window, ignoring NaNs.
/// - Returns the sample variance of those variances, falling back to `0.0` when fewer than two windows survive.
///
/// # In simple terms
/// 1. Break the series into blocks.
/// 2. Measure how volatile each block is.
/// 3. See how much those volatility scores fluctuate.
///
/// # Why it matters
/// - **Regime detection**: Large values signal abrupt changes in variability.
/// - **Forecast difficulty**: Helps decide when variance-stabilizing transforms are needed.
/// - **Benchmark parity**: Mirrors the original tsfeatures implementation used in forecasting competitions.
///
/// # Parameters
/// - `x`: Time-series samples.
/// - `freq`: Optional seasonal period; when 1 or absent we fall back to blocks of length 10.
///
/// # Returns
/// Sample variance of window variances (`0.0` when the series is too short, `NaN` only when the input itself is degenerate).

pub fn lumpiness(x: &[f64], freq: Option<usize>) -> f64 {
    // Handle edge cases
    if x.is_empty() {
        return f64::NAN;
    }
    
    // Determine window width
    let width = freq.unwrap_or(1);
    let width = if width == 1 { 10 } else { width };
    
    let nr = x.len();
    
    // If series is too short, return 0
    if nr < 2 * width {
        return 0.0;
    }
    
    // Create windows and calculate their variances
    let mut variances = Vec::new();
    let mut start = 0;
    
    while start + width <= nr {
        let window = &x[start..start + width];
        
        // Calculate variance using nanvar equivalent
        if window.len() > 1 {
            let var = nan_variance_f(window, 1);  
            if !var.is_nan() {
                variances.push(var);
            }
        }
        
        start += width;
    }
    
    // Calculate variance of the variances
    if variances.len() < 2 {
        0.0
    } else {
        nan_variance_f(&variances, 1)
    }
}

