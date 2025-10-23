use crate::hctsa::get_all_hctsa_features;
use crate::parallel::common::{FeatureOutput, compute_features_parallel_dyn};

/// Compute all HCTSA features in parallel
pub fn compute_hctsa_parallel(y: Vec<f64>, normalize: bool) -> FeatureOutput {
    let features = get_all_hctsa_features();
    compute_features_parallel_dyn(y, normalize, features)
}

