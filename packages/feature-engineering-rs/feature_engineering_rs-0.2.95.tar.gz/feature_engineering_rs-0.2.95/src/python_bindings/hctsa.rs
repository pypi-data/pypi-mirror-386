// HCTSA Python bindings

use pyo3::prelude::*;
use super::common_types::HCTSAResult;


use crate::hctsa::distribution::dn_mean::{dn_mean_arithmetic, dn_median, dn_geometric_mean, dn_harmonic_mean, dn_rms_mean, dn_iqm_mean, dn_midhinge_mean};
// use crate::hctsa::distribution::dn_minmax::dn_minmax;
use crate::hctsa::distribution::dn_histogrammode::{dn_histogrammode_5, dn_histogrammode_10, dn_histogrammode_12, dn_histogrammode_21, dn_histogrammode_52,
dn_histogrammode_abs_5, dn_histogrammode_abs_10, dn_histogrammode_abs_12, dn_histogrammode_abs_21, dn_histogrammode_abs_52};
use crate::hctsa::distribution::dn_histogramasymmetry::{dn_histogramasymmetry_5_densitydiff, dn_histogramasymmetry_5_modeprobpos, dn_histogramasymmetry_5_modeprobneg, dn_histogramasymmetry_5_modediff, dn_histogramasymmetry_5_posmode, dn_histogramasymmetry_5_negmode, dn_histogramasymmetry_5_modeasymmetry, dn_histogramasymmetry_11_densitydiff, 
    dn_histogramasymmetry_11_modeprobpos, dn_histogramasymmetry_11_modeprobneg, dn_histogramasymmetry_11_modediff,
     dn_histogramasymmetry_11_posmode, dn_histogramasymmetry_11_negmode, dn_histogramasymmetry_11_modeasymmetry, dn_histogramasymmetry_15_densitydiff, dn_histogramasymmetry_15_modeprobpos, dn_histogramasymmetry_15_modeprobneg, dn_histogramasymmetry_15_modediff, dn_histogramasymmetry_15_posmode, dn_histogramasymmetry_15_negmode, dn_histogramasymmetry_15_modeasymmetry};
use crate::hctsa::distribution::dn_trimmedmean::{dn_trimmed_mean_1, dn_trimmed_mean_5, dn_trimmed_mean_10, dn_trimmed_mean_25, dn_trimmed_mean_50};
use crate::parallel::hctsa::compute_hctsa_parallel;

/////////////////////////////////////////////////////////////
// DN_Mean
#[pyfunction]
pub fn dn_mean_arithmetic_f(y: Vec<f64>) -> f64 {
    dn_mean_arithmetic(&y)
}

#[pyfunction]
pub fn dn_median_f(y: Vec<f64>) -> f64 {
    dn_median(&y)
}

#[pyfunction]
pub fn dn_geometric_mean_f(y: Vec<f64>) -> f64 {
    dn_geometric_mean(&y)
}

#[pyfunction]
pub fn dn_harmonic_mean_f(y: Vec<f64>) -> f64 {
    dn_harmonic_mean(&y)
}

#[pyfunction]
pub fn dn_rms_mean_f(y: Vec<f64>) -> f64 {
    dn_rms_mean(&y)
}

#[pyfunction]
pub fn dn_iqm_mean_f(y: Vec<f64>) -> f64 {
    dn_iqm_mean(&y)
}

#[pyfunction]
pub fn dn_midhinge_mean_f(y: Vec<f64>) -> f64 {
    dn_midhinge_mean(&y)
}


/////////////////////////////////////////////////////////////
// DN_MinMax
// #[pyfunction]
// pub fn dn_minmax_f(y: Vec<f64>, min_or_max: &str) -> f64 {
//     dn_minmax(&y, min_or_max)
// }

/////////////////////////////////////////////////////////////
// DN_HistogramMode
#[pyfunction]
pub fn dn_histogrammode_5_f(y: Vec<f64>) -> f64 {
    dn_histogrammode_5(&y)
}

#[pyfunction]
pub fn dn_histogrammode_10_f(y: Vec<f64>) -> f64 {
    dn_histogrammode_10(&y)
}

#[pyfunction]
pub fn dn_histogrammode_12_f(y: Vec<f64>) -> f64 {
    dn_histogrammode_12(&y)
}

#[pyfunction]
pub fn dn_histogrammode_21_f(y: Vec<f64>) -> f64 {
    dn_histogrammode_21(&y)
}

#[pyfunction]
pub fn dn_histogrammode_52_f(y: Vec<f64>) -> f64 {
    dn_histogrammode_52(&y)
}

/////////////////////////////////////////////////////////////
// DN_HistogramMode_Abs
#[pyfunction]
pub fn dn_histogrammode_abs_5_f(y: Vec<f64>) -> f64 {
    dn_histogrammode_abs_5(&y)
}

#[pyfunction]
pub fn dn_histogrammode_abs_10_f(y: Vec<f64>) -> f64 {
    dn_histogrammode_abs_10(&y)
}

#[pyfunction]
pub fn dn_histogrammode_abs_12_f(y: Vec<f64>) -> f64 {
    dn_histogrammode_abs_12(&y)
}

#[pyfunction]
pub fn dn_histogrammode_abs_21_f(y: Vec<f64>) -> f64 {
    dn_histogrammode_abs_21(&y)
}


#[pyfunction]
pub fn dn_histogrammode_abs_52_f(y: Vec<f64>) -> f64 {
    dn_histogrammode_abs_52(&y)
}

/////////////////////////////////////////////////////////////
// DN_HistogramAsymmetry 5
#[pyfunction]
pub fn dn_histogramasymmetry_5_densitydiff_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_5_densitydiff(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_5_modeprobpos_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_5_modeprobpos(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_5_modeprobneg_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_5_modeprobneg(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_5_modediff_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_5_modediff(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_5_posmode_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_5_posmode(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_5_negmode_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_5_negmode(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_5_modeasymmetry_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_5_modeasymmetry(&y)
}

/////////////////////////////////////////////////////////////
// DN_HistogramAsymmetry 11
#[pyfunction]
pub fn dn_histogramasymmetry_11_densitydiff_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_11_densitydiff(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_11_modeprobpos_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_11_modeprobpos(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_11_modeprobneg_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_11_modeprobneg(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_11_modediff_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_11_modediff(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_11_posmode_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_11_posmode(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_11_negmode_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_11_negmode(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_11_modeasymmetry_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_11_modeasymmetry(&y)
}

/////////////////////////////////////////////////////////////
// DN_HistogramAsymmetry 15
#[pyfunction]
pub fn dn_histogramasymmetry_15_densitydiff_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_15_densitydiff(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_15_modeprobpos_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_15_modeprobpos(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_15_modeprobneg_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_15_modeprobneg(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_15_modediff_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_15_modediff(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_15_posmode_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_15_posmode(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_15_negmode_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_15_negmode(&y)
}

#[pyfunction]
pub fn dn_histogramasymmetry_15_modeasymmetry_f(y: Vec<f64>) -> f64 {
    dn_histogramasymmetry_15_modeasymmetry(&y)
}

/////////////////////////////////////////////////////////////
// DN_TrimmedMean
#[pyfunction]
pub fn dn_trimmed_mean_1_f(y: Vec<f64>) -> f64 {
    dn_trimmed_mean_1(&y)
}

#[pyfunction]
pub fn dn_trimmed_mean_5_f(y: Vec<f64>) -> f64 {
    dn_trimmed_mean_5(&y)
}

#[pyfunction]
pub fn dn_trimmed_mean_10_f(y: Vec<f64>) -> f64 {
    dn_trimmed_mean_10(&y)
}

#[pyfunction]
pub fn dn_trimmed_mean_25_f(y: Vec<f64>) -> f64 {
    dn_trimmed_mean_25(&y)
}

#[pyfunction]
pub fn dn_trimmed_mean_50_f(y: Vec<f64>) -> f64 {
    dn_trimmed_mean_50(&y)
}

/////////////////////////////////////////////////////////////
// HCTSA
#[pyfunction]
pub fn compute_hctsa_parallel_f(y: Vec<f64>, normalize: bool) -> HCTSAResult {
    let result = compute_hctsa_parallel(y, normalize);

    HCTSAResult {
        names: result.names,
        values: result.values,
    }
}

