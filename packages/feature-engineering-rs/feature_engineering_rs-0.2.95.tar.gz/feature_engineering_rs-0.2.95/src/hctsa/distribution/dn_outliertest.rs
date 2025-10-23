use crate::{define_feature, feature_registry};
use crate::helpers::common::{mean_f, stdev_f};

fn dn_outliertest(y: &[f64], p: f64, how: &str) -> f64 {
    if y.is_empty() || y.iter().any(|&val| val.is_nan()) {
        return f64::NAN;
    }
    
    // Calculate percentiles using linear interpolation (closer to MATLAB's prctile)
    let mut sorted = y.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    
    let n = sorted.len() as f64;
    
    // Calculate percentile indices with linear interpolation
    let lower_pos = (p / 100.0) * (n - 1.0);
    let upper_pos = ((100.0 - p) / 100.0) * (n - 1.0);
    
    // Linear interpolation for percentiles
    let lower_threshold = if lower_pos.fract() == 0.0 {
        sorted[lower_pos as usize]
    } else {
        let idx = lower_pos.floor() as usize;
        let weight = lower_pos.fract();
        sorted[idx] * (1.0 - weight) + sorted[(idx + 1).min(sorted.len() - 1)] * weight
    };
    
    let upper_threshold = if upper_pos.fract() == 0.0 {
        sorted[upper_pos as usize]
    } else {
        let idx = upper_pos.floor() as usize;
        let weight = upper_pos.fract();
        sorted[idx] * (1.0 - weight) + sorted[(idx + 1).min(sorted.len() - 1)] * weight
    };
    
    // Filter to middle (100-2*p)% of data
    // Note: Using > and < (exclusive) to match MATLAB behavior
    let filtered: Vec<f64> = y.iter()
        .filter(|&&val| val > lower_threshold && val < upper_threshold)
        .copied()
        .collect();
    
    if filtered.is_empty() {
        return f64::NAN;
    }
    
    match how {
        "std" => {
            // Return ratio: std(filtered) / std(original)
            let std_filtered = stdev_f(&filtered, 1);
            let std_original = stdev_f(y, 1);
            
            if std_original == 0.0 || std_original.is_nan() {
                return f64::NAN;
            }
            
            std_filtered / std_original
        },
        "mean" => {
            // Return mean of filtered data
            mean_f(&filtered, Some("arithmetic"))
        },
        _ => f64::NAN,
    }
}


pub fn dn_outliertest2_mean(y: &[f64]) -> f64 {
    dn_outliertest(y, 2.0, "mean")
}

pub fn dn_outliertest2_std(y: &[f64]) -> f64 {
    dn_outliertest(y, 2.0, "std")
}

pub fn dn_outliertest5_mean(y: &[f64]) -> f64 {
    dn_outliertest(y, 5.0, "mean")
}

pub fn dn_outliertest5_std(y: &[f64]) -> f64 {
    dn_outliertest(y, 5.0, "std")
}

pub fn dn_outliertest10_mean(y: &[f64]) -> f64 {
    dn_outliertest(y, 10.0, "mean")
}

pub fn dn_outliertest10_std(y: &[f64]) -> f64 {
    dn_outliertest(y, 10.0, "std")
}

// FEATURE DEFINITIONS
define_feature!(
    DNOutliertest2Mean,
    dn_outliertest2_mean,
    "DN_Outliertest_2_mean"
);

define_feature!(
    DNOutliertest2Std,
    dn_outliertest2_std,
    "DN_Outliertest_2_std"
);

define_feature!(
    DNOutliertest5Mean,
    dn_outliertest5_mean,
    "DN_Outliertest_5_mean"
);

define_feature!(
    DNOutliertest5Std,
    dn_outliertest5_std,
    "DN_Outliertest_5_std"
);

define_feature!(
    DNOutliertest10Mean,
    dn_outliertest10_mean,
    "DN_Outliertest_10_mean"
);

define_feature!(
    DNOutliertest10Std,
    dn_outliertest10_std,
    "DN_Outliertest_10_std"
);

// FEATURE REGISTRY
feature_registry!(
    DNOutliertest2Mean,
    DNOutliertest2Std,
    DNOutliertest5Mean,
    DNOutliertest5Std,
    DNOutliertest10Mean,
    DNOutliertest10Std,
);