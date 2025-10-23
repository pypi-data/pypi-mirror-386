use std::collections::HashMap;
use crate::helpers::common::{mean_f, cumsum_f, linreg_f};

/// KPSS unit-root statistic for level stationarity.
///
/// # What it does
/// - Demeans the series (level regression), accumulates residuals, and estimates the long-run variance with Newey–West weights.
/// - Uses the default lag rule `4 * (n / 100)^(1/4)` from tsfeatures.
///
/// # In simple terms
/// 1. Test whether the level of the series is stationary around a constant.
/// 2. Compare the score with critical values ≈0.347/0.463/0.574/0.739 (10–1% levels).
/// 3. Large numbers imply a unit root (non-stationary level).
///
/// # Why it matters
/// - **Differencing decisions**: Complements PP/ADF tests when choosing integration order.
/// - **Feature parity**: Matches `tsfeatures.unitroot_kpss`.
/// - **Automation**: Handy input for automated forecasting pipelines.
///
/// # Parameters
/// - `x`: Time-series samples.
/// - `freq`: Kept for API symmetry with Python; the current implementation does not use it directly.
///
/// # Returns
/// KPSS statistic as `f64`, or `NaN` when inputs are invalid.

pub fn unitroot_kpss(x: &[f64], freq: i32) -> f64 {
    let n = x.len();
    let nlags = (4.0 * (n as f64 / 100.0).powf(0.25)) as usize;
    
    match kpss(x, "c", nlags) {
        Ok((statistic, _, _, _)) => statistic,
        Err(_) => f64::NAN,
    }
}

/// KPSS test for stationarity
/// 
/// # Parameters
/// - `x`: The data series to test
/// - `regression`: "c" for constant, "ct" for constant and trend
/// - `nlags`: Number of lags to use
/// 
/// # Returns
/// Result containing (kpss_stat, p_value, lags, critical_values) or error
fn kpss(x: &[f64], regression: &str, nlags: usize) -> Result<(f64, f64, usize, HashMap<String, f64>), String> {
    let nobs = x.len();
    
    if nobs == 0 {
        return Err("Input array is empty".to_string());
    }
    
    // Calculate residuals based on regression type
    let resids = match regression {
        "ct" => {
            // Detrend: y_t = beta * t + r_t + e_t
            // Use OLS to fit trend and get residuals
            let t: Vec<f64> = (1..=nobs).map(|i| i as f64).collect();
            let (slope, intercept) = linreg_f(&t, x)
                .map_err(|e| e.to_string())?;
            
            x.iter()
                .enumerate()
                .map(|(i, &xi)| xi - (slope * (i + 1) as f64 + intercept))
                .collect::<Vec<f64>>()
        },
        "c" | _ => {
            // Demean: special case where beta = 0
            let mean = mean_f(x, Some("arithmetic"));
            x.iter().map(|&xi| xi - mean).collect::<Vec<f64>>()
        }
    };
    
    // Critical values from Kwiatkowski et al. (1992)
    let crit = if regression == "ct" {
        vec![0.119, 0.146, 0.176, 0.216]
    } else {
        vec![0.347, 0.463, 0.574, 0.739]
    };
    
    // Ensure nlags is valid
    let nlags = nlags.min(nobs - 1);
    
    // Calculate eta (equation 11 from the paper)
    let cumsum_resids = cumsum_f(&resids);
    let eta = cumsum_resids.iter()
        .map(|&x| x * x)
        .sum::<f64>() / (nobs as f64 * nobs as f64);
    
    // Calculate s_hat (long-run variance estimate)
    let s_hat = sigma_est_kpss(&resids, nobs, nlags)?;
    
    if s_hat <= 0.0 || !s_hat.is_finite() {
        return Err("Invalid variance estimate".to_string());
    }
    
    // Calculate KPSS statistic
    let kpss_stat = eta / s_hat;
    
    // Interpolate p-value
    let pvals = vec![0.10, 0.05, 0.025, 0.01];
    let p_value = interp_pvalue(kpss_stat, &crit, &pvals);
    
    // Create critical values map
    let mut crit_dict = HashMap::new();
    crit_dict.insert("10%".to_string(), crit[0]);
    crit_dict.insert("5%".to_string(), crit[1]);
    crit_dict.insert("2.5%".to_string(), crit[2]);
    crit_dict.insert("1%".to_string(), crit[3]);
    
    Ok((kpss_stat, p_value, nlags, crit_dict))
}

/// Estimate long-run variance using Newey-West estimator
fn sigma_est_kpss(resids: &[f64], nobs: usize, nlags: usize) -> Result<f64, String> {
    // Start with sum of squared residuals
    let mut s_hat = resids.iter().map(|&r| r * r).sum::<f64>();
    
    // Add weighted autocovariances
    for i in 1..=nlags {
        // Calculate dot product of resids[i:] and resids[:nobs-i]
        let resids_prod: f64 = resids[i..]
            .iter()
            .zip(resids[..nobs - i].iter())
            .map(|(&a, &b)| a * b)
            .sum();
        
        // Apply Bartlett weight
        let weight = 1.0 - (i as f64 / (nlags + 1) as f64);
        s_hat += 2.0 * resids_prod * weight;
    }
    
    // Normalize by nobs
    s_hat /= nobs as f64;
    
    if s_hat <= 0.0 {
        return Err("Variance estimate is non-positive".to_string());
    }
    
    Ok(s_hat)
}

/// Interpolate p-value from critical values
fn interp_pvalue(stat: f64, crit: &[f64], pvals: &[f64]) -> f64 {
    // If stat is below smallest critical value, p > largest p-value
    if stat < crit[0] {
        return pvals[0];
    }
    
    // If stat is above largest critical value, p < smallest p-value
    if stat > crit[crit.len() - 1] {
        return pvals[pvals.len() - 1];
    }
    
    // Find the interval and interpolate
    for i in 0..crit.len() - 1 {
        if stat >= crit[i] && stat <= crit[i + 1] {
            // Linear interpolation
            let t = (stat - crit[i]) / (crit[i + 1] - crit[i]);
            return pvals[i] * (1.0 - t) + pvals[i + 1] * t;
        }
    }
    
    // Fallback (shouldn't reach here)
    pvals[0]
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_kpss_empty() {
        let x: Vec<f64> = vec![];
        let result = unitroot_kpss(&x, 1);
        
        assert!(result.is_nan());
    }
    
    #[test]
    fn test_kpss_with_nan() {
        let x = vec![1.0, 2.0, f64::NAN, 4.0, 5.0];
        let result = unitroot_kpss(&x, 1);
        
        assert!(result.is_nan());
    }
}