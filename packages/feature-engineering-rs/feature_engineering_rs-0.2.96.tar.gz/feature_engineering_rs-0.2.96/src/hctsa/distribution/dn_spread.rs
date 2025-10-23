use crate::{define_feature, feature_registry};
use crate::helpers::common::{stdev_f, iqr_f, mad_f};

fn dn_spread(y: &[f64], spread_measure: &str) -> f64 {
    
    match spread_measure {
        "std" => stdev_f(y, 1),
        "iqr" => iqr_f(y),
        "mad_mean" => mad_f(y, Some("mean")),
        "mad_median" => mad_f(y, Some("median")),
        _ => panic!("Unknown spread measure: {}", spread_measure)
    }
}

pub fn dn_spread_std(y: &[f64]) -> f64 {
    dn_spread(y, "std")
}

pub fn dn_spread_iqr(y: &[f64]) -> f64 {
    dn_spread(y, "iqr")
}

pub fn dn_spread_mad_mean(y: &[f64]) -> f64 {
    dn_spread(y, "mad_mean")
}

pub fn dn_spread_mad_median(y: &[f64]) -> f64 {
    dn_spread(y, "mad_median")
}

// FEATURE DEFINITIONS
define_feature!(
    DNSpread,
    dn_spread_std,
    "standard_deviation"
);

define_feature!(
    DNSpreadMADMean,
    dn_spread_mad_mean,
    "mean_absolute_deviation"
);


define_feature!(
    DNIQR,
    dn_spread_iqr,
    "interquartile_range"
);

define_feature!(
    DNSpreadMADMedian,
    dn_spread_mad_median,
    "median_absolute_deviation"
);

// FEATURE REGISTRY
feature_registry!(
    DNSpread,
    DNSpreadMADMean,
    DNIQR,
    DNSpreadMADMedian,
);

