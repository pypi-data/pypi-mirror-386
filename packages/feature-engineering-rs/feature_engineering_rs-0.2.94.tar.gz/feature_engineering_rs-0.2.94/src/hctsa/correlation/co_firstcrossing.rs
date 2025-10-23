use crate::{define_feature, feature_registry};
use crate::hctsa::correlation::co_autocorr::co_autocorr;
use crate::hctsa::helpers::bf_point_of_crossing::bf_point_of_crossing;

/// Finds where the autocorrelation function (ACF) first crosses a threshold.
///
/// This function computes the autocorrelation of a time series and identifies
/// the lag at which it first crosses below (or above) a specified threshold.
/// This is useful for determining the "memory" or "decorrelation time" of a time series.
///
/// # Arguments
///
/// * `y` - Input time series
/// * `threshold` - Threshold value to detect crossing (typically 0 or 1/e)
///
/// # Returns
///
/// A tuple containing:
/// * `.0` - **Discrete lag** (usize): The first integer lag where ACF crosses the threshold
/// * `.1` - **Continuous lag** (f64): Linear interpolation between points for sub-lag precision
pub fn co_firstcrossing(y: &[f64], threshold: f64) -> (usize, f64) {
    // Compute autocorrelation using Fourier method
    let corrs = co_autocorr(y, None);
    
    // Find the discrete first crossing point
    bf_point_of_crossing(&corrs, threshold)
}

pub fn firstzero_acf_tau(y: &[f64]) -> f64 {
    co_firstcrossing(y, 0.0).0 as f64
}

pub fn firstzero_acf_point(y: &[f64]) -> f64 {
    co_firstcrossing(y, 0.0).1
}

pub fn firstcrossing_1e_acf_tau(y: &[f64]) -> f64 {
    co_firstcrossing(y, 1.0 / (1.0_f64).exp()).0 as f64
}

pub fn firstcrossing_1e_acf_point(y: &[f64]) -> f64 {
    co_firstcrossing(y, 1.0 / (1.0_f64).exp()).1
}

define_feature!(
    FirstZeroACFTau,
    firstzero_acf_tau,
    "firstZero_acf_tau"
);

define_feature!(
    FirstZeroACFPoint,
    firstzero_acf_point,
    "firstZero_acf_point"
);

define_feature!(
    FirstCrossing1eACFTau,
    firstcrossing_1e_acf_tau,
    "firstCrossing_1e_acf_tau"
);

define_feature!(
    FirstCrossing1eACFPoint,
    firstcrossing_1e_acf_point,
    "firstCrossing_1e_acf_point"
);

feature_registry!(
    FirstZeroACFTau,
    FirstZeroACFPoint,
    FirstCrossing1eACFTau,
    FirstCrossing1eACFPoint,
);