use crate::{define_feature, feature_registry};
use crate::helpers::common::{min_f, max_f};

/// DN_MinMax - The maximum and minimum values of the input data vector
///
/// # Inputs
///
/// * `y` - The input data vector
/// * `min_or_max` - Either "min" or "max" to return either the minimum or maximum of y
fn dn_minmax(y: &[f64], min_or_max: &str) -> f64 {
    match min_or_max {
        "min" => min_f(&y, Some(true)),
        "max" => max_f(&y, Some(true)),
        _ => f64::NAN,
    }
}

pub fn dn_minmax_min(y: &[f64]) -> f64 {
    dn_minmax(y, "min")
}

pub fn dn_minmax_max(y: &[f64]) -> f64 {
    dn_minmax(y, "max")
}

// FEATURE DEFINITIONS
define_feature!(
    DNMaximum,
    dn_minmax_max,
    "maximum"
);

define_feature!(
    DNMinimum,
    dn_minmax_min,
    "minimum"
);

// FEATURE REGISTRY
feature_registry!(
    DNMaximum,
    DNMinimum,
);


