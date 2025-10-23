//! Catch22 Python bindings

use pyo3::prelude::*;
use crate::catch22::co_auto_corr::{
    co_embed2_dist_tau_d_expfit_meandiff, co_f1ecac, co_first_min_ac, co_histogram_ami_even_2_5,
    co_trev_1_num,
};
use crate::catch22::dn_outlierinclude::{dn_outlierinclude_n_001_mdrmd, dn_outlierinclude_p_001_mdrmd};
use crate::catch22::dn_spread_std::dn_spread_std;
use crate::catch22::fc_localsimple::{fc_localsimple_mean1_tauresrat, fc_localsimple_mean3_stderr};
use crate::catch22::in_automutualinfostats::in_automutualinfostats_40_gaussian_fmmi;
use crate::catch22::md_hrv::md_hrv_classic_pnn40;
use crate::catch22::pd_periodicitywang::pd_periodicitywang;
use crate::catch22::sb_binarystats::{
    bin_binarystats_diff_longsstretch0, bin_binarystats_mean_longstretch1,
};
use crate::catch22::sb_motifthree::sb_motifthree_quantile_hh;
use crate::catch22::sb_transitionmatrix::sb_transitionmatrix_3ac_sumdiagcov;
use crate::catch22::sc_fluctanal::{
    sc_fluctanal_2_dfa_50_1_2_logi_prop_r1, sc_fluctanal_2_rsrangefit_50_1_2_logi_prop_r1,
};
use crate::catch22::sp_summaries::{sp_summaries_welch_rect_area_5_1, sp_summaries_welch_rect_centroid};
use crate::parallel::catch22::{compute_catch22_parallel, extract_catch22_features_cumulative_optimized};
use super::common_types::{Catch22Result, CumulativeFeatures};

#[pyfunction]
#[pyo3(signature = (y, normalize=None, catch24=None))]
pub fn catch22_all_f(y: Vec<f64>, normalize: Option<bool>, catch24: Option<bool>) -> Catch22Result {
    let result = compute_catch22_parallel(y, normalize.unwrap_or(true), catch24.unwrap_or(false));

    Catch22Result {
        names: result.names,
        values: result.values,
    }
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn co_trev_1_num_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    co_trev_1_num(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn co_f1ecac_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    co_f1ecac(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn co_first_min_ac_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    co_first_min_ac(&y, use_normalization) as f64
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn co_histogram_ami_even_2_5_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    co_histogram_ami_even_2_5(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn md_hrv_classic_pnn40_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    md_hrv_classic_pnn40(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn sb_binarystats_diff_longsstretch0_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    bin_binarystats_diff_longsstretch0(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn sb_transitionmatrix_3ac_sumdiagcov_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    sb_transitionmatrix_3ac_sumdiagcov(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn sb_binarystats_mean_longstretch1_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    bin_binarystats_mean_longstretch1(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn pd_periodicitywang_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    pd_periodicitywang(&y, use_normalization) as f64
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn co_embed2_dist_tau_d_expfit_meandiff_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    co_embed2_dist_tau_d_expfit_meandiff(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn in_automutualinfostats_40_gaussian_fmmi_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    in_automutualinfostats_40_gaussian_fmmi(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn fc_localsimple_mean1_tauresrat_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    fc_localsimple_mean1_tauresrat(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn fc_localsimple_mean3_stderr_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    fc_localsimple_mean3_stderr(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn dn_outlierinclude_p_001_mdrmd_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    dn_outlierinclude_p_001_mdrmd(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn dn_outlierinclude_n_001_mdrmd_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    dn_outlierinclude_n_001_mdrmd(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn sp_summaries_welch_rect_area_5_1_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    sp_summaries_welch_rect_area_5_1(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn sp_summaries_welch_rect_centroid_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    sp_summaries_welch_rect_centroid(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn sb_motifthree_quantile_hh_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    sb_motifthree_quantile_hh(&y, use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn sc_fluctanal_2_dfa_50_1_2_logi_prop_r1_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    sc_fluctanal_2_dfa_50_1_2_logi_prop_r1(&y, 2, "dfa", use_normalization)
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn sc_fluctanal_2_rsrangefit_50_1_2_logi_prop_r1_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    let use_normalization = normalize.unwrap_or(true);
    sc_fluctanal_2_rsrangefit_50_1_2_logi_prop_r1(&y, 1, "rsrangefit", use_normalization)
}


#[pyfunction]
pub fn dn_spread_std_f(y: Vec<f64>) -> f64 {
    dn_spread_std(&y)
}

#[pyfunction]
#[pyo3(signature = (series, normalize=None, catch24=None, value_column_name=None))]
pub fn extract_catch22_features_cumulative_f(
    series: Vec<f64>, 
    normalize: Option<bool>, 
    catch24: Option<bool>,
    value_column_name: Option<String>
) -> CumulativeFeatures {
    let normalize = normalize.unwrap_or(true);
    let catch24 = catch24.unwrap_or(false);
    
    let result = extract_catch22_features_cumulative_optimized(
        &series, 
        normalize, 
        catch24, 
        value_column_name.as_deref()
    );

    // Extract feature names from the first row (they should be consistent)
    let feature_names: Vec<String> = if let Some(first_row) = result.data.first() {
        let mut names: Vec<String> = first_row.keys().cloned().collect();
        names.sort(); // Ensure consistent ordering
        names
    } else {
        Vec::new()
    };
    
    // Extract values in the same order as feature names
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
