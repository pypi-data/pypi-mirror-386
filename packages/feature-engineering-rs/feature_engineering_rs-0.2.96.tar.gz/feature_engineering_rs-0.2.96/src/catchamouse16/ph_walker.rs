use crate::helpers::common::*;

pub fn ph_walker_momentum_5_w_momentumzcross(y: &[f64], normalize: bool) -> f64 {
    if y.iter().any(|&val| val.is_nan()) {
        return f64::NAN;
    }

    let data = if normalize {
        zscore_norm2_f(y)
    } else {
        y.to_vec()
    };

    let n = data.len();
    
    if n < 2 {
        return f64::NAN;
    }

    let mut w = vec![0.0; n]; 
    let m = 5.0;

    w[0] = data[0];
    w[1] = data[1];

    let mut w_inert;

    for i in 2..n {
        w_inert = w[i-1] + (w[i-1] - w[i-2]);
        w[i] = w_inert + (data[i] - w_inert) / m;
    }

    let mut w_propzcross = 0.0;

    for i in 1..n {
        if w[i-1] * w[i] < 0.0 {
            w_propzcross += 1.0;
        }
    }
    
    w_propzcross / (n as f64 - 1.0)
}

pub fn ph_walker_biasprop_05_01_sw_meanabsdiff(y: &[f64], normalize: bool) -> f64 {
    if y.iter().any(|&val| val.is_nan()) {
        return f64::NAN;
    }

    let data = if normalize {
        zscore_norm2_f(y)
    } else {
        y.to_vec()
    };

    let n = data.len();
    let mut w = vec![0.0; n]; 
    let pup = 0.5;
    let pdown = 0.1;

    w[0] = 0.0;
    for i in 1..n {
        if data[i] > data[i-1] {
            w[i] = w[i-1] + pup * (data[i-1] - w[i-1]);
        } else {
            w[i] = w[i-1] + pdown * (data[i-1] - w[i-1]);
        }
    }

    let mut sw_meanabsdiff = 0.0;
    for i in 0..n {
        sw_meanabsdiff += (data[i] - w[i]).abs();
    }
    sw_meanabsdiff / n as f64
    
}