use std::collections::HashMap;
use crate::helpers::common::{mean_f, diff_f};

/// Partial-autocorrelation-based summaries for the original and differenced series.
///
/// # What it does
/// - Computes PACF coefficients up to `max(freq, 5)` using Levinson–Durbin recursion.
/// - Sums the squared lags 1–5 for the raw series, first difference, and second difference.
/// - When `freq > 1`, records the seasonal PACF at lag `freq`.
///
/// # In simple terms
/// 1. Measure how strongly the series correlates with itself after conditioning on lower lags.
/// 2. Repeat after differencing once and twice.
/// 3. Package the results as `x_pacf5`, `diff1x_pacf5`, `diff2x_pacf5`, and optionally `seas_pacf`.
///
/// # Why it matters
/// - **Model identification**: Highlights autoregressive structure under different differencing regimes.
/// - **Seasonality cues**: Seasonal PACF aids seasonal AR order selection.
/// - **Compatibility**: Mirrors the expectations of the original tsfeatures package.
///
/// # Parameters
/// - `x`: Time-series samples (copied internally).
/// - `freq`: Optional seasonal period; caps the PACF lag and unlocks `seas_pacf`.
///
/// # Returns
/// Hash map of PACF-derived features with `NaN` placeholders when inputs are invalid or too short.

pub fn pacf_features(x: Vec<f64>, freq: Option<usize>) -> HashMap<String, f64> {
    let mut output = HashMap::new();
    
    // Handle edge cases
    if x.is_empty() {
        output.insert("x_pacf5".to_string(), f64::NAN);
        output.insert("diff1x_pacf5".to_string(), f64::NAN);
        output.insert("diff2x_pacf5".to_string(), f64::NAN);
        return output;
    }
    
    // NaN/infinite check
    if x.iter().any(|&val| val.is_nan() || val.is_infinite()) {
        output.insert("x_pacf5".to_string(), f64::NAN);
        output.insert("diff1x_pacf5".to_string(), f64::NAN);
        output.insert("diff2x_pacf5".to_string(), f64::NAN);
        return output;
    }
    
    let m = freq.unwrap_or(1);
    let nlags = m.max(5);

    // Calculate PACF for original series
    let pacf_5 = if x.len() > 5 {
        match pacf_ldb(&x, nlags) {
            Ok(pacfx) => {
                // Sum of squares of PACF coefficients 1-5 (excluding lag 0)
                let sum: f64 = pacfx.iter()
                    .skip(1)
                    .take(5)
                    .map(|&v| v * v)
                    .sum();
                sum
            }
            Err(_) => f64::NAN
        }
    } else {
        f64::NAN
    };
    
    // Calculate PACF for first difference
    let diff1_pacf_5 = if x.len() > 6 {
        let diff1 = diff_f(&x);
        if diff1.len() > 5 {
            match pacf_ldb(&diff1, 5) {  
                Ok(pacfx) => {
                    let sum: f64 = pacfx.iter()
                        .skip(1)
                        .take(5)
                        .map(|&v| v * v)
                        .sum();
                    sum
                }
                Err(_) => f64::NAN
            }
        } else {
            f64::NAN
        }
    } else {
        f64::NAN
    };
    
    // Calculate PACF for second difference
    let diff2_pacf_5 = if x.len() > 7 {
        let diff1 = diff_f(&x);
        
        let diff2 = diff_f(&diff1);
        
        if diff2.len() > 5 {
            match pacf_ldb(&diff2, 5) {  
                Ok(pacfx) => {
                    let sum: f64 = pacfx.iter()
                        .skip(1)
                        .take(5)
                        .map(|&v| v * v)
                        .sum();
                    sum
                }
                Err(_) => f64::NAN
            }
        } else {
            f64::NAN
        }
    } else {
        f64::NAN
    };
    
    output.insert("x_pacf5".to_string(), pacf_5);
    output.insert("diff1x_pacf5".to_string(), diff1_pacf_5);
    output.insert("diff2x_pacf5".to_string(), diff2_pacf_5);
    
    // Add seasonal PACF if freq > 1
    if m > 1 {
        let seas_pacf = if x.len() > m {
            match pacf_ldb(&x, nlags) {
                Ok(pacfx) => {
                    if pacfx.len() > m {
                        pacfx[m]
                    } else {
                        f64::NAN
                    }
                }
                Err(_) => f64::NAN
            }
        } else {
            f64::NAN
        };
        output.insert("seas_pacf".to_string(), seas_pacf);
    }
    
    output
}

// Levinson-Durbin recursion for PACF (biased version - 'ldb')
fn pacf_ldb(x: &[f64], nlags: usize) -> Result<Vec<f64>, &'static str> {
    let n = x.len();
    
    // // Check if we have enough data
    if nlags > n / 2 {
        return Err("nlags must be less than half the sample size");
    }
    
    // Calculate autocovariance (not adjusted for bias - matching 'ldb' method)
    let acv = acovf(x, nlags, false)?;
    
    // Levinson-Durbin recursion
    let pacf = levinson_durbin(&acv, nlags)?;
    
    Ok(pacf)
}

// Calculate autocovariance function
fn acovf(x: &[f64], nlags: usize, adjusted: bool) -> Result<Vec<f64>, &'static str> {
    let n = x.len();
    if n == 0 {
        return Err("Empty time series");
    }
    
    // Calculate mean
    let mean = mean_f(x, Some("arithmetic"));
    
    // Center the data
    let centered: Vec<f64> = x.iter().map(|&v| v - mean).collect();
    
    // Calculate autocovariances
    let mut acv = Vec::with_capacity(nlags + 1);
    
    for lag in 0..=nlags {
        if lag >= n {
            acv.push(0.0);
            continue;
        }
        
        let mut sum = 0.0;
        for i in 0..(n - lag) {
            sum += centered[i] * centered[i + lag];
        }
        
        // Divide by n (biased) or n-lag (adjusted)
        let divisor = if adjusted {
            (n - lag) as f64
        } else {
            n as f64
        };
        
        acv.push(sum / divisor);
    }
    
    Ok(acv)
}

// Levinson-Durbin recursion algorithm
fn levinson_durbin(acv: &[f64], nlags: usize) -> Result<Vec<f64>, &'static str> {
    if acv.is_empty() {
        return Err("Empty autocovariance");
    }
    
    let mut pacf = vec![0.0; nlags + 1];
    pacf[0] = 1.0;  // PACF at lag 0 is always 1
    
    if acv[0] == 0.0 {
        return Ok(pacf);  // Return zeros if variance is zero
    }
    
    // Initialize
    let mut phi = vec![vec![0.0; nlags + 1]; nlags + 1];
    
    // First lag
    if nlags > 0 {
        phi[1][1] = acv[1] / acv[0];
        pacf[1] = phi[1][1];
    }
    
    // Recursion for lags 2 to nlags
    for k in 2..=nlags {
        if k > acv.len() - 1 {
            break;
        }
        
        // Calculate numerator
        let mut numer = acv[k];
        for j in 1..k {
            numer -= phi[k-1][j] * acv[k - j];
        }
        
        // Calculate denominator
        let mut denom = acv[0];
        for j in 1..k {
            denom -= phi[k-1][j] * acv[j];
        }
        
        if denom.abs() < 1e-10 {
            break;  // Stop if denominator is too small
        }
        
        // Calculate k-th partial autocorrelation
        phi[k][k] = numer / denom;
        pacf[k] = phi[k][k];
        
        // Update phi coefficients
        for j in 1..k {
            phi[k][j] = phi[k-1][j] - phi[k][k] * phi[k-1][k - j];
        }
    }
    
    Ok(pacf)
}
