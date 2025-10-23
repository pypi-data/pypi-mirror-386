use crate::helpers::common::*;


// Direct translation of FC_LocalSimple
fn fc_localsimple(y: &[f64], train_length: usize) -> f64 {
    if train_length >= y.len() {
        return f64::NAN;
    }
    
    let evalr_len = y.len() - train_length;
    if evalr_len == 0 {
        return f64::NAN;
    }
    
    let mut res = vec![0.0; evalr_len];
    
    for i in 0..evalr_len {
        let mut sum = 0.0;
        for j in 0..train_length {
            sum += y[i + j];
        }
        let mean_val = sum / train_length as f64;
        res[i] = mean_val - y[i + train_length]; 
    }
    
    stdev_f(&res, 1) 
}

// Translation of FC_LoopLocalSimple_mean_stderr_chn
pub fn fc_looplocalsimple_mean_stderr_chn(y: &[f64], normalize: bool) -> f64 {
    if y.iter().any(|&val| val.is_nan()) {
        return f64::NAN;
    }

    let data = if normalize {
        zscore_norm2_f(y)
    } else {
        y.to_vec()
    };
    
    let train_length_range = 10;
    let mut stats_st = vec![0.0; train_length_range];
    let mut mi = f64::MAX;
    let mut ma = f64::MIN;
    
    for i in 0..train_length_range {
        stats_st[i] = fc_localsimple(&data, i + 1);
        mi = mi.min(stats_st[i]);
        ma = ma.max(stats_st[i]);
    }
    
    let range = ma - mi;
    let st_diff = diff_f(&stats_st);
    
    
    mean_f(&st_diff, Some("arithmetic")) / range
}