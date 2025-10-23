use crate::{define_feature, feature_registry};
use crate::helpers::common::{mean_f, stdev_f, median_f, iqr_f};

fn dn_withinp(y: &[f64], p: f64, mean_or_median: Option<&str>) -> f64 {
    let n = y.len() as f64;
    
    let (mu, sig) = match mean_or_median.unwrap_or("mean") {
        "mean" => {
            let mu = mean_f(y, Some("arithmetic"));
            let sig = stdev_f(y, 0);
            (mu, sig)
        },
        "median" => {
            let mu = median_f(y, Some(false));
            let sig = 1.35 * iqr_f(y); // rescaled IQR
            (mu, sig)
        },
        _ => panic!("Unknown setting: {}", mean_or_median.unwrap())
    };
    
    let withinp = y.iter()
        .filter(|&&x| x >= mu - p * sig && x <= mu + p * sig)
        .count() as f64 / n;
    
    withinp
}

// DN_Withinp_Mean
pub fn dn_withinp_mean_05(y: &[f64]) -> f64 {
    dn_withinp(y, 0.5, Some("mean"))
}

pub fn dn_withinp_mean_10(y: &[f64]) -> f64 {
    dn_withinp(y, 1.0, Some("mean"))
}

pub fn dn_withinp_mean_15(y: &[f64]) -> f64 {
    dn_withinp(y, 1.5, Some("mean"))
}

pub fn dn_withinp_mean_20(y: &[f64]) -> f64 {
    dn_withinp(y, 2.0, Some("mean"))
}


pub fn dn_withinp_mean_25(y: &[f64]) -> f64 {
    dn_withinp(y, 2.5, Some("mean"))
}

pub fn dn_withinp_mean_30(y: &[f64]) -> f64 {
    dn_withinp(y, 3.0, Some("mean"))
}

// DN_Withinp_Median
pub fn dn_withinp_median_05(y: &[f64]) -> f64 {
    dn_withinp(y, 0.5, Some("median"))
}

pub fn dn_withinp_median_10(y: &[f64]) -> f64 {
    dn_withinp(y, 1.0, Some("median"))
}

pub fn dn_withinp_median_15(y: &[f64]) -> f64 {
    dn_withinp(y, 1.5, Some("median"))
}

pub fn dn_withinp_median_20(y: &[f64]) -> f64 {
    dn_withinp(y, 2.0, Some("median"))
}

pub fn dn_withinp_median_25(y: &[f64]) -> f64 {
    dn_withinp(y, 2.5, Some("median"))
}

pub fn dn_withinp_median_30(y: &[f64]) -> f64 {
    dn_withinp(y, 3.0, Some("median"))
}

// FEATURE DEFINITIONS
define_feature!(
    DNWithinpMean05,
    dn_withinp_mean_05,
    "DN_Withinp_05"
);

define_feature!(
    DNWithinpMean10,
    dn_withinp_mean_10,
    "DN_Withinp_10"
);

define_feature!(
    DNWithinpMean15,
    dn_withinp_mean_15,
    "DN_Withinp_15"
);

define_feature!(
    DNWithinpMean20,
    dn_withinp_mean_20,
    "DN_Withinp_20"
);

define_feature!(
    DNWithinpMean25,
    dn_withinp_mean_25,
    "DN_Withinp_25"
);

define_feature!(
    DNWithinpMean30,
    dn_withinp_mean_30,
    "DN_Withinp_30"
);

define_feature!(
    DNWithinpMedian05,
    dn_withinp_median_05,
    "DN_Withinp_median_05"
);

define_feature!(
    DNWithinpMedian10,
    dn_withinp_median_10,
    "DN_Withinp_median_10"
);

define_feature!(
    DNWithinpMedian15,
    dn_withinp_median_15,
    "DN_Withinp_median_15"
);

define_feature!(
    DNWithinpMedian20,
    dn_withinp_median_20,
    "DN_Withinp_median_20"
);

define_feature!(
    DNWithinpMedian25,
    dn_withinp_median_25,
    "DN_Withinp_median_25"
);

define_feature!(
    DNWithinpMedian30,
    dn_withinp_median_30,
    "DN_Withinp_median_30"
);

// FEATURE REGISTRY
feature_registry!(
    DNWithinpMean05,
    DNWithinpMean10,
    DNWithinpMean15,
    DNWithinpMean20,
    DNWithinpMean25,
    DNWithinpMean30,
    DNWithinpMedian05,
    DNWithinpMedian10,
    DNWithinpMedian15,
    DNWithinpMedian20,
    DNWithinpMedian25,
    DNWithinpMedian30,
);

