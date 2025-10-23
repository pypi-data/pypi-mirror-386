use crate::{define_feature, feature_registry};
/// Returns the proportion of values in a data vector that meet a specified condition.
///
/// # Arguments
/// * `x` - The input data vector
/// * `prop_what` - The type of proportion to calculate:
///   - "zeros": proportion of values equal to zero
///   - "positive": proportion of values strictly greater than zero  
///   - "geq0": proportion of values greater than or equal to zero
///
/// # Returns
/// * `f64` - The proportion as a value between 0.0 and 1.0
fn dn_proportionvalues(x:&[f64], propwhat: &str) -> f64{
    let n = x.len() as f64;

    if n == 0.0 {
        return f64::NAN;
    }

    match propwhat {
        "zeros" => x.iter().filter(|&&x| x == 0.0).count() as f64 / n,
        "positives" => x.iter().filter(|&&x| x > 0.0).count() as f64 / n,
        "geq0" => x.iter().filter(|&&x| x >= 0.0).count() as f64 / n,
        _ => panic!("Unknown condition to measure: {}", propwhat),
    }
}

pub fn dn_proportionvalues_zeros(x: &[f64]) -> f64 {
    dn_proportionvalues(x, "zeros")
}

pub fn dn_proportionvalues_positives(x: &[f64]) -> f64 {
    dn_proportionvalues(x, "positives")
}

pub fn dn_proportionvalues_geq0(x: &[f64]) -> f64 {
    dn_proportionvalues(x, "geq0")
}

// FEATURE DEFINITIONS
define_feature!(
    DNProportionValuesZeros,
    dn_proportionvalues_zeros,
    "DN_ProportionValues_zeros"
);

define_feature!(
    DNProportionValuesPositives,
    dn_proportionvalues_positives,
    "DN_ProportionValues_positive"
);

define_feature!(
    DNProportionValuesGeq0,
    dn_proportionvalues_geq0,
    "DN_ProportionValues_geq0"
);

// FEATURE REGISTRY
feature_registry!(
    DNProportionValuesZeros,
    DNProportionValuesPositives,
    DNProportionValuesGeq0,
);



