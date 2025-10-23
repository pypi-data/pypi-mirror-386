use crate::{define_feature, feature_registry};
use crate::hctsa::correlation::co_autocorr::co_autocorr;
use std::cmp::Ordering;

fn dn_removepoints(y: &[f64], remove_how: &str, p: f64, mode: &str, stat: &str) -> f64 {
    // NaN check
    if y.iter().any(|&val| val.is_nan()) {
        return f64::NAN;
    }

    let size = y.len();

    if size < 3 {
        return f64::NAN;
    }
    
    // Create vector of (absolute_value, original_index) pairs
    let mut abs_y: Vec<(f64, usize)> = y.iter()
        .enumerate()
        .map(|(i, &val)| (val.abs(), i))
        .collect();
    
    // Sort by absolute value in descending order (largest first)
    abs_y.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(Ordering::Equal));
    
    // Keep first 50% (smallest absolute values after sorting descending means we take the end)
    let keep_size = (size as f64 * 0.5).round() as usize;
    
    // Get the indices of the smallest 50% in absolute value
    let mut sorted_ind: Vec<usize> = abs_y[..keep_size]
        .iter()
        .map(|(_, idx)| *idx)
        .collect();
    
    // Sort indices to maintain temporal order
    sorted_ind.sort_unstable();
    
    // Create transformed time series
    let y_transform: Vec<f64> = sorted_ind.iter()
        .map(|&idx| y[idx])
        .collect();
    
    // Compute autocorrelation at lag 2 for both series
    let acf_y = co_autocorr(y, &[1, 2, 3, 4, 5, 6, 7, 8]);
    let acf_y_transform = co_autocorr(&y_transform, &[1, 2, 3, 4, 5, 6, 7, 8]);
    
    // Return ratio
    acf_y_transform[0] / acf_y[0]   
}

