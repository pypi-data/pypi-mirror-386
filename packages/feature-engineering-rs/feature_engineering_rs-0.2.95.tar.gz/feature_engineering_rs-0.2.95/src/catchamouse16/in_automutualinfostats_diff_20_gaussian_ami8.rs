use crate::helpers::common::*;

pub fn in_automutualinfostats_diff_20_gaussian_ami8(y: &[f64], normalize: bool) -> f64 {
    if y.iter().any(|&val| val.is_nan()) {
        return f64::NAN;
    }
    
    let data = if normalize {
        zscore_norm2_f(y)
    } else {
        y.to_vec()
    };
    
    let y_diff = diff_f(&data);
    let diff_size = data.len() - 1;

    let mut tau = 20.0;

    if tau > (diff_size as f64 / 2.0).ceil() as f64 {
        tau = (diff_size as f64 / 2.0).ceil() as f64;
    }

    let ac = autocorr_lag_f(&y_diff, 8);
    let ami8 = -0.5 * (1.0 - ac * ac).ln();

    if tau >= 7.0 {
        ami8
    } else {
        f64::NAN
    }
}