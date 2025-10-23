use std::cmp::Ordering;
use crate::helpers::common_types::Cplx;

// Calculate the minimum of a vector of f64s
pub fn min_f(a: &[f64], skip_nan: Option<bool>) -> f64 {

    if !skip_nan.unwrap_or(false) && a.iter().any(|&x| x.is_nan()) {
        return f64::NAN;
    }

    a.iter()
        .filter(|&&x| !x.is_nan())
        .fold(f64::INFINITY, |acc, &x| acc.min(x))
}

// Calculate the maximum of a vector of f64s
pub fn max_f(a: &[f64], skip_nan: Option<bool>) -> f64 {

    if !skip_nan.unwrap_or(false) && a.iter().any(|&x| x.is_nan()) {
        return f64::NAN;
    }

    a.iter()
        .filter(|&&x| !x.is_nan())
        .fold(f64::NEG_INFINITY, |acc, &x| acc.max(x))
}

// Calculate the mean of a vector of f64s
pub fn mean_f(x: &[f64], mean_type: Option<&str>) -> f64 {
    let mean_type = mean_type.unwrap_or("arithmetic");
    
    if x.iter().any(|&v| v.is_nan()) {
        return f64::NAN;
    }

    let n = x.len() as f64;
    
    match mean_type {
        "arithmetic" => x.iter().sum::<f64>() / n,
        // Geometric mean 
        "geometric" => {
            if x.iter().any(|&v| v.is_nan()) {
                f64::NAN
            } else {
                x.iter().map(|&x| x.ln()).sum::<f64>().exp()
            }
        },
        // Harmonic mean N/sum(y.^(-1))
        "harmonic" => {
            if x.iter().any(|&v| v.is_nan()) {
                f64::NAN
            } else {
                n / x.iter().map(|&x| 1.0 / x).sum::<f64>()
            }
        },
        // Root mean square (rms) sqrt(mean(y.^2))
        "rms" => (x.iter().map(|&x| x * x).sum::<f64>() / n).sqrt(),
        // Interquartile mean (iqm)
        "iqm" => {
            let mut sorted = x.to_vec();
            sorted.sort_unstable_by(|a, b| a.partial_cmp(b).unwrap());
            let q1_idx = (0.25 * n) as usize;
            let q3_idx = (0.75 * n) as usize;
            let q1 = sorted[q1_idx];
            let q3 = sorted[q3_idx];
            let filtered: Vec<f64> = sorted.into_iter()
                .filter(|&v| v >= q1 && v <= q3)
                .collect();
            if filtered.is_empty() {
                f64::NAN
            } else {
                filtered.iter().sum::<f64>() / filtered.len() as f64
            }
        },
        // Midhinge mean (midhinge)
        "midhinge" => {
            let mut sorted = x.to_vec();
            sorted.sort_unstable_by(|a, b| a.partial_cmp(b).unwrap());
            let q1_idx = (0.25 * n) as usize;
            let q3_idx = (0.75 * n) as usize;
            let q1 = sorted[q1_idx];
            let q3 = sorted[q3_idx];
            (q1 + q3) / 2.0
        },
        _ => return x.iter().sum::<f64>() / n,
    }
}

// Calculate the median of a vector of f64s
pub fn median_f(a: &[f64], skip_nan: Option<bool>) -> f64 {
    if !skip_nan.unwrap_or(false) && a.iter().any(|&x| x.is_nan()) {
        return f64::NAN;
    }

    let skip_nan = skip_nan.unwrap_or(true);
    
    let valid: Vec<f64> = if skip_nan {
        a.iter().filter(|&&x| !x.is_nan()).copied().collect()
    } else {
        a.to_vec()
    };
    
    if valid.is_empty() {
        return f64::NAN;
    }
    
    let mut sorted = valid;
    sorted.sort_unstable_by(|a, b| a.partial_cmp(b).unwrap());
    
    let size = sorted.len();
    if size % 2 == 1 {
        sorted[size / 2]
    } else {
        (sorted[size / 2 - 1] + sorted[size / 2]) / 2.0
    }
}


// Calculate the sum of a vector of f64s
pub fn sum_f(x: &[f64]) -> f64 {
    if x.iter().any(|&v| v.is_nan()) {
        return f64::NAN;
    }
    x.iter().sum()
}

// Calculate the difference of a vector of f64s
pub fn diff_f(a: &[f64]) -> Vec<f64> {
    a.windows(2).map(|w| w[1] - w[0]).collect()
}

// Calculate the cumulative sum of a vector of f64s
pub fn cumsum_f(a: &[f64]) -> Vec<f64> {

    if a.iter().any(|&v| v.is_nan()) {
        return vec![f64::NAN; a.len()];  
    }

    let mut result = Vec::with_capacity(a.len());
    let mut running_sum = 0.0;
    for &val in a {
        running_sum += val;
        result.push(running_sum);
    }
    result
}

// Calculate the sum of a vector of i32s
pub fn isum_f(a: &[i32]) -> f64 {

    a.iter().map(|&x| x as f64).sum()
}

// Calculate the cumulative sum of a vector of i32s
pub fn icumsum_f(a: &[i32]) -> Vec<i32> {

    let mut result = Vec::with_capacity(a.len());
    let mut running_sum = 0;
    for &val in a {
        running_sum += val;
        result.push(running_sum);
    }
    result
}

// Calculate the standard deviation of a vector of f64s
pub fn stdev_f(x: &[f64], ddof: usize) -> f64 {
    if x.iter().any(|&v| v.is_nan()) {
        return f64::NAN;
    }

    var_f(x, ddof).sqrt()
}

// Calculate the variance of a vector of f64s with ddof
pub fn var_f(a: &[f64], ddof: usize) -> f64 {
    if a.len() <= ddof {
        return f64::NAN;
    }
    
    let m = mean_f(a, Some("arithmetic"));
    if m.is_nan() {
        return f64::NAN;
    }
    
    let variance_sum: f64 = a.iter()
        .map(|&x| (x - m).powi(2))
        .sum();
    
    variance_sum / (a.len() - ddof) as f64
}


pub fn nanstd_f(x: &[f64], ddof: usize) -> f64 {
    nan_variance_f(x, ddof).sqrt()
}

pub fn nan_variance_f(x: &[f64], ddof: usize) -> f64 {
    // Filter out NaN values only (keep infinity)
    let valid: Vec<f64> = x.iter()
        .filter(|&&v| !v.is_nan())
        .copied()
        .collect();
    
    if valid.len() <= ddof {
        return f64::NAN;
    }
    
    let mean: f64 = valid.iter().sum::<f64>() / valid.len() as f64;
    let variance: f64 = valid.iter()
        .map(|&value| (value - mean).powi(2))
        .sum::<f64>() / (valid.len() - ddof) as f64;
    
    variance
}

pub fn cov_mean_f(x: &[f64], y: &[f64]) -> f64 {
    assert_eq!(x.len(), y.len());

    x.iter()
        .zip(y.iter())
        .map(|(&xi, &yi)| xi * yi)
        .sum::<f64>()
        / x.len() as f64
}


// Calculate the covariance of two vectors of f64s
pub fn covariance_f(x: &[f64], y: &[f64]) -> f64 {

    if x.contains(&f64::NAN) || y.contains(&f64::NAN) {
        return f64::NAN;
    }

    let avg_x: f64 = mean_f(x, Some("arithmetic"));
    let avg_y: f64 = mean_f(y, Some("arithmetic"));

    let covariance: f64 = x
        .iter()
        .zip(y.iter())
        .map(|(&v_x, &v_y)| (v_x - avg_x) * (v_y - avg_y))
        .sum::<f64>();

    covariance / (x.len() - 1) as f64
}

// Calculate the correlation of two vectors of f64s
pub fn corr_f(x: &[f64], y: &[f64]) -> f64 {

    if x.iter().any(|&v| v.is_nan()) || y.iter().any(|&v| v.is_nan()) {
        return f64::NAN;
    }

    let cov: f64 = covariance_f(x, y);
    let deno: f64 = stdev_f(x, 1) * stdev_f(y, 1);

    if near_f(deno, 0.0) {
        return f64::NAN;
    }

    cov / deno
}

// Calculate the quantile of a vector of f64s
pub fn quantile_f(y: &[f64], quant: f64) -> f64 {

    if y.iter().any(|&v| v.is_nan()) {
        return f64::NAN;
    }

    let size = y.len();
    let mut tmp: Vec<f64> = y.to_vec();
    tmp.sort_by(|a, b| a.partial_cmp(b).unwrap_or(Ordering::Equal));

    // out of range limit?
    let q = 0.5 / size as f64;
    if quant < q {
        return tmp[0]; // min value
    } else if quant > (1.0 - q) {
        return tmp[size - 1]; // max value
    }

    let quant_idx = size as f64 * quant - 0.5;
    let idx_left = quant_idx.floor() as usize;
    let idx_right = quant_idx.ceil() as usize;

    tmp[idx_left]
        + (quant_idx - idx_left as f64) * (tmp[idx_right] - tmp[idx_left])
            / (idx_right - idx_left) as f64
}

// Calculate the euclidean norm of a vector of f64s
pub fn euclidean_norm_f(a: &[f64]) -> f64 {
    a.iter().map(|&x| x * x).sum::<f64>().sqrt()
}

// Calculate the z-score normalized vector of a vector of f64s
pub fn zscore_norm2_f(a: &[f64]) -> Vec<f64> {

    if a.iter().any(|&v| v.is_nan()) {
        return vec![f64::NAN];
    }

    let m = mean_f(a, Some("arithmetic"));
    let sd = stdev_f(a, 1);
    a.iter().map(|&x| (x - m) / sd).collect()
}

// Multiply two complex numbers
pub fn cmul_f(x: Cplx, y: Cplx) -> Cplx {
    x * y
}

// Subtract two complex numbers
pub fn cminus_f(x: Cplx, y: Cplx) -> Cplx {
    x - y
}

// Add two complex numbers
pub fn cadd_f(x: Cplx, y: Cplx) -> Cplx {
    x + y
}

// Divide two complex numbers
pub fn cdiv_f(x: Cplx, y: Cplx) -> Cplx {
    x / y
}


// Linear regression
pub fn linreg_f(x: &[f64], y: &[f64]) -> Result<(f64, f64), &'static str> {
    assert_eq!(x.len(), y.len());
    let n = x.len() as f64;

    let sumx = x.iter().sum::<f64>();
    let sumx2 = x.iter().map(|&xi| xi * xi).sum::<f64>();
    let sumxy = x
        .iter()
        .zip(y.iter())
        .map(|(&xi, &yi)| xi * yi)
        .sum::<f64>();
    let sumy = y.iter().sum::<f64>();

    let denom = n * sumx2 - sumx * sumx;
    if denom == 0.0 {
        return Err("Singular matrix. Can't solve the problem.");
    }

    let m = (n * sumxy - sumx * sumy) / denom;
    let b = (sumy * sumx2 - sumx * sumxy) / denom;

    Ok((m, b))
}

// Autocorrelation lag
pub fn autocorr_lag_f(x: &[f64], lag: usize) -> f64 {
    if lag >= x.len() {
        return f64::NAN;
    }
    corr_f(&x[..x.len() - lag], &x[lag..])
}

// Autocovariance lag
pub fn autocov_lag_f(x: &[f64], lag: usize) -> f64 {
    if lag >= x.len() {
        return f64::NAN;
    }
    cov_mean_f(&x[..x.len() - lag], &x[lag..])
}

// Calculate the entropy of a vector of f64s
pub fn entropy_f(a: &[f64]) -> f64 {
    -a.iter()
        .filter(|&&x| x > 0.0)
        .map(|&x| x * x.ln())
        .sum::<f64>()
}

// Check if two f64s are close to each other
pub fn near_f(x: f64, y: f64) -> bool {
    let epsilon: f64 = f64::EPSILON.sqrt();
    if !x.is_finite() || !y.is_finite() {
        return false;
    }
    (x - y).abs() < epsilon
}

pub fn linspace_f(start: f64, end: f64, num_groups: usize) -> Vec<f64> {
    let mut result = vec![0.0; num_groups];
    let step_size = (end - start) / (num_groups - 1) as f64;
    let mut val = start;
    for i in 0..num_groups {
        result[i] = val;
        val += step_size;  
    }
    result
}

pub fn abs_f(a: &[f64]) -> Vec<f64> {
    a.iter().map(|&x| x.abs()).collect()
}

pub fn iqr_f(y: &[f64]) -> f64 {
    let mut sorted = y.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());
    
    let n = sorted.len();
    let q1_idx = n / 4;
    let q3_idx = 3 * n / 4;
    
    let q1 = if n % 4 == 0 {
        (sorted[q1_idx - 1] + sorted[q1_idx]) / 2.0
    } else {
        sorted[q1_idx]
    };
    
    let q3 = if n % 4 == 0 {
        (sorted[q3_idx - 1] + sorted[q3_idx]) / 2.0
    } else {
        sorted[q3_idx]
    };
    
    q3 - q1
}

pub fn mad_f(y: &[f64], flag: Option<&str>) -> f64 {

    if flag.unwrap_or("mean") == "mean" {
        let y_mean = mean_f(y, Some("arithmetic"));
        let deviations: Vec<f64> = y.iter()
            .map(|&val| (val - y_mean).abs())
            .collect();
        
        mean_f(&deviations, Some("arithmetic"))
    } else {
        let y_median = median_f(y, Some(false));
        let deviations: Vec<f64> = y.iter()
            .map(|&val| (val - y_median).abs())
            .collect();
        median_f(&deviations, Some(false))
    }
}