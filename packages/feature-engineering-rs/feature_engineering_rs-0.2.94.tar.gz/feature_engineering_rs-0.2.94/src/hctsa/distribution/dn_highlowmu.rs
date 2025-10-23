use crate::{define_feature, feature_registry};
use crate::helpers::common::{mean_f};

pub fn dn_highlowmu(y: &[f64]) -> f64 {
    let mu = mean_f(y, Some("arithmetic"));
    
    let high: Vec<f64> = y.iter().copied().filter(|&x| x > mu).collect();
    let low: Vec<f64> = y.iter().copied().filter(|&x| x < mu).collect();
    
    let mhi = mean_f(&high, Some("arithmetic"));
    let mlo = mean_f(&low, Some("arithmetic"));
    
    (mhi - mu) / (mu - mlo)
}

// FEATURE DEFINITIONS
define_feature!(
    DNHighLowMu,
    dn_highlowmu,
    "HighLowMu"
);

// FEATURE REGISTRY
feature_registry!(
    DNHighLowMu,
);