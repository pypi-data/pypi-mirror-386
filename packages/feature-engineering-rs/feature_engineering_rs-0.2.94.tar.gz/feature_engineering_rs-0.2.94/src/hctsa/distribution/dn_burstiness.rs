use crate::{define_feature, feature_registry};
use crate::helpers::common::{mean_f, stdev_f};

fn dn_burstiness_full(y: &[f64], which: &str) -> f64 {
    // Check for NaN values
    if y.iter().any(|&v| v.is_nan()) {
        return f64::NAN;
    }
    
    // Calculate coefficient of variation: r = std(y)/mean(y)
    let mean_val = mean_f(y, Some("arithmetic"));
    let std_val = stdev_f(y, 1);
    
    let r = std_val / mean_val;
    let n = y.len() as f64;
    
    match which {
        "goh" => {
            let b_goh = (r - 1.0) / (r + 1.0);
            b_goh
        },
        "kim" => {
            let sqrt_n_plus_1 = (n + 1.0).sqrt();
            let sqrt_n_minus_1 = (n - 1.0).sqrt();
            let b_kim = (sqrt_n_plus_1 * r - sqrt_n_minus_1) / 
                        ((sqrt_n_plus_1 - 2.0) * r + sqrt_n_minus_1);
            b_kim
        },
        _ => {
            return f64::NAN;
        }
    }
}

pub fn dn_burstiness_goh(y: &[f64]) -> f64 {
    dn_burstiness_full(y, "goh")
}

pub fn dn_burstiness_kim(y: &[f64]) -> f64 {
    dn_burstiness_full(y, "kim")
}

// FEATURE DEFINITIONS
define_feature!(
    DNBurstinessGoh,
    dn_burstiness_goh,
    "burstiness_Goh"
);

define_feature!(
    DNBurstinessKim,
    dn_burstiness_kim,
    "burstiness_Kim"
);

// FEATURE REGISTRY
feature_registry!(
    DNBurstinessGoh,
    DNBurstinessKim,
);

