use crate::{define_feature, feature_registry};
use crate::helpers::common::{mean_f, stdev_f};

/// Coefficient of variation of order k: (std^k) / (mean^k)
///
/// # Arguments
/// * `y` - Input time series
/// * `k` - Order of coefficient of variation (typically 1)
///
/// # Returns
/// The coefficient of variation, or NaN if invalid
fn dn_cv(y: &[f64], k: Option<f64>) -> f64 {
    // Default k = 1 if not provided
    let k = k.unwrap_or(1.0);
    
    // Input validation
    if y.is_empty() || y.iter().any(|&v| v.is_nan()) {
        return f64::NAN;
    }
    
    // Note: In MATLAB version, non-integer or negative k triggers a warning
    // but computation continues. We'll do the same.
    if k < 0.0 || (k.fract() != 0.0 && k != 0.0) {
        eprintln!("Warning: k should probably be a positive integer, got {}", k);
    }
    
    let mean_val = mean_f(y, Some("arithmetic"));
    let std_val = stdev_f(y, 1);
    
    // Handle zero mean to avoid division by zero
    if mean_val.abs() < f64::EPSILON {
        return f64::NAN;
    }
    
    // Compute (std^k) / (mean^k)
    std_val.powf(k) / mean_val.powf(k)
}

pub fn dn_cv_1(y: &[f64]) -> f64 {
    dn_cv(y, Some(1.0))
}

pub fn dn_cv_2(y: &[f64]) -> f64 {
    dn_cv(y, Some(2.0))
}

// FEATURE DEFINITIONS
define_feature!(
    DNCV1,
    dn_cv_1,
    "coeff_var_1"
);

define_feature!(
    DNCV2,
    dn_cv_2,
    "coeff_var_2"
);

// FEATURE REGISTRY
feature_registry!(
    DNCV1,
    DNCV2,
);

