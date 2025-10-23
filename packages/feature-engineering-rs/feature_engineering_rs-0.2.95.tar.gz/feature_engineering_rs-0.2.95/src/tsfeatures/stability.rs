use crate::helpers::common::{mean_f, var_f};

/// Variance of window means—how stable the level of the series is.
///
/// # What it does
/// - Chops the series into windows of length `freq` (or 10 when `freq` is `Some(1)` or `None`).
/// - Computes the mean of each window after dropping NaNs.
/// - Returns the sample variance of those means, yielding `0.0` when fewer than two windows remain.
///
/// # In simple terms
/// 1. Average each block of observations.
/// 2. Compare how those averages move across the series.
/// 3. Return 0 for a flat level, larger numbers for drifting means.
///
/// # Why it matters
/// - **Trend vs. level**: Complements lumpiness by focusing on shifts in mean rather than variance.
/// - **Model diagnostics**: Helps pick between mean-stationary vs. drifting models.
/// - **Feature parity**: Matches the TSFeatures "stability" feature used in forecasting toolkits.
///
/// # Parameters
/// - `x`: Time-series samples.
/// - `freq`: Seasonal period; uses 10 when it is 1 or missing.
///
/// # Returns
/// Sample variance of window means, or `0.0` when the series is too short to form multiple windows.
pub fn stability(x: &[f64], freq: Option<usize>) -> f64 {
    let width = if freq == Some(1) { 10 } else { freq.unwrap_or(1) };
    let nr = x.len();
    
    if nr < 2 * width {
        return 0.0;
    }

    let nsegs = nr / width;
    let mut means = Vec::with_capacity(nsegs);

    for i in 0..nsegs {
        let start = i * width;
        let end = (start + width).min(nr);
        let segment = &x[start..end];
        
        // Filter out NaN values and use the stats::mean function
        let valid_values: Vec<f64> = segment.iter()
            .filter(|&&val| !val.is_nan())
            .copied()
            .collect();
        
        let mean_val = if !valid_values.is_empty() {
            mean_f(&valid_values, Some("arithmetic"))
        } else {
            f64::NAN
        };
        means.push(mean_val);
    }
    
    let stability = var_f(&means, 1);
    
    stability
}
