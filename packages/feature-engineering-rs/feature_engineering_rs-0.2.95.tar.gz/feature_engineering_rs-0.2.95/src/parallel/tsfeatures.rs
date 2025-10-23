use super::common::*;
use std::collections::HashMap;

// Import TSFeatures
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

/// TSFeatures implementations
pub struct CrossingPoints;
impl FeatureCompute for CrossingPoints {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        crossing_points(y)
    }
    fn name(&self) -> String {
        "crossing_points".to_string()
    }
}

pub struct Entropy;
impl FeatureCompute for Entropy {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        entropy(y)
    }
    fn name(&self) -> String {
        "entropy".to_string()
    }
}

pub struct FlatSpots;
impl FeatureCompute for FlatSpots {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        flat_spots(y)
    }
    fn name(&self) -> String {
        "flat_spots".to_string()
    }
}

pub struct Lumpiness{
    pub freq: Option<usize>
}
impl FeatureCompute for Lumpiness {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        lumpiness(y, self.freq) // Using default frequency
    }
    fn name(&self) -> String {
        "lumpiness".to_string()
    }
}

pub struct Stability{
    pub freq: Option<usize>
}
impl FeatureCompute for Stability {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        stability(y, self.freq) 
    }
    fn name(&self) -> String {
        "stability".to_string()
    }
}

pub struct Hurst;
impl FeatureCompute for Hurst {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        hurst(y)
    }
    fn name(&self) -> String {
        "hurst".to_string()
    }
}

pub struct Nonlinearity;
impl FeatureCompute for Nonlinearity {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        nonlinearity(y.to_vec())
    }
    fn name(&self) -> String {
        "nonlinearity".to_string()
    }
}

pub struct XPacf5 {
    pub freq: Option<usize>,
}
impl FeatureCompute for XPacf5 {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        pacf_features(y.to_vec(), self.freq).get("x_pacf5").copied().unwrap_or(f64::NAN)
    }
    fn name(&self) -> String {
        "x_pacf5".to_string()
    }
}

pub struct Diff1XPacf5 {
    pub freq: Option<usize>,
}
impl FeatureCompute for Diff1XPacf5 {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        pacf_features(y.to_vec(), self.freq).get("diff1x_pacf5").copied().unwrap_or(f64::NAN)
    }
    fn name(&self) -> String {
        "diff1x_pacf5".to_string()
    }
}

pub struct Diff2XPacf5 {
    pub freq: Option<usize>,
}
impl FeatureCompute for Diff2XPacf5 {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        pacf_features(y.to_vec(), self.freq).get("diff2x_pacf5").copied().unwrap_or(f64::NAN)
    }
    fn name(&self) -> String {
        "diff2x_pacf5".to_string()
    }
}


pub struct SeasPacf {
    pub freq: Option<usize>,
}
impl FeatureCompute for SeasPacf {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        pacf_features(y.to_vec(), self.freq).get("seas_pacf").copied().unwrap_or(f64::NAN)
    }
    fn name(&self) -> String {
        "seas_pacf".to_string()
    }
}

pub struct UnitrootKpss;
impl FeatureCompute for UnitrootKpss {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        unitroot_kpss(y, 1)
    }
    fn name(&self) -> String {
        "unitroot_kpss".to_string()
    }
}

pub struct UnitrootPp;
impl FeatureCompute for UnitrootPp {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        unitroot_pp(y, 1)
    }
    fn name(&self) -> String {
        "unitroot_pp".to_string()
    }
}

pub struct ArchStat {
    pub lags: usize,
    pub demean: bool,
}
impl FeatureCompute for ArchStat {
    fn compute(&self, y: &[f64], _normalize: bool) -> f64 {
        arch_stat(y, self.lags, self.demean)
    }
    fn name(&self) -> String {
        "arch_lm".to_string()
    }
}

pub type TSFeaturesOutput = FeatureOutput;

/// Compute all TSFeatures in parallel
pub fn compute_tsfeatures_parallel(y: Vec<f64>, normalize: bool, freq: Option<usize>, lags: usize, demean: bool) -> TSFeaturesOutput {
    
    let mut features: Vec<Box<dyn FeatureCompute>> = vec![
        Box::new(CrossingPoints),
        Box::new(FlatSpots),
        Box::new(Lumpiness { freq: freq }),
        Box::new(Stability { freq: freq }),
        Box::new(XPacf5 { freq: freq }),
        Box::new(Diff1XPacf5 { freq: freq }),
        Box::new(Diff2XPacf5 { freq: freq }),
        Box::new(SeasPacf { freq: freq }),  
        Box::new(Hurst),
        Box::new(UnitrootPp),
        Box::new(UnitrootKpss),
        Box::new(Nonlinearity),
        Box::new(ArchStat { lags: lags, demean: demean }),
        Box::new(Entropy),
    ];

    // Only add SeasPacf if freq > 1
    if let Some(f) = freq {
        if f > 1 {
            features.push(Box::new(SeasPacf { freq: freq }));
        }
    }

    compute_features_parallel_dyn(y, normalize, features)
}

/// Extract TSFeatures cumulatively
pub fn extract_tsfeatures_cumulative_optimized(
    series: &[f64],
    normalize: bool,
    freq: Option<usize>,
    lags: usize,
    demean: bool,
    value_column_name: Option<&str>,
) -> CumulativeResult {
    extract_features_cumulative_optimized(
        series,
        normalize,
        value_column_name,
        |data, norm| compute_tsfeatures_parallel(data.to_vec(), norm, freq, lags, demean),
    )
}