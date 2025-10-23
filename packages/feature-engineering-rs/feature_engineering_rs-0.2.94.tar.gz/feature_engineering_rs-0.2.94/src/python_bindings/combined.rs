//! Combined features Python bindings

use pyo3::prelude::*;
use crate::parallel::combined::{compute_combined_parallel, extract_combined_features_cumulative_optimized, CombinedParams};
use super::common_types::{CombinedResult, CumulativeFeatures};

#[pyfunction]
#[pyo3(signature = (y, normalize=None, catch24=None, catchamouse16=None, hctsa=None, freq=None, lags=12, demean=true))]
pub fn combined_all_f(
    y: Vec<f64>, 
    normalize: Option<bool>, 
    catch24: Option<bool>, 
    catchamouse16: Option<bool>,
    hctsa: Option<bool>,
    freq: Option<usize>, 
    lags: usize, 
    demean: bool
) -> CombinedResult {
    let result = compute_combined_parallel(
        y, 
        CombinedParams {
            normalize: normalize.unwrap_or(true),
            catch24: catch24.unwrap_or(false),
            hctsa: hctsa.unwrap_or(false),
            catchamouse16: catchamouse16.unwrap_or(true),
            freq,
            lags,
            demean,
        }
    );
    
    CombinedResult {
        names: result.names,
        values: result.values,
    }
}

#[pyfunction]
#[pyo3(signature = (series, normalize=None, catch24=None, catchamouse16=None, hctsa=None, freq=None, lags=12, demean=true, value_column_name=None))]
pub fn extract_combined_features_cumulative_f(
    series: Vec<f64>, 
    normalize: Option<bool>, 
    catch24: Option<bool>,
    catchamouse16: Option<bool>,
    hctsa: Option<bool>,
    freq: Option<usize>,
    lags: usize,
    demean: bool,
    value_column_name: Option<String>
) -> CumulativeFeatures {
    let normalize = normalize.unwrap_or(true);
    let catch24 = catch24.unwrap_or(false);
    let catchamouse16 = catchamouse16.unwrap_or(true);
        
    let result = extract_combined_features_cumulative_optimized(
        &series,
        CombinedParams {
            normalize,
            hctsa: hctsa.unwrap_or(false),
            catch24,
            catchamouse16,
            freq,
            lags,
            demean,
        },
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
