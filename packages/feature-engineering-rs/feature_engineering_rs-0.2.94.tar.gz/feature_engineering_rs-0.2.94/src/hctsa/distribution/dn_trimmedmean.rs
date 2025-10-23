use crate::{define_feature, feature_registry};
use crate::helpers::common::mean_f;

/// DN_TrimmedMean - Mean of the trimmed time series.
///
/// Calculates the mean after excluding a specified percentage of the highest
/// and lowest values from the time series.
///
/// # Arguments
///
/// * `y` - The input time series
/// * `n` - The percent of highest and lowest values to exclude from the mean
///         calculation (e.g., 20.0 means trim 10% from each end)
///
/// # Returns
///
/// The trimmed mean of the time series.
fn dn_trimmed_mean(y: &[f64], n: Option<f64>) -> f64 {
    let n = n.unwrap_or(0.0);
    
    // Handle edge cases
    if y.is_empty() {
        return f64::NAN;
    }
    
    if n <= 0.0 {
        // No trimming, return normal mean
        return y.iter().sum::<f64>() / y.len() as f64;
    }
    
    if n >= 100.0 {
        // Trimming everything
        return f64::NAN;
    }
    
    // Sort the data
    let mut sorted_y = y.to_vec();
    sorted_y.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    
    // Calculate number of elements to trim from each end
    let n_trim = ((n / 100.0) * sorted_y.len() as f64 / 2.0).floor() as usize;
    
    // If we're trimming everything, return NaN
    if n_trim * 2 >= sorted_y.len() {
        return f64::NAN;
    }
    
    // Calculate mean of the middle portion
    let trimmed = &sorted_y[n_trim..sorted_y.len() - n_trim];
    
    if trimmed.is_empty() {
        return f64::NAN;
    }
    
    mean_f(trimmed, Some("arithmetic"))
}

pub fn dn_trimmed_mean_1(y: &[f64]) -> f64 {
    dn_trimmed_mean(y, Some(1.0))
}

pub fn dn_trimmed_mean_5(y: &[f64]) -> f64 {
    dn_trimmed_mean(y, Some(5.0))
}

pub fn dn_trimmed_mean_10(y: &[f64]) -> f64 {
    dn_trimmed_mean(y, Some(10.0))
}

pub fn dn_trimmed_mean_25(y: &[f64]) -> f64 {
    dn_trimmed_mean(y, Some(25.0))
}

pub fn dn_trimmed_mean_50(y: &[f64]) -> f64 {
    dn_trimmed_mean(y, Some(50.0))
}

// FEATURE DEFINITIONS
define_feature!(
    DNTrimmedMean1,
    dn_trimmed_mean_1,
    "trimmed_mean_1"
);

define_feature!(
    DNTrimmedMean5,
    dn_trimmed_mean_5,
    "trimmed_mean_5"
);

define_feature!(
    DNTrimmedMean10,
    dn_trimmed_mean_10,
    "trimmed_mean_10"
);

define_feature!(
    DNTrimmedMean25,
    dn_trimmed_mean_25,
    "trimmed_mean_25"
);

define_feature!(
    DNTrimmedMean50,
    dn_trimmed_mean_50,
    "trimmed_mean_50"
);

// FEATURE REGISTRY
feature_registry!(
    DNTrimmedMean1,
    DNTrimmedMean5,
    DNTrimmedMean10,
    DNTrimmedMean25,
    DNTrimmedMean50,
);

