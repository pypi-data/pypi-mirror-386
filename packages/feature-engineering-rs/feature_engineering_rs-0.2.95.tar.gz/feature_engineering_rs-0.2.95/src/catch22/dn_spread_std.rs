use crate::helpers::common::stdev_f;
// use crate::features::stats::stddev;

pub fn dn_spread_std(y: &[f64]) -> f64 {
    stdev_f(y, 1)
}
