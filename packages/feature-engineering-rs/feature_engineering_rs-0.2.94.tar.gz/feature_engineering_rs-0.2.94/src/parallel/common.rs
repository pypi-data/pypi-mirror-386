use rayon::prelude::*;
use std::sync::Arc;
use std::collections::HashMap;
use crate::helpers::common::zscore_norm2_f;

/// Common trait for all feature computation
pub trait FeatureCompute: Send + Sync {
    fn compute(&self, y: &[f64], normalize: bool) -> f64;
    fn name(&self) -> String;
}

/// Generic result structure for feature computation
#[derive(Debug, Clone)]
pub struct FeatureOutput {
    pub names: Vec<String>,
    pub values: Vec<f64>,
}

/// Generic cumulative result structure
#[derive(Debug, Clone)]
pub struct CumulativeResult {
    pub data: Vec<HashMap<String, f64>>,
}

/// Generic parallel feature computation for trait objects
pub fn compute_features_parallel_dyn(
    y: Vec<f64>,
    normalize: bool,
    features: Vec<Box<dyn FeatureCompute>>,
) -> FeatureOutput {
    let normalized_y = if normalize {
        crate::helpers::common::zscore_norm2_f(&y)
    } else {
        y
    };

    let y_arc = Arc::new(normalized_y);

    let results: Vec<(String, f64)> = features
        .into_par_iter()
        .map(|feature| {
            let name = feature.name();
            let value = feature.compute(&y_arc, normalize);
            (name, value)
        })
        .collect();

    let (names, values): (Vec<String>, Vec<f64>) = results.into_iter().unzip();
    FeatureOutput { names, values }
}

/// Generic cumulative feature extraction
pub fn extract_features_cumulative_optimized<F>(
    series: &[f64],
    normalize: bool,
    value_column_name: Option<&str>,
    compute_fn: F,
) -> CumulativeResult
where
    F: Fn(&[f64], bool) -> FeatureOutput + Sync,
{
    let series_len = series.len();
    let column_name = value_column_name.unwrap_or("VALUE");
    
    let mut results = vec![HashMap::new(); series_len];
    
    results
        .par_iter_mut()
        .enumerate()
        .for_each(|(end_idx, result_map)| {
            let window_data = &series[..=end_idx];
            let features = compute_fn(window_data, normalize);
            
            result_map.insert(column_name.to_string(), series[end_idx]);
            
            for (name, value) in features.names.iter().zip(features.values.iter()) {
                result_map.insert(name.clone(), *value);
            }
        });
    
    CumulativeResult { data: results }
}