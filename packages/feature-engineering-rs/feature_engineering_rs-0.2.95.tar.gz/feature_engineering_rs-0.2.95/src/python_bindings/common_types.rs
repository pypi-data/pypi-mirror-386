//! Common Python types and result structures

use pyo3::prelude::*;

#[pyclass]
pub struct Catch22Result {
    #[pyo3(get)]
    pub names: Vec<String>,
    #[pyo3(get)]
    pub values: Vec<f64>,
}

#[pyclass]
pub struct HCTSAResult {
    #[pyo3(get)]
    pub names: Vec<String>,
    #[pyo3(get)]
    pub values: Vec<f64>,
}

#[pyclass]
pub struct TSFeaturesResult {
    #[pyo3(get)]
    pub names: Vec<String>,
    #[pyo3(get)]
    pub values: Vec<f64>,
}

#[pyclass]
pub struct CombinedResult {
    #[pyo3(get)]
    pub names: Vec<String>,
    #[pyo3(get)]
    pub values: Vec<f64>,
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct CumulativeFeatures {
    #[pyo3(get)]
    pub feature_names: Vec<String>,
    #[pyo3(get)]
    pub values: Vec<Vec<f64>>,
}
