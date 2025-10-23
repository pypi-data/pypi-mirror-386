use super::common::*;

// Import catchamouse16 functions
use crate::catchamouse16::sy_driftingmean::sy_driftingmean50_min;
use crate::catchamouse16::sy_slidingwindow::sy_slidingwindow;
use crate::catchamouse16::st_localextrema::st_localextrema_n100_diffmaxabsmin;
use crate::catchamouse16::ph_walker::{ph_walker_momentum_5_w_momentumzcross, ph_walker_biasprop_05_01_sw_meanabsdiff};
use crate::catchamouse16::in_automutualinfostats_diff_20_gaussian_ami8::in_automutualinfostats_diff_20_gaussian_ami8;
use crate::catchamouse16::fc_looplocalsimple::fc_looplocalsimple_mean_stderr_chn;
use crate::catchamouse16::co_translateshape::{co_translateshape_circle_35_pts_statav4_m, co_translateshape_circle_35_pts_std};
use crate::catchamouse16::co_histogramami::{co_histogram_ami_even_10_1, co_histogram_ami_even_10_3, co_histogram_ami_even_2_3};
use crate::catchamouse16::co_nonlinearautocorr::{ac_nl_035, ac_nl_036, ac_nl_112};
use crate::catchamouse16::dn_removepoints::dn_removepoints_absclose_05_ac2rat;
use crate::catchamouse16::sc_fluctanal::sc_fluctanal_2_dfa_50_2_logi_r2_se2;
use crate::catchamouse16::co_addnoise::co_addnoise_1_even_10_ami_at_10;

/// SY_DriftingMean50_Min feature
pub struct SYDriftingMean50Min;
impl FeatureCompute for SYDriftingMean50Min {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        sy_driftingmean50_min(y, _normalize)
    }
    fn name(&self) -> String {
        "SY_DriftingMean50_min".to_string()
    }
}

/// SY_SlidingWindow with std/std parameters
pub struct SYSlidingWindowStdStd {
    pub num_seg: usize,
    pub inc_move: usize,
}

impl Default for SYSlidingWindowStdStd {
    fn default() -> Self {
        Self {
            num_seg: 5,
            inc_move: 2,
        }
    }
}

impl FeatureCompute for SYSlidingWindowStdStd {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        sy_slidingwindow(y, "std", "std", self.num_seg, self.inc_move, _normalize)
    }
    fn name(&self) -> String {
        format!("SY_SlidingWindow_Std_Std_{}_{}", self.num_seg, self.inc_move)
    }
}

/// SY_SlidingWindow with mean/std parameters  
pub struct SYSlidingWindowMeanStd {
    pub num_seg: usize,
    pub inc_move: usize,
}

impl Default for SYSlidingWindowMeanStd {
    fn default() -> Self {
        Self {
            num_seg: 5,
            inc_move: 2,
        }
    }
}

impl FeatureCompute for SYSlidingWindowMeanStd {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        sy_slidingwindow(y, "mean", "std", self.num_seg, self.inc_move, _normalize)
    }
    fn name(&self) -> String {
        format!("SY_SlidingWindow_Mean_Std_{}_{}", self.num_seg, self.inc_move)
    }
}

/// ST_LocalExtrema_N100_DiffMaxAbsMin feature
pub struct STLocalExtremaN100DiffMaxAbsMin;
impl FeatureCompute for STLocalExtremaN100DiffMaxAbsMin {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        st_localextrema_n100_diffmaxabsmin(y, _normalize)
    }
    fn name(&self) -> String {
        "ST_LocalExtrema_n100_diffmaxabsmin".to_string()
    }
}

/// PH_Walker_Momentum_5_W_MomentumZCross feature
pub struct PHWalkerMomentum5WMomentumZCross;
impl FeatureCompute for PHWalkerMomentum5WMomentumZCross {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        ph_walker_momentum_5_w_momentumzcross(y, _normalize)
    }
    fn name(&self) -> String {
        "PH_Walker_momentum_5_w_momentumzcross".to_string()
    }
}

pub struct PHWalkerBiasProp0501SWMeanAbsDiff;
impl FeatureCompute for PHWalkerBiasProp0501SWMeanAbsDiff {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        ph_walker_biasprop_05_01_sw_meanabsdiff(y, _normalize)
    }
    fn name(&self) -> String {
        "PH_Walker_biasprop_05_01_sw_meanabsdiff".to_string()
    }
}

/// IN_AutoMutualInfoStats_Diff_20_Gaussian_AMI8 feature
pub struct INAutoMutualInfoStatsDiff20GaussianAMI8;
impl FeatureCompute for INAutoMutualInfoStatsDiff20GaussianAMI8 {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        in_automutualinfostats_diff_20_gaussian_ami8(y, _normalize)
    }
    fn name(&self) -> String {
        "IN_AutoMutualInfoStats_diff_20_gaussian_ami8".to_string()
    }
}

/// FC_LoopLocalSimple_Mean_StdErr_CHN feature
pub struct FCLoopLocalSimpleMeanStdErrCHN;
impl FeatureCompute for FCLoopLocalSimpleMeanStdErrCHN {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        fc_looplocalsimple_mean_stderr_chn(y, _normalize)
    }
    fn name(&self) -> String {
        "FC_LoopLocalSimple_mean_stderr_chn".to_string()
    }
}

/// CO_TranslateShape_Circle_35_Pts_StatAv4_M feature
pub struct COTranslateShapeCircle35PtsStatAv4M;
impl FeatureCompute for COTranslateShapeCircle35PtsStatAv4M {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        co_translateshape_circle_35_pts_statav4_m(y, _normalize)
    }
    fn name(&self) -> String {
        "CO_TranslateShape_Circle_35_Pts_StatAv4_M".to_string()
    }
}

/// CO_TranslateShape_Circle_35_Pts_Std feature
pub struct COTranslateShapeCircle35PtsStd;
impl FeatureCompute for COTranslateShapeCircle35PtsStd {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        co_translateshape_circle_35_pts_std(y, _normalize)
    }
    fn name(&self) -> String {
        "CO_TranslateShape_Circle_35_Pts_Std".to_string()
    }
}

/// CO_HistogramAMI_Even_10_1 feature
pub struct COHistogramAMIEven101;
impl FeatureCompute for COHistogramAMIEven101 {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        co_histogram_ami_even_10_1(y, _normalize)
    }
    fn name(&self) -> String {
        "CO_HistogramAMI_Even_10_1".to_string()
    }
}

/// CO_HistogramAMI_Even_10_3 feature
pub struct COHistogramAMIEven103;
impl FeatureCompute for COHistogramAMIEven103 {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        co_histogram_ami_even_10_3(y, _normalize)
    }
    fn name(&self) -> String {
        "CO_HistogramAMI_Even_10_3".to_string()
    }
}

/// CO_HistogramAMI_Even_2_3 feature
pub struct COHistogramAMIEven23;
impl FeatureCompute for COHistogramAMIEven23 {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        co_histogram_ami_even_2_3(y, _normalize)
    }
    fn name(&self) -> String {
        "CO_HistogramAMI_Even_2_3".to_string()
    }
}

/// AC_NL_035 feature

pub struct ACNL035;
impl FeatureCompute for ACNL035 {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        ac_nl_035(y, _normalize)
    }
    fn name(&self) -> String {
        "AC_NL_035".to_string()
    }
}

/// AC_NL_036 feature
pub struct ACNL036;
impl FeatureCompute for ACNL036 {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        ac_nl_036(y, _normalize)
    }
    fn name(&self) -> String {
        "AC_NL_036".to_string()
    }
}

/// AC_NL_112 feature
pub struct ACNL112;
impl FeatureCompute for ACNL112 {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        ac_nl_112(y, _normalize)
    }
    fn name(&self) -> String {
        "AC_NL_112".to_string()
    }
}

/// DN_RemovePoints_AbsClose_05_AC2Rat feature
pub struct DNRemovePointsAbsClose05AC2Rat;
impl FeatureCompute for DNRemovePointsAbsClose05AC2Rat {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        dn_removepoints_absclose_05_ac2rat(y, _normalize)
    }
    fn name(&self) -> String {
        "DN_RemovePoints_AbsClose_05_AC2Rat".to_string()
    }
}

/// SC_FluctAnal_2_DFA_50_2_Logi_R2_SE2 feature

pub struct SCFluctAnal2Dfa502LogiR2Se2;
impl FeatureCompute for SCFluctAnal2Dfa502LogiR2Se2 {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        sc_fluctanal_2_dfa_50_2_logi_r2_se2(y, _normalize)
    }
    fn name(&self) -> String {
        "SC_FluctAnal_2_DFA_50_2_Logi_R2_SE2".to_string()
    }
}

/// CO_AddNoise_1_Even_10_AMI_At_10 feature
pub struct COAddNoise1Even10AmiAt10;
impl FeatureCompute for COAddNoise1Even10AmiAt10 {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        co_addnoise_1_even_10_ami_at_10(y, _normalize)
    }
    fn name(&self) -> String {
        "CO_AddNoise_1_Even_10_AMI_At_10".to_string()
    }
}

pub type Catchamouse16Output = FeatureOutput;

/// Compute all Catchamouse16 features in parallel
pub fn compute_catchamouse16_parallel(y: Vec<f64>, normalize: bool) -> Catchamouse16Output {
    let features: Vec<Box<dyn FeatureCompute>> = vec![
        Box::new(SYDriftingMean50Min),
        Box::new(SYSlidingWindowStdStd::default()),
        Box::new(SYSlidingWindowMeanStd::default()),
        Box::new(STLocalExtremaN100DiffMaxAbsMin),
        Box::new(PHWalkerMomentum5WMomentumZCross),
        Box::new(PHWalkerBiasProp0501SWMeanAbsDiff),
        Box::new(INAutoMutualInfoStatsDiff20GaussianAMI8),
        Box::new(FCLoopLocalSimpleMeanStdErrCHN),
        Box::new(COTranslateShapeCircle35PtsStatAv4M),
        Box::new(COTranslateShapeCircle35PtsStd),
        Box::new(COHistogramAMIEven101),
        Box::new(COHistogramAMIEven103),
        Box::new(COHistogramAMIEven23),
        Box::new(ACNL035),
        Box::new(ACNL036),
        Box::new(ACNL112),
        Box::new(DNRemovePointsAbsClose05AC2Rat),
        Box::new(SCFluctAnal2Dfa502LogiR2Se2),
        Box::new(COAddNoise1Even10AmiAt10),
    ];

    compute_features_parallel_dyn(y, normalize, features)
}

/// Extract Catchamouse16 features cumulatively
pub fn extract_catchamouse16_features_cumulative_optimized(
    series: &[f64],
    normalize: bool,
    value_column_name: Option<&str>,
) -> CumulativeResult {
    extract_features_cumulative_optimized(
        series,
        normalize,
        value_column_name,
        |data, norm| compute_catchamouse16_parallel(data.to_vec(), norm),
    )
}