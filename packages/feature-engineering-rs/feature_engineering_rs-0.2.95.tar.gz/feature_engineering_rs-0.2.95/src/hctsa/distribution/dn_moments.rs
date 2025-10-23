use crate::{define_feature, feature_registry};
use crate::helpers::common::{mean_f, stdev_f};

fn moments_f(y: &[f64], k: f64) -> f64 {

    let x_bar = mean_f(&y, Some("arithmetic"));
    let n = y.len();

    let mut moment = 0.0;
    
    for i in 0..n {
        moment += (y[i] - x_bar).powf(k);
    }

    let raw_moment = moment / n as f64;
    raw_moment / stdev_f(&y, 1) as f64
}

pub fn dn_moments_3(y: &[f64]) -> f64 {
    moments_f(y, 3.0)
}

pub fn dn_moments_4(y: &[f64]) -> f64 {
    moments_f(y, 4.0)
}

pub fn dn_moments_5(y: &[f64]) -> f64 {
    moments_f(y, 5.0)
}

pub fn dn_moments_6(y: &[f64]) -> f64 {
    moments_f(y, 6.0)
}

pub fn dn_moments_7(y: &[f64]) -> f64 {
    moments_f(y, 7.0)
}

pub fn dn_moments_8(y: &[f64]) -> f64 {
    moments_f(y, 8.0)
}

pub fn dn_moments_9(y: &[f64]) -> f64 {
    moments_f(y, 9.0)
}

pub fn dn_moments_10(y: &[f64]) -> f64 {
    moments_f(y, 10.0)
}

pub fn dn_moments_11(y: &[f64]) -> f64 {
    moments_f(y, 11.0)
}

// FEATURE DEFINITIONS
define_feature!(
    DNMoments3,
    dn_moments_3,
    "DN_Moments_3"
);

define_feature!(
    DNMoments4,
    dn_moments_4,
    "DN_Moments_4"
);

define_feature!(
    DNMoments5,
    dn_moments_5,
    "DN_Moments_5"
);

define_feature!(
    DNMoments6,
    dn_moments_6,
    "DN_Moments_6"
);

define_feature!(
    DNMoments7,
    dn_moments_7,
    "DN_Moments_7"
);

define_feature!(
    DNMoments8,
    dn_moments_8,
    "DN_Moments_8"
);

define_feature!(
    DNMoments9,
    dn_moments_9,
    "DN_Moments_9"
);

define_feature!(
    DNMoments10,
    dn_moments_10,
    "DN_Moments_10"
);

define_feature!(
    DNMoments11,
    dn_moments_11,
    "DN_Moments_11"
);

// FEATURE REGISTRY
feature_registry!(
    DNMoments3,
    DNMoments4,
    DNMoments5,
    DNMoments6,
    DNMoments7,
    DNMoments8,
    DNMoments9,
    DNMoments10,
    DNMoments11,
);

