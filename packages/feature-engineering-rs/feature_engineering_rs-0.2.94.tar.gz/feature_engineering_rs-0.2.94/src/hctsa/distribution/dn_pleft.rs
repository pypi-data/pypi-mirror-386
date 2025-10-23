use crate::{define_feature, feature_registry};
use crate::helpers::common::{mean_f, stdev_f, quantile_f};

fn dn_pleft(y: &[f64], th: Option<f64>) -> f64 {
    let th = th.unwrap_or(0.1);
    let mean_val = mean_f(y, Some("arithmetic"));
    
    // Calculate absolute deviations from mean
    let abs_deviations: Vec<f64> = y.iter().map(|&x| (x - mean_val).abs()).collect();
    
    // Get the quantile
    let p = quantile_f(&abs_deviations, 1.0 - th);
    
    // Normalize by standard deviation
    p / stdev_f(y, 0)
}

pub fn dn_pleft_005(y: &[f64]) -> f64 {
    dn_pleft(y, Some(0.05))
}

pub fn dn_pleft_01(y: &[f64]) -> f64 {
    dn_pleft(y, Some(0.1))
}

pub fn dn_pleft_02(y: &[f64]) -> f64 {
    dn_pleft(y, Some(0.2))
}

pub fn dn_pleft_03(y: &[f64]) -> f64 {
    dn_pleft(y, Some(0.3))
}

pub fn dn_pleft_04(y: &[f64]) -> f64 {
    dn_pleft(y, Some(0.4))
}

pub fn dn_pleft_05(y: &[f64]) -> f64 {
    dn_pleft(y, Some(0.5))
}

// FEATURE DEFINITIONS
define_feature!(
    DNPleft005,
    dn_pleft_005,
    "DN_pleft_005"
);

define_feature!(
    DNPleft01,
    dn_pleft_01,
    "DN_pleft_01"
);

define_feature!(
    DNPleft02,
    dn_pleft_02,
    "DN_pleft_02"
);

define_feature!(
    DNPleft03,
    dn_pleft_03,
    "DN_pleft_03"
);

define_feature!(
    DNPleft04,
    dn_pleft_04,
    "DN_pleft_04"
);

define_feature!(
    DNPleft05,
    dn_pleft_05,
    "DN_pleft_05"
);

// FEATURE REGISTRY
feature_registry!(
    DNPleft005,
    DNPleft01,
    DNPleft02,
    DNPleft03,
    DNPleft04,
    DNPleft05,
);

