/// Length of the longest “flat” spell after binning the series into 10 equal-width buckets.
///
/// # What it does
/// - Cleans infinities, filters NaNs, and mirrors Pandas' bin edges (including the 0.1% left-edge shift).
/// - Assigns each observation to a bin and counts the longest run of consecutive values in the same bin.
/// - Treats an all-equal series as one long flat spot.
///
/// # In simple terms
/// 1. Slice the value range into 10 buckets.
/// 2. Walk the series and see how long it stays in the same bucket.
/// 3. Return that longest stay as a float.
///
/// # Why it matters
/// - **Plateau detection**: Highlights prolonged stretches of identical or near-identical values.
/// - **Data quality**: Flags sensors that get stuck producing the same reading.
/// - **Model selection**: Flat regions often call for piecewise or regime-based models.
///
/// # Parameters
/// - `x`: Time-series samples; NaN rows are skipped, ±∞ returns `NaN`.
///
/// # Returns
/// Longest run length as `f64`, or `NaN` when no finite data is available.

pub fn flat_spots(x: &[f64]) -> f64 {
    // Handle edge cases
    if x.is_empty() || x.iter().any(|&v| v.is_infinite()){
        return f64::NAN;
    }
    
    if x.len() == 1 {
        return 1.0;
    }
    
    // Filter out NaN values for min/max calculation (like pandas)
    let finite_vals: Vec<f64> = x.iter().filter(|&&v| v.is_finite()).copied().collect();
    
    if finite_vals.is_empty() {
        return f64::NAN;
    }
    
    let min_val = finite_vals.iter().fold(f64::INFINITY, |a, &b| a.min(b));
    let max_val = finite_vals.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
    
    // Check for infinity in min/max
    if min_val.is_infinite() || max_val.is_infinite() {
        return f64::NAN;
    }
    
    // Handle constant series (pandas adjusts by 0.1% when min==max)
    if (max_val - min_val).abs() < f64::EPSILON {
        // When all values are the same, pandas creates adjusted bins
        // and all values fall into the same bin, so max run length = length
        return x.len() as f64;
    }
    
    // Create bins exactly like pandas: np.linspace(min, max, bins+1)
    let num_bins = 10;
    let mut bin_edges: Vec<f64> = Vec::with_capacity(num_bins + 1);
    for i in 0..=num_bins {
        bin_edges.push(min_val + (max_val - min_val) * i as f64 / num_bins as f64);
    }
    
    // Adjust leftmost edge by 0.1% (pandas default behavior with right=True)
    let adj = (max_val - min_val) * 0.001;
    bin_edges[0] -= adj;
    
    // Assign each value to a bin
    let mut binned: Vec<i32> = Vec::with_capacity(x.len());
    
    for &val in x {
        if val.is_nan() {
            binned.push(-1); // NaN marker
        } else {
            let mut bin_idx = 0;
            
            // Find the appropriate bin using pandas logic
            // For include_lowest=True: first interval is [min, edge1], others are (edge_i, edge_i+1]
            if val <= bin_edges[1] {
                bin_idx = 0; // First bin (pandas returns 0-based indices)
            } else {
                // Find the rightmost bin edge that val is greater than
                for i in 1..num_bins {
                    if val <= bin_edges[i + 1] {
                        bin_idx = i;
                        break;
                    }
                }
            }
            
            // Convert to 1-based indexing (like Python code does: +1)
            binned.push((bin_idx + 1) as i32);
        }
    }
    
    // Find maximum run length using itertools.groupby logic
    if binned.is_empty() {
        return 1.0;
    }
    
    let mut max_run_length = 1;
    let mut current_run_length = 1;
    let mut current_value = binned[0];
    
    for i in 1..binned.len() {
        if binned[i] == current_value && binned[i] != -1 {
            current_run_length += 1;
        } else {
            max_run_length = max_run_length.max(current_run_length);
            current_run_length = 1;
            current_value = binned[i];
        }
    }
    
    // Don't forget the last run
    max_run_length = max_run_length.max(current_run_length);
    
    max_run_length as f64
}