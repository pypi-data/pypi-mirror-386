use crate::helpers::common::median_f;

/// Computes the number of times a time series crosses the median.
/// 
/// This function counts how many times the time series moves from above the median
/// to below it (or vice versa) as it progresses through time.
/// 
/// # What it does
/// 
/// This function measures how often a time series oscillates around its median value.
/// 
/// # In simple terms
/// 
/// 1. Calculates the median of the entire time series
/// 2. For each point, checks if it's above or below the median
/// 3. Counts every time the series switches from above to below (or vice versa)
/// 4. Returns the total number of crossings
/// 
/// # Why it matters
/// 
/// - **Market behavior**: High crossings suggest mean-reverting behavior
/// - **Trend analysis**: Low crossings indicate strong trends or persistence
/// - **Volatility patterns**: More crossings often correlate with higher volatility
/// - **Model selection**: Helps choose between trend-following vs mean-reverting models
/// 
/// # Example
/// 
/// - If crossings = 8 → the series crossed its median 8 times
/// - If crossings = 2 → the series mostly stayed on one side of the median
/// 
/// # Parameters
/// - `series`: The time series data
/// 
/// # Returns
/// Number of times the series crosses its median (as f64)
pub fn crossing_points(series: &[f64]) -> f64 {
    
    if series.len() < 2 {
        return 0.0;
    }
    
    let median = median_f(series, Some(false));
    
    // Count crossings using iterator methods
    let ab: Vec<bool> = series.iter()
        .map(|&x| !x.is_nan() && !median.is_nan() && x <= median)
        .collect();
    
    ab.windows(2)
        .filter(|w| w[0] != w[1])
        .count() as f64
}
