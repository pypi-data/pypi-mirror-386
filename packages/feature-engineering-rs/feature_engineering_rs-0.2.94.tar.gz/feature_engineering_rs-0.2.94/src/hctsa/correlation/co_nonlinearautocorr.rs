use crate::{define_feature, feature_registry};


fn co_nonlinearautocorr(y: &[f64], taus: &[usize; 3], normalize: bool) -> f64 {
    if y.iter().any(|&val| val.is_nan()) {
        return f64::NAN;
    }
    

    let size = y.len();
    let tmax = taus[2];

    // Check if time series is long enough
    if size <= tmax {
        return f64::NAN;
    }
    
    // Initialize nlac array
    let mut nlac = vec![0.0; size];
    
    // Copy data starting from tmax
    for i in tmax..size {
        nlac[i - tmax] = y[i];
    }

    let size_nlac = size - tmax;
    
    // Apply nonlinear autocorrelation for each tau
    for i in 0..3 {
        let start = tmax - taus[i];
        let end = size - taus[i];
        
        if start >= end {
            return f64::NAN;
        }
        
        for j in start..end {
            nlac[j - start] *= y[j];
        }
    }
    
    
    // Return mean of the first size_nlac elements
    nlac[..size_nlac].iter().sum::<f64>() / size_nlac as f64
}

