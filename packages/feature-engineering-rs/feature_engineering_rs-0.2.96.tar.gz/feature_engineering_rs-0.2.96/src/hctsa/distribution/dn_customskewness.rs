use crate::{define_feature, feature_registry};
use crate::helpers::common::{mean_f, median_f, stdev_f, quantile_f};

fn dn_customskewness(y: &[f64], whatskew: &str) -> f64 {

    match whatskew {
        "pearson" => {
            (3.0 * mean_f(y, Some("arithmetic")) - median_f(y, Some(false))) / stdev_f(y, 1)
        },
        "bowley" => {
            let qs_1 = quantile_f(y, 0.25);
            let qs_2 = quantile_f(y, 0.5);
            let qs_3 = quantile_f(y, 0.75);
            (qs_3 + qs_1 - 2.0 * qs_2) / (qs_3 - qs_1)
        },
        _ => {
            return f64::NAN;
        }
    }
}

pub fn dn_customskewness_pearson(y: &[f64]) -> f64 {
    dn_customskewness(y, "pearson")
}

pub fn dn_customskewness_bowley(y: &[f64]) -> f64 {
    dn_customskewness(y, "bowley")
}

// FEATURE DEFINITIONS
define_feature!(
    DNCustomSkewnessPearson,
    dn_customskewness_pearson,
    "skewness_pearson"
);

define_feature!(
    DNCustomSkewnessBowley,
    dn_customskewness_bowley,
    "skewness_bowley"
);

// FEATURE REGISTRY
feature_registry!(
    DNCustomSkewnessPearson,
    DNCustomSkewnessBowley,
);