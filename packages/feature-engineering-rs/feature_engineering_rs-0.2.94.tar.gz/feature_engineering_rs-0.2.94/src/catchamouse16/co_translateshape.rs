use crate::helpers::common::*;
use crate::catchamouse16::sy_slidingwindow::sy_slidingwindow;

pub fn co_translateshape_circle_35_pts(y: &[f64], normalize: bool, whichout: &str) -> f64 {
    if y.iter().any(|&val| val.is_nan()) {
        return f64::NAN;
    }

    let data = if normalize {
        zscore_norm2_f(y)
    } else {
        y.to_vec()
    };

    let size = data.len();
    let r = 3.5_f64;
    let w = r.floor() as usize;

    if size <= 2 * w {
        return f64::NAN;
    }

    let nn = size - 2 * w; // number of admissible points

    if nn == 0 {
        return f64::NAN;
    }

    let mut np = vec![0.0; nn];
    
    for i in (w + 1)..=(size - w) {
        let mut count = 0;
        
        for j in (i - w)..=(i + w) {
            let difwin_sum = ((j as f64 - i as f64) * (j as f64 - i as f64)) + 
                            ((data[j - 1] - data[i - 1]) * (data[j - 1] - data[i - 1]));
            
            if difwin_sum <= r * r {
                count += 1;
            }
        }
        
        np[i - w - 1] = count as f64;
    }
    
    // Return standard deviation (equivalent to "std" case)
    match whichout {
        "std" => {
            stdev_f(&np, 1)
        }
        "statav4_m" => {
            sy_slidingwindow(&np, "mean", "std", 4, 1, false)
        }
        _ => {
            f64::NAN
        }
    }
}

pub fn co_translateshape_circle_35_pts_statav4_m(y: &[f64], normalize: bool) -> f64 {
    co_translateshape_circle_35_pts(y, normalize, "statav4_m")
}

pub fn co_translateshape_circle_35_pts_std(y: &[f64], normalize: bool) -> f64 {
    co_translateshape_circle_35_pts(y, normalize, "std")
}