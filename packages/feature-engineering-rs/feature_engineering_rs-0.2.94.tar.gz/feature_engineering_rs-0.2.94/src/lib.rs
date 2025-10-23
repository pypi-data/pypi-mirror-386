use pyo3::prelude::*;

// Core modules
pub mod helpers;
pub mod catch22;
pub mod tsfeatures;
pub mod parallel;
pub mod catchamouse16;
pub mod hctsa;
pub mod macros;

// Python bindings module
pub mod python_bindings;

// Re-export all Python bindings for easy access
use python_bindings::*;

#[pymodule]
fn feature_engineering_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    
    /////////////////////////////////////////////////////////////
    // Catch22 + DNMean + DNSpreadStd --------------------------
    m.add_class::<Catch22Result>()?;
    m.add_class::<CumulativeFeatures>()?;
    m.add_function(wrap_pyfunction!(catch22_all_f, m)?)?;
    m.add_function(wrap_pyfunction!(co_trev_1_num_f, m)?)?;
    m.add_function(wrap_pyfunction!(co_f1ecac_f, m)?)?;
    m.add_function(wrap_pyfunction!(co_first_min_ac_f, m)?)?;
    m.add_function(wrap_pyfunction!(co_histogram_ami_even_2_5_f, m)?)?;
    m.add_function(wrap_pyfunction!(md_hrv_classic_pnn40_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_spread_std_f, m)?)?;
    m.add_function(wrap_pyfunction!(sb_binarystats_diff_longsstretch0_f, m)?)?;
    m.add_function(wrap_pyfunction!(sb_binarystats_mean_longstretch1_f, m)?)?;
    m.add_function(wrap_pyfunction!(sb_transitionmatrix_3ac_sumdiagcov_f, m)?)?;
    m.add_function(wrap_pyfunction!(pd_periodicitywang_f, m)?)?;
    m.add_function(wrap_pyfunction!(co_embed2_dist_tau_d_expfit_meandiff_f,m)?)?;
    m.add_function(wrap_pyfunction!(in_automutualinfostats_40_gaussian_fmmi_f,m)?)?;
    m.add_function(wrap_pyfunction!(fc_localsimple_mean1_tauresrat_f, m)?)?;
    m.add_function(wrap_pyfunction!(fc_localsimple_mean3_stderr_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_outlierinclude_p_001_mdrmd_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_outlierinclude_n_001_mdrmd_f, m)?)?;
    m.add_function(wrap_pyfunction!(sp_summaries_welch_rect_area_5_1_f, m)?)?;
    m.add_function(wrap_pyfunction!(sp_summaries_welch_rect_centroid_f, m)?)?;
    m.add_function(wrap_pyfunction!(sb_motifthree_quantile_hh_f, m)?)?;
    m.add_function(wrap_pyfunction!(sc_fluctanal_2_dfa_50_1_2_logi_prop_r1_f,m)?)?;
    m.add_function(wrap_pyfunction!(sc_fluctanal_2_rsrangefit_50_1_2_logi_prop_r1_f,m)?)?;
    m.add_function(wrap_pyfunction!(extract_catch22_features_cumulative_f, m)?)?;

    /////////////////////////////////////////////////////////////
    // Catchamouse16 --------------------------------------------
    m.add_function(wrap_pyfunction!(sy_driftingmean50_min_f, m)?)?;
    m.add_function(wrap_pyfunction!(sy_slidingwindow_f, m)?)?;
    m.add_function(wrap_pyfunction!(st_localextrema_n100_diffmaxabsmin_f, m)?)?;
    m.add_function(wrap_pyfunction!(ph_walker_momentum_5_w_momentumzcross_f, m)?)?;
    m.add_function(wrap_pyfunction!(ph_walker_biasprop_05_01_sw_meanabsdiff_f, m)?)?;
    m.add_function(wrap_pyfunction!(in_automutualinfostats_diff_20_gaussian_ami8_f, m)?)?;
    m.add_function(wrap_pyfunction!(fc_looplocalsimple_mean_stderr_chn_f, m)?)?;
    m.add_function(wrap_pyfunction!(co_translateshape_circle_35_pts_statav4_m_f, m)?)?;
    m.add_function(wrap_pyfunction!(co_translateshape_circle_35_pts_std_f, m)?)?;
    m.add_function(wrap_pyfunction!(co_histogram_ami_even_10_1_f, m)?)?;
    m.add_function(wrap_pyfunction!(co_histogram_ami_even_10_3_f, m)?)?;
    m.add_function(wrap_pyfunction!(co_histogram_ami_even_2_3_f, m)?)?;
    m.add_function(wrap_pyfunction!(co_addnoise_1_even_10_ami_at_10_f, m)?)?;
    m.add_function(wrap_pyfunction!(ac_nl_035_f, m)?)?;
    m.add_function(wrap_pyfunction!(ac_nl_036_f, m)?)?;
    m.add_function(wrap_pyfunction!(ac_nl_112_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_removepoints_absclose_05_ac2rat_f, m)?)?;
    m.add_function(wrap_pyfunction!(sc_fluctanal_2_dfa_50_2_logi_r2_se2_f, m)?)?;
    
    /////////////////////////////////////////////////////////////
    // TSFeatures ------------------------------------------------
    m.add_class::<TSFeaturesResult>()?;
    m.add_function(wrap_pyfunction!(crossing_points_f, m)?)?;
    m.add_function(wrap_pyfunction!(entropy_f, m)?)?;
    m.add_function(wrap_pyfunction!(flat_spots_f, m)?)?;
    m.add_function(wrap_pyfunction!(lumpiness_f, m)?)?;
    m.add_function(wrap_pyfunction!(stability_f, m)?)?;
    m.add_function(wrap_pyfunction!(hurst_f, m)?)?;
    m.add_function(wrap_pyfunction!(nonlinearity_f, m)?)?;
    m.add_function(wrap_pyfunction!(pacf_features_f, m)?)?;
    m.add_function(wrap_pyfunction!(unitroot_kpss_f, m)?)?;
    m.add_function(wrap_pyfunction!(unitroot_pp_f, m)?)?;
    m.add_function(wrap_pyfunction!(arch_stat_f, m)?)?;
    m.add_function(wrap_pyfunction!(tsfeatures_all_f, m)?)?;
    m.add_function(wrap_pyfunction!(extract_tsfeatures_cumulative_f, m)?)?;

    /////////////////////////////////////////////////////////////
    // HCTSA ----------------------------------------------------
    // DN_Mean --------------------------------------------------
    m.add_function(wrap_pyfunction!(dn_mean_arithmetic_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_median_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_harmonic_mean_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_geometric_mean_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_rms_mean_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_iqm_mean_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_midhinge_mean_f, m)?)?;
    // DN_MinMax --------------------------------------------------
    // m.add_function(wrap_pyfunction!(dn_minmax_f, m)?)?;
    // DN_HistogramMode ------------------------------------------
    m.add_function(wrap_pyfunction!(dn_histogrammode_5_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_histogrammode_10_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_histogrammode_12_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_histogrammode_21_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_histogrammode_52_f, m)?)?;
    // DN_TrimmedMean --------------------------------------------
    m.add_function(wrap_pyfunction!(dn_trimmed_mean_1_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_trimmed_mean_5_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_trimmed_mean_10_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_trimmed_mean_25_f, m)?)?;
    m.add_function(wrap_pyfunction!(dn_trimmed_mean_50_f, m)?)?;

    // HCTSA --------------------------------------------------
    m.add_function(wrap_pyfunction!(compute_hctsa_parallel_f, m)?)?;

    // Combined Features
    m.add_class::<CombinedResult>()?;
    m.add_function(wrap_pyfunction!(combined_all_f, m)?)?;
    m.add_function(wrap_pyfunction!(extract_combined_features_cumulative_f, m)?)?;
    Ok(())
}