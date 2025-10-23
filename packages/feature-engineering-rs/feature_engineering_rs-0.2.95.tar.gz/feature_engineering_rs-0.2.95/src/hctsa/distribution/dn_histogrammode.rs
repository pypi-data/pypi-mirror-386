use crate::{define_feature, feature_registry};

use crate::catch22::histcounts::histcounts;
use crate::helpers::common::abs_f;

/// DN_HistogramMode - Mode of a data vector.
///
/// Measures the mode of the data vector using histograms with a given number
/// of bins.
///
/// # Arguments
///
/// * `y` - The input data vector
/// * `nbins` - The number of bins to use in the histogram
/// * `normalize` - Whether to normalize the data using z-score normalization
///
/// # Returns
///
/// The mode of the data vector. Returns NaN if the input contains NaN or infinite values.
///
/// # Algorithm
///
/// 1. Check for NaN/infinite values in input
/// 2. Optionally normalize data using z-score normalization
/// 3. Create histogram with specified number of bins
/// 4. Find bin(s) with maximum count
/// 5. Return average of bin centers for bins with maximum count
fn dn_histogrammode(y: &[f64], nbins: usize) -> f64 {
    // NaN check
    if y.iter().any(|&val| val.is_nan() || val.is_infinite()) {
        return f64::NAN;
    }

    let (hist_counts, bin_edges) = histcounts(&y, nbins);

    let mut max_count = 0i32;
    let mut num_maxs = 1;
    let mut out = 0.0;

    for i in 0..nbins {
        if hist_counts[i] > max_count {
            max_count = hist_counts[i];
            num_maxs = 1;
            out = (bin_edges[i] + bin_edges[i + 1]) * 0.5;
        } else if hist_counts[i] == max_count {
            num_maxs += 1;
            out += (bin_edges[i] + bin_edges[i + 1]) * 0.5;
        }
    }

    out / num_maxs as f64
}

/// Calculate histogram mode using 5 bins
pub fn dn_histogrammode_5(y: &[f64]) -> f64 {
    dn_histogrammode(y, 5)
}

/// Calculate histogram mode using 10 bins
pub fn dn_histogrammode_10(y: &[f64]) -> f64 {
    dn_histogrammode(y, 10)
}

/// Calculate histogram mode using 12 bins
pub fn dn_histogrammode_12(y: &[f64]) -> f64 {
    dn_histogrammode(y, 12)
}

/// Calculate histogram mode using 21 bins
pub fn dn_histogrammode_21(y: &[f64]) -> f64 {
    dn_histogrammode(y, 21)
}

/// Calculate histogram mode using 52 bins
pub fn dn_histogrammode_52(y: &[f64]) -> f64 {
    dn_histogrammode(y, 52)
}

/////////////////////////////////////////////////////////////
// ABS
/// Calculate histogram mode using 5 bins
pub fn dn_histogrammode_abs_5(y: &[f64]) -> f64 {
    let y_abs = abs_f(y);
    dn_histogrammode(&y_abs, 5)
}

/// Calculate histogram mode using 10 bins
pub fn dn_histogrammode_abs_10(y: &[f64]) -> f64 {
    let y_abs = abs_f(y);
    dn_histogrammode(&y_abs, 10)
}

/// Calculate histogram mode using 12 bins
pub fn dn_histogrammode_abs_12(y: &[f64]) -> f64 {
    let y_abs = abs_f(y);
    dn_histogrammode(&y_abs, 12)
}

/// Calculate histogram mode using 21 bins
pub fn dn_histogrammode_abs_21(y: &[f64]) -> f64 {
    let y_abs = abs_f(y);
    dn_histogrammode(&y_abs, 21)
}

/// Calculate histogram mode using 52 bins
pub fn dn_histogrammode_abs_52(y: &[f64]) -> f64 {
    let y_abs = abs_f(y);
    dn_histogrammode(&y_abs, 52)
}

// FEATURE DEFINITIONS
define_feature!(
    DNHistogramMode5,
    dn_histogrammode_5,
    "DN_HistogramMode_5"
);

define_feature!(
    DNHistogramMode10,
    dn_histogrammode_10,
    "DN_HistogramMode_10"
);

define_feature!(
    DNHistogramMode12,
    dn_histogrammode_12,
    "DN_HistogramMode_12"
);

define_feature!(
    DNHistogramMode21,
    dn_histogrammode_21,
    "DN_HistogramMode_21"
);

define_feature!(
    DNHistogramMode52,
    dn_histogrammode_52,
    "DN_HistogramMode_52"
);

define_feature!(
    DNHistogramModeAbs5,
    dn_histogrammode_abs_5,
    "DN_HistogramMode_Abs_5"
);

define_feature!(
    DNHistogramModeAbs10,
    dn_histogrammode_abs_10,
    "DN_HistogramMode_Abs_10"
);

define_feature!(
    DNHistogramModeAbs12,
    dn_histogrammode_abs_12,
    "DN_HistogramMode_Abs_12"
);

define_feature!(
    DNHistogramModeAbs21,
    dn_histogrammode_abs_21,
    "DN_HistogramMode_Abs_21"
);

define_feature!(
    DNHistogramModeAbs52,
    dn_histogrammode_abs_52,
    "DN_HistogramMode_Abs_52"
);

// FEATURE REGISTRY
feature_registry!(
    DNHistogramMode5,
    DNHistogramMode10,
    DNHistogramMode12,
    DNHistogramMode21,
    DNHistogramMode52,
    DNHistogramModeAbs5,
    DNHistogramModeAbs10,
    DNHistogramModeAbs12,
    DNHistogramModeAbs21,
    DNHistogramModeAbs52,
);

