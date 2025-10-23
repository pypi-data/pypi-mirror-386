pub mod co_nonlinearautocorr;
pub mod co_autocorr;
pub mod co_histogramami;
pub mod co_firstcrossing;

use crate::parallel::common::FeatureCompute;

/// Get all correlation features as a vector of trait objects
pub fn get_features() -> Vec<Box<dyn FeatureCompute>> {
    let mut features = Vec::new();
    
    // Collect features from each sub-module
    // features.extend(co_nonlinearautocorr::get_features());
    features.extend(co_autocorr::get_features());
    features.extend(co_firstcrossing::get_features());
    features.extend(co_histogramami::get_features());
    features
}