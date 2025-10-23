use crate::helpers::common::{mean_f, median_f};
use crate::{define_feature, feature_registry};

/// DN_Mean - A given measure of location of a data vector.
///
/// # Arguments
///
/// * `y` - The input data vector
/// * `mean_type` - The type of mean to calculate (default: "arithmetic")
///                 "median", "geometric", "harmonic", "rms", "iqm", "midhinge"
/// # Returns
///
/// The calculated mean.
fn dn_mean(y: &[f64], mean_type: Option<&str>) -> f64 {
    let mean_type = mean_type.unwrap_or("arithmetic");

    match mean_type {
        "arithmetic" => mean_f(y, Some("arithmetic")),
        "median" => median_f(y, Some(false)),
        "geometric" => mean_f(y, Some("geometric")),
        "harmonic" => mean_f(y, Some("harmonic")),
        "rms" => mean_f(y, Some("rms")),
        "midhinge" => mean_f(y, Some("midhinge")),
        _ => mean_f(y, Some("arithmetic")),
    }
}

pub fn dn_mean_arithmetic(y: &[f64]) -> f64 {
    dn_mean(y, Some("arithmetic"))
}

pub fn dn_median(y: &[f64]) -> f64 {
    median_f(y, Some(false))
}

pub fn dn_geometric_mean(y: &[f64]) -> f64 {
    dn_mean(y, Some("geometric"))
}

pub fn dn_harmonic_mean(y: &[f64]) -> f64 {
    dn_mean(y, Some("harmonic"))
}

pub fn dn_rms_mean(y: &[f64]) -> f64 {
    dn_mean(y, Some("rms"))
}

pub fn dn_iqm_mean(y: &[f64]) -> f64 {
    dn_mean(y, Some("iqm"))
}

pub fn dn_midhinge_mean(y: &[f64]) -> f64 {
    dn_mean(y, Some("midhinge"))
}

// FEATURE DEFINITIONS
define_feature!(
    DNMeanArithmetic,
    dn_mean_arithmetic,
    "mean"
);

define_feature!(
    DNHarmonicMean,
    dn_harmonic_mean,
    "harmonic_mean"
);

define_feature!(
    DNMedian,
    dn_median,
    "median"
);

define_feature!(
    DNMidhingeMean,
    dn_midhinge_mean,
    "midhinge"
);

define_feature!(
    DNRMSMean,
    dn_rms_mean,
    "rms"
);


// FEATURE REGISTRY
feature_registry!(
    DNMeanArithmetic,
    DNHarmonicMean,
    DNMedian,
    DNMidhingeMean,
    DNRMSMean,
);



