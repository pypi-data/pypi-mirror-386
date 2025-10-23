pub fn bf_point_of_crossing(x: &[f64], threshold: f64) -> (usize, f64) {
    let n = x.len();
    
    if n == 0 {
        return (0, 0.0);
    }
    
    // Find first crossing
    let first_crossing = if x[0] > threshold {
        // Looking for crossing downward (x - threshold < 0)
        x.iter()
            .position(|&val| val - threshold < 0.0)
    } else {
        // Looking for crossing upward (x - threshold > 0)
        x.iter()
            .position(|&val| val - threshold > 0.0)
    };
    
    match first_crossing {
        None => {
            // Never crosses
            (n, n as f64)
        }
        Some(idx) => {
            if idx == 0 {
                // Edge case: crossing at first point
                (idx, idx as f64)
            } else {
                // Interpolate the continuous crossing point
                let value_before = x[idx - 1];
                let value_after = x[idx];
                let point_of_crossing = (idx - 1) as f64 
                    + (threshold - value_before) / (value_after - value_before);
                (idx, point_of_crossing)
            }
        }
    }
}