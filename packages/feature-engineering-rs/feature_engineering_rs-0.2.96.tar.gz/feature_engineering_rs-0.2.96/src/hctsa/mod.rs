// Reference: https://time-series-features.gitbook.io/hctsa-manual/information-about-hctsa/list-of-included-code-files
pub mod distribution;
pub mod correlation;
pub mod helpers;
use crate::parallel::common::FeatureCompute;

/// Get all HCTSA features as a vector of trait objects
pub fn get_all_hctsa_features() -> Vec<Box<dyn FeatureCompute>> {
    let mut features = Vec::new();
    
    // Collect features from each sub-module
    features.extend(distribution::get_features());
    features.extend(correlation::get_features());
    features
}

