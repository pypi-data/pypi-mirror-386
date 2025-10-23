//! TSFeatures Python bindings

use pyo3::prelude::*;
use std::collections::HashMap;
use crate::tsfeatures::crossing_points::crossing_points;
use crate::tsfeatures::entropy::entropy;
use crate::tsfeatures::flat_spots::flat_spots;
use crate::tsfeatures::lumpiness::lumpiness;
use crate::tsfeatures::stability::stability;
use crate::tsfeatures::hurst::hurst;
use crate::tsfeatures::nonlinearity::nonlinearity;
use crate::tsfeatures::pacf::pacf_features;
use crate::tsfeatures::unitroot_kpss::unitroot_kpss;
use crate::tsfeatures::unitroot_pp::unitroot_pp;
use crate::tsfeatures::arch_stat::arch_stat;
use crate::parallel::tsfeatures::{compute_tsfeatures_parallel, extract_tsfeatures_cumulative_optimized};
use super::common_types::{TSFeaturesResult, CumulativeFeatures};

#[pyfunction]
pub fn crossing_points_f(y: Vec<f64>) -> f64 {
    crossing_points(&y)
}

#[pyfunction]
pub fn entropy_f(y: Vec<f64>) -> f64 {
    entropy(&y)
}

#[pyfunction]
pub fn flat_spots_f(y: Vec<f64>) -> f64 {
    flat_spots(&y)
}

#[pyfunction]
#[pyo3(signature = (y, freq=1))]
pub fn lumpiness_f(y: Vec<f64>, freq: Option<usize>) -> f64 {
    lumpiness(&y, freq)
}

#[pyfunction]
#[pyo3(signature = (y, freq=1))]
pub fn stability_f(y: Vec<f64>, freq: Option<usize>) -> f64 {
    stability(&y, freq)
}

#[pyfunction]
#[pyo3(signature = (y))]
pub fn hurst_f(y: Vec<f64>) -> f64 {
    hurst(&y)
}

#[pyfunction]
#[pyo3(signature = (y))]
pub fn nonlinearity_f(y: Vec<f64>) -> f64 {
    nonlinearity(y)
}

#[pyfunction]
#[pyo3(signature = (y, freq=1))]
pub fn pacf_features_f(y: Vec<f64>, freq: Option<usize>) -> HashMap<String, f64> {
    pacf_features(y, freq)
}

#[pyfunction]
#[pyo3(signature = (y, freq=1))]
pub fn unitroot_kpss_f(y: Vec<f64>, freq: i32) -> f64 {
    unitroot_kpss(&y, freq)
}

#[pyfunction]
#[pyo3(signature = (y, freq=1))]
pub fn unitroot_pp_f(y: Vec<f64>, freq: i32) -> f64 {
    unitroot_pp(&y, freq)
}

#[pyfunction]
#[pyo3(signature = (y, lags=12, demean=true))]
pub fn arch_stat_f(y: Vec<f64>, lags: usize, demean: bool) -> f64 {
    arch_stat(&y, lags, demean)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None, freq=1, lags=12, demean=true))]
pub fn tsfeatures_all_f(y: Vec<f64>, normalize: Option<bool>, freq: Option<usize>, lags: usize, demean: bool) -> TSFeaturesResult {
    let result = compute_tsfeatures_parallel(y, normalize.unwrap_or(false), freq, lags, demean);
    
    TSFeaturesResult {
        names: result.names,
        values: result.values,
    }
}

#[pyfunction]
#[pyo3(signature = (series, normalize=None, freq=None, lags=12, demean=true, value_column_name=None))]
pub fn extract_tsfeatures_cumulative_f(
    series: Vec<f64>, 
    normalize: Option<bool>, 
    freq: Option<usize>,
    lags: usize,
    demean: bool,
    value_column_name: Option<String>
) -> CumulativeFeatures {
    let normalize = normalize.unwrap_or(false);
    
    let result = extract_tsfeatures_cumulative_optimized(
        &series, 
        normalize, 
        freq,
        lags,
        demean,
        value_column_name.as_deref()
    );

    let feature_names: Vec<String> = if let Some(first_row) = result.data.first() {
        let mut names: Vec<String> = first_row.keys().cloned().collect();
        names.sort();
        names
    } else {
        Vec::new()
    };
    
    let values: Vec<Vec<f64>> = result.data.iter().map(|row| {
        feature_names.iter().map(|name| {
            row.get(name).copied().unwrap_or(f64::NAN)
        }).collect()
    }).collect();
    
    CumulativeFeatures {
        feature_names,
        values,
    }
}
