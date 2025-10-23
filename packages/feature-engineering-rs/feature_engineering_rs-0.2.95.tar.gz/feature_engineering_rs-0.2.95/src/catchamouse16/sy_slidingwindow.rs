use crate::helpers::common::{mean_f, stdev_f, zscore_norm2_f};

pub fn sy_slidingwindow(y: &[f64], window_stat: &str, across_win_stat: &str, num_seg: usize, inc_move: usize, normalize: bool) -> f64 {
    // NAN check
    if y.iter().any(|&val| val.is_nan()) {
        return f64::NAN;
    }

    let data = if normalize {
        zscore_norm2_f(y)
    } else {
        y.to_vec()
    };

    let size = data.len();
    let winlen = size / num_seg;
    let mut inc = winlen / inc_move;
    if inc == 0 {
        inc = 1;
    }

    let num_steps = (size - winlen) / inc + 1;
    let mut qs = Vec::with_capacity(num_steps);

    match window_stat {
        "mean" => {
            for i in 0..num_steps {
                let start_idx = i * inc;
                let end_idx = start_idx + winlen;
                let window_slice = &data[start_idx..end_idx];
                qs.push(mean_f(window_slice, Some("arithmetic")));
            }
        }
        "std" => {
            for i in 0..num_steps {
                let start_idx = i * inc;
                let end_idx = start_idx + winlen;
                let window_slice = &data[start_idx..end_idx];
                qs.push(stdev_f(window_slice, 1)); // ddof=1 for sample std
            }
        }
        _ => {
            return f64::NAN;
        }
    }

    // NAN check on computed statistics
    if qs.iter().any(|&val| val.is_nan()) {
        return f64::NAN;
    }

    match across_win_stat {
        "std" => {
            let qs_std = stdev_f(&qs, 1);
            let y_std = stdev_f(&data, 1);
            qs_std / y_std
        }
        _ => {
            f64::NAN
        }
    }
}