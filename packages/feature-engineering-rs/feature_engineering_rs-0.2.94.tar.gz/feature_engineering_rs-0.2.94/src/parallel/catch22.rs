use rayon::prelude::*;
use std::sync::Arc;
use std::collections::HashMap;
use super::common::*;

use crate::catch22::co_auto_corr::co_embed2_dist_tau_d_expfit_meandiff;
use crate::catch22::co_auto_corr::{
    co_f1ecac, co_first_min_ac, co_histogram_ami_even_2_5, co_trev_1_num,
};
use crate::catch22::dn_outlierinclude::{
    dn_outlierinclude_n_001_mdrmd, dn_outlierinclude_p_001_mdrmd,
};
use crate::catch22::dn_spread_std::dn_spread_std;
use crate::catch22::fc_localsimple::{
    fc_localsimple_mean1_tauresrat, fc_localsimple_mean3_stderr,
};
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
use crate::catch22::sp_summaries::{
    sp_summaries_welch_rect_area_5_1, sp_summaries_welch_rect_centroid,
};

#[derive(Debug, Clone)]
pub struct Catch22Output {
    pub names: Vec<String>,
    pub values: Vec<f64>,
}

#[derive(Debug, Clone)]
pub struct CumulativeResult {
    pub data: Vec<HashMap<String, f64>>,
}

pub struct COF1ecac;
impl FeatureCompute for COF1ecac {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        co_f1ecac(y, normalize)
    }
    fn name(&self) -> String {
        "CO_f1ecac".to_string()
    }
}

pub struct COFirstMinAC;
impl FeatureCompute for COFirstMinAC {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        co_first_min_ac(y, normalize) as f64
    }
    fn name(&self) -> String {
        "CO_FirstMin_ac".to_string()
    }
}

pub struct COHistogramAMIEven25;
impl FeatureCompute for COHistogramAMIEven25 {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        co_histogram_ami_even_2_5(y, normalize)
    }
    fn name(&self) -> String {
        "CO_HistogramAMI_even_2_5".to_string()
    }
}

pub struct COTrev1Num;
impl FeatureCompute for COTrev1Num {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        co_trev_1_num(y, normalize)
    }
    fn name(&self) -> String {
        "CO_trev_1_num".to_string()
    }
}

pub struct MDHrvClassicPnn40;
impl FeatureCompute for MDHrvClassicPnn40 {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        md_hrv_classic_pnn40(y, normalize)
    }
    fn name(&self) -> String {
        "MD_hrv_classic_pnn40".to_string()
    }
}

pub struct DNSpreadStd;
impl FeatureCompute for DNSpreadStd {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        dn_spread_std(y)
    }
    fn name(&self) -> String {
        "DN_Spread_Std".to_string()
    }
}

pub struct SBBinaryStatsMeanLongstretch1;
impl FeatureCompute for SBBinaryStatsMeanLongstretch1 {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        bin_binarystats_mean_longstretch1(y, _normalize)
    }
    fn name(&self) -> String {
        "SB_BinaryStats_mean_longstretch1".to_string()
    }
}

pub struct SBBinaryStatsDiffLongsstretch0;
impl FeatureCompute for SBBinaryStatsDiffLongsstretch0 {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        bin_binarystats_diff_longsstretch0(y, _normalize)
    }
    fn name(&self) -> String {
        "SB_BinaryStats_diff_longstretch0".to_string()
    }
}

pub struct SBTransitionMatrix3acSumdiagcov;
impl FeatureCompute for SBTransitionMatrix3acSumdiagcov {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        sb_transitionmatrix_3ac_sumdiagcov(y, normalize)
    }
    fn name(&self) -> String {
        "SB_TransitionMatrix_3ac_sumdiagcov".to_string()
    }
}

pub struct PDPeriodicityWangTh001;
impl FeatureCompute for PDPeriodicityWangTh001 {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        pd_periodicitywang(y, normalize) as f64
    }
    fn name(&self) -> String {
        "PD_PeriodicityWang_th0_01".to_string()
    }
}

pub struct COEmbed2DistTauDExpfitMeandiff;
impl FeatureCompute for COEmbed2DistTauDExpfitMeandiff {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        co_embed2_dist_tau_d_expfit_meandiff(y, normalize)
    }
    fn name(&self) -> String {
        "CO_Embed2_Dist_tau_d_expfit_meandiff".to_string()
    }
}

pub struct INAutoMutualInfoStats40GaussianFmmi;
impl FeatureCompute for INAutoMutualInfoStats40GaussianFmmi {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        in_automutualinfostats_40_gaussian_fmmi(y, normalize)
    }
    fn name(&self) -> String {
        "IN_AutoMutualInfoStats_40_gaussian_fmmi".to_string()
    }
}

pub struct FCLocalSimpleMean1StderrTauresrat;
impl FeatureCompute for FCLocalSimpleMean1StderrTauresrat {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        fc_localsimple_mean1_tauresrat(y, _normalize)
    }
    fn name(&self) -> String {
        "FC_LocalSimple_mean1_tauresrat".to_string()
    }
}

pub struct FCLocalSimpleMean3Stderr;
impl FeatureCompute for FCLocalSimpleMean3Stderr {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        fc_localsimple_mean3_stderr(y, _normalize)
    }
    fn name(&self) -> String {
        "FC_LocalSimple_mean3_stderr".to_string()
    }
}

pub struct DNOutlierIncludeNP001Mdrmd;
impl FeatureCompute for DNOutlierIncludeNP001Mdrmd {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        dn_outlierinclude_n_001_mdrmd(y, normalize)
    }
    fn name(&self) -> String {
        "DN_OutlierInclude_n_001_mdrmd".to_string()
    }
}

pub struct DNOutlierIncludeP001Mdrmd;
impl FeatureCompute for DNOutlierIncludeP001Mdrmd {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        dn_outlierinclude_p_001_mdrmd(y, normalize)
    }
    fn name(&self) -> String {
        "DN_OutlierInclude_p_001_mdrmd".to_string()
    }
}

pub struct SPSummariesWelchRectArea51;
impl FeatureCompute for SPSummariesWelchRectArea51 {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        sp_summaries_welch_rect_area_5_1(y, normalize)
    }
    fn name(&self) -> String {
        "SP_Summaries_welch_rect_area_5_1".to_string()
    }
}

pub struct SBMotifThreeQuantileHH;
impl FeatureCompute for SBMotifThreeQuantileHH {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        sb_motifthree_quantile_hh(y, normalize)
    }
    fn name(&self) -> String {
        "SB_MotifThree_quantile_hh".to_string()
    }
}
pub struct SPSummariesWelchRectCentroid;
impl FeatureCompute for SPSummariesWelchRectCentroid {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        sp_summaries_welch_rect_centroid(y, normalize)
    }
    fn name(&self) -> String {
        "SP_Summaries_welch_rect_centroid".to_string()
    }
}

pub struct SCFluctanal2Dfa5012LogiPropR1;
impl FeatureCompute for SCFluctanal2Dfa5012LogiPropR1 {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        sc_fluctanal_2_dfa_50_1_2_logi_prop_r1(y, 2, "dfa", normalize)
    }
    fn name(&self) -> String {
        "SC_FluctAnal_2_dfa_50_1_2_logi_prop_r1".to_string()
    }
}

pub struct SCFluctanal2Rsrangefit5012LogiPropR1;
impl FeatureCompute for SCFluctanal2Rsrangefit5012LogiPropR1 {
    fn compute(&self, y: &[f64], normalize: bool) -> f64 {
        sc_fluctanal_2_rsrangefit_50_1_2_logi_prop_r1(y, 1, "rsrangefit", normalize)
    }
    fn name(&self) -> String {
        "SC_FluctAnal_2_rsrangefit_50_1_logi_prop_r1".to_string()
    }
}

/// Compute all catch22 features in parallel
pub fn compute_catch22_parallel(y: Vec<f64>, normalize: bool, catch24: bool) -> Catch22Output {
    // Create Arc to share the data between threads without cloning
    let y_arc = Arc::new(y);

    // Create a vector of feature computers
    let mut features: Vec<Box<dyn FeatureCompute>> = vec![
        Box::new(COF1ecac),
        Box::new(COFirstMinAC),
        Box::new(COHistogramAMIEven25),
        Box::new(COTrev1Num),
        Box::new(MDHrvClassicPnn40),
        Box::new(SBBinaryStatsMeanLongstretch1),
        Box::new(SBTransitionMatrix3acSumdiagcov),
        Box::new(PDPeriodicityWangTh001),
        Box::new(COEmbed2DistTauDExpfitMeandiff),
        Box::new(INAutoMutualInfoStats40GaussianFmmi),
        Box::new(FCLocalSimpleMean1StderrTauresrat),
        Box::new(DNOutlierIncludeP001Mdrmd),
        Box::new(DNOutlierIncludeNP001Mdrmd),
        Box::new(SPSummariesWelchRectArea51),
        Box::new(SBBinaryStatsDiffLongsstretch0),
        Box::new(SBMotifThreeQuantileHH),
        Box::new(SCFluctanal2Rsrangefit5012LogiPropR1),
        Box::new(SCFluctanal2Dfa5012LogiPropR1),
        Box::new(SPSummariesWelchRectCentroid),
        Box::new(FCLocalSimpleMean3Stderr),
    ];

    if catch24 {
        features.push(Box::new(DNSpreadStd));
    }

    // Parallel computation using Rayon
    let results: Vec<(String, f64)> = features
        .into_par_iter()
        .map(|feature| {
            let name = feature.name();
            let value = feature.compute(&y_arc, normalize);
            (name, value)
        })
        .collect();

    // Separate names and values
    let (names, values): (Vec<String>, Vec<f64>) = results.into_iter().unzip();

    Catch22Output { names, values }
}

// Optimized version that processes all windows in parallel
pub fn extract_catch22_features_cumulative_optimized(
    series: &[f64],
    normalize: bool,
    catch24: bool,
    value_column_name: Option<&str>,
) -> CumulativeResult {
    let series_len = series.len();
    let column_name = value_column_name.unwrap_or("VALUE");
    
    // Pre-allocate result vector
    let mut results = vec![HashMap::new(); series_len];
    
    // Process all cumulative windows in parallel
    results
        .par_iter_mut()
        .enumerate()
        .for_each(|(end_idx, result_map)| {
            // Extract cumulative data up to this index
            let window_data = &series[..=end_idx];
            
            // Compute features for this window
            let features = compute_catch22_parallel(window_data.to_vec(), normalize, catch24);
            
            // Store original value with configurable column name
            result_map.insert(column_name.to_string(), series[end_idx]);
            
            // Store all catch22 features
            for (name, value) in features.names.iter().zip(features.values.iter()) {
                result_map.insert(name.clone(), *value);
            }
        });
    
    CumulativeResult { data: results }
}