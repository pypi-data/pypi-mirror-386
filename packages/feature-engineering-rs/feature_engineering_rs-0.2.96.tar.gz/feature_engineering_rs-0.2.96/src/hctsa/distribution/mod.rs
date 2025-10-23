// Declare sub-modules
pub mod dn_mean;
pub mod dn_minmax;
pub mod dn_histogrammode;
pub mod dn_histogramasymmetry;
pub mod dn_trimmedmean;
pub mod dn_moments;
pub mod dn_withinp;
pub mod dn_pleft;
pub mod dn_quantile;
pub mod dn_proportionvalues;
pub mod dn_burstiness;
pub mod dn_unique;
pub mod dn_cv;
pub mod dn_spread;
pub mod dn_customskewness;
pub mod dn_highlowmu;
// pub mod dn_removepoints;
pub mod dn_outliertest;

use crate::parallel::common::FeatureCompute;

/// Get all distribution features as a vector of trait objects
pub fn get_features() -> Vec<Box<dyn FeatureCompute>> {
    let mut features = Vec::new();
    
    // Collect features from each sub-module
    features.extend(dn_mean::get_features());
    features.extend(dn_trimmedmean::get_features());
    features.extend(dn_minmax::get_features());
    features.extend(dn_burstiness::get_features());
    features.extend(dn_spread::get_features());
    features.extend(dn_moments::get_features());
    features.extend(dn_customskewness::get_features());
    features.extend(dn_histogrammode::get_features());
    features.extend(dn_histogramasymmetry::get_features());
    features.extend(dn_withinp::get_features());
    features.extend(dn_pleft::get_features());
    features.extend(dn_quantile::get_features());
    features.extend(dn_proportionvalues::get_features());
    features.extend(dn_unique::get_features());
    features.extend(dn_cv::get_features());
    features.extend(dn_highlowmu::get_features());
    features.extend(dn_outliertest::get_features());
    features
}