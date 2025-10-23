use crate::{define_feature, feature_registry};
use crate::helpers::common::quantile_f;

fn dn_quantile(y: &[f64], p: f64) -> f64 {
    quantile_f(y, p)
}

pub fn dn_quantile_1(y: &[f64]) -> f64 {
    dn_quantile(y, 0.01)
}

pub fn dn_quantile_2(y: &[f64]) -> f64 {
    dn_quantile(y, 0.02)
}

pub fn dn_quantile_3(y: &[f64]) -> f64 {
    dn_quantile(y, 0.03)
}

pub fn dn_quantile_4(y: &[f64]) -> f64 {
    dn_quantile(y, 0.04)
}

pub fn dn_quantile_5(y: &[f64]) -> f64 {
    dn_quantile(y, 0.05)
}

pub fn dn_quantile_10(y: &[f64]) -> f64 {
    dn_quantile(y, 0.1)
}

pub fn dn_quantile_20(y: &[f64]) -> f64 {
    dn_quantile(y, 0.2)
}

pub fn dn_quantile_30(y: &[f64]) -> f64 {
    dn_quantile(y, 0.3)
}

pub fn dn_quantile_40(y: &[f64]) -> f64 {
    dn_quantile(y, 0.4)
}

pub fn dn_quantile_50(y: &[f64]) -> f64 {
    dn_quantile(y, 0.5)
}

pub fn dn_quantile_60(y: &[f64]) -> f64 {
    dn_quantile(y, 0.6)
}

pub fn dn_quantile_70(y: &[f64]) -> f64 {
    dn_quantile(y, 0.7)
}

pub fn dn_quantile_80(y: &[f64]) -> f64 {
    dn_quantile(y, 0.8)
}

pub fn dn_quantile_90(y: &[f64]) -> f64 {
    dn_quantile(y, 0.9)
}

pub fn dn_quantile_91(y: &[f64]) -> f64 {
    dn_quantile(y, 0.91)
}

pub fn dn_quantile_92(y: &[f64]) -> f64 {
    dn_quantile(y, 0.92)
}

pub fn dn_quantile_93(y: &[f64]) -> f64 {
    dn_quantile(y, 0.93)
}

pub fn dn_quantile_94(y: &[f64]) -> f64 {
    dn_quantile(y, 0.94)
}

pub fn dn_quantile_95(y: &[f64]) -> f64 {
    dn_quantile(y, 0.95)
}

pub fn dn_quantile_96(y: &[f64]) -> f64 {
    dn_quantile(y, 0.96)
}

pub fn dn_quantile_97(y: &[f64]) -> f64 {
    dn_quantile(y, 0.97)
}

pub fn dn_quantile_98(y: &[f64]) -> f64 {
    dn_quantile(y, 0.98)
}

pub fn dn_quantile_99(y: &[f64]) -> f64 {
    dn_quantile(y, 0.99)
}

// FEATURE DEFINITIONS
define_feature!(
    DNQuantile1,
    dn_quantile_1,
    "quantile_1"
);

define_feature!(
    DNQuantile2,
    dn_quantile_2,
    "quantile_2"
);

define_feature!(
    DNQuantile3,
    dn_quantile_3,
    "quantile_3"
);

define_feature!(
    DNQuantile4,
    dn_quantile_4,
    "quantile_4"
);

define_feature!(
    DNQuantile5,
    dn_quantile_5,
    "quantile_5"
);

define_feature!(
    DNQuantile10,
    dn_quantile_10,
    "quantile_10"
);

define_feature!(
    DNQuantile20,
    dn_quantile_20,
    "quantile_20"
);

define_feature!(
    DNQuantile30,
    dn_quantile_30,
    "quantile_30"
);

define_feature!(
    DNQuantile40,
    dn_quantile_40,
    "quantile_40"
);

define_feature!(
    DNQuantile50,
    dn_quantile_50,
    "quantile_50"
);  

define_feature!(
    DNQuantile60,
    dn_quantile_60,
    "quantile_60"
);

define_feature!(
    DNQuantile70,
    dn_quantile_70,
    "quantile_70"
);

define_feature!(
    DNQuantile80,
    dn_quantile_80,
    "quantile_80"
);

define_feature!(
    DNQuantile90,
    dn_quantile_90,
    "quantile_90"
);

define_feature!(
    DNQuantile91,
    dn_quantile_91,
    "quantile_91"
);

define_feature!(
    DNQuantile92,
    dn_quantile_92,
    "quantile_92"
);

define_feature!(
    DNQuantile93,
    dn_quantile_93,
    "quantile_93"
);

define_feature!(
    DNQuantile94,
    dn_quantile_94,
    "quantile_94"
);

define_feature!(
    DNQuantile95,
    dn_quantile_95,
    "quantile_95"
);

define_feature!(
    DNQuantile96,
    dn_quantile_96,
    "quantile_96"
);

define_feature!(
    DNQuantile97,
    dn_quantile_97,
    "quantile_97"
);

define_feature!(
    DNQuantile98,
    dn_quantile_98,
    "quantile_98"
);

define_feature!(
    DNQuantile99,
    dn_quantile_99,
    "quantile_99"
);

// FEATURE REGISTRY
feature_registry!(
    DNQuantile1,
    DNQuantile2,
    DNQuantile3,
    DNQuantile4,
    DNQuantile5,
    DNQuantile10,
    DNQuantile20,
    DNQuantile30,
    DNQuantile40,
    DNQuantile50,
    DNQuantile60,
    DNQuantile70,
    DNQuantile80,
    DNQuantile90,
    DNQuantile91,
    DNQuantile92,
    DNQuantile93,
    DNQuantile94,
    DNQuantile95,
    DNQuantile96,
    DNQuantile97,
    DNQuantile98,
    DNQuantile99,
);

