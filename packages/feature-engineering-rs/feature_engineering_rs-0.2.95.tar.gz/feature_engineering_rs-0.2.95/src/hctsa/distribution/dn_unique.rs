use crate::{define_feature, feature_registry};

pub fn dn_unique(x: &[f64]) -> f64 {
    let n = x.len();
    
    if n == 0 {
        return f64::NAN;
    }
    
    // Sort to find unique values efficiently
    let mut sorted = x.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    
    // Count unique values by comparing consecutive elements
    let unique_count = if n == 1 {
        1
    } else {
        sorted.windows(2)
            .filter(|window| window[0] != window[1])
            .count() + 1 // +1 for the first element
    };
    
    unique_count as f64 / n as f64
}

// FEATURE DEFINITIONS
define_feature!(
    DNUnique,
    dn_unique,
    "propUnique"
);

// FEATURE REGISTRY
feature_registry!(
    DNUnique,
);

