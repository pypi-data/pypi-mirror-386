use crate::helpers::common::mean_f;

/// Embeds the time series x into a low-dimensional Euclidean space.
pub fn embed(x: &[f64], p: usize) -> Vec<Vec<f64>> {
    let n = x.len();
    if n < p {
        return Vec::new();
    }
    
    // Create p rolled versions of x
    let mut rolled_arrays = Vec::with_capacity(p);
    
    for k in 0..p {
        let mut rolled = vec![0.0; n];
        
        // Implement np.roll behavior: elements that roll beyond the last position
        // are re-introduced at the first
        for i in 0..n {
            let source_idx = (n + i - k) % n;
            rolled[i] = x[source_idx];
        }
        
        rolled_arrays.push(rolled);
    }
    
    // Transpose and skip first p-1 rows
    // The transpose makes each row of the result contain one element from each rolled array
    let mut result = Vec::with_capacity(n - p + 1);
    
    for i in (p - 1)..n {
        let mut row = Vec::with_capacity(p);
        for j in 0..p {
            row.push(rolled_arrays[j][i]);
        }
        result.push(row);
    }
    
    result
}

/// Solve linear system Ax = b using Gaussian elimination with partial pivoting
fn solve_linear_system(a_input: &[Vec<f64>], b_input: &[f64]) -> Option<Vec<f64>> {
    let n = a_input.len();
    if n == 0 || a_input[0].len() != n || b_input.len() != n {
        return None;
    }
    
    // Create augmented matrix
    let mut a = a_input.to_vec();
    let mut b = b_input.to_vec();
    
    // Forward elimination with partial pivoting
    for k in 0..n {
        // Find pivot
        let mut max_val = a[k][k].abs();
        let mut max_row = k;
        
        for i in (k + 1)..n {
            if a[i][k].abs() > max_val {
                max_val = a[i][k].abs();
                max_row = i;
            }
        }
        
        // Check for singular matrix
        if max_val < 1e-10 {
            return None;
        }
        
        // Swap rows
        if max_row != k {
            a.swap(k, max_row);
            b.swap(k, max_row);
        }
        
        // Eliminate column
        for i in (k + 1)..n {
            let factor = a[i][k] / a[k][k];
            for j in (k + 1)..n {
                a[i][j] -= factor * a[k][j];
            }
            b[i] -= factor * b[k];
            a[i][k] = 0.0;
        }
    }
    
    // Back substitution
    let mut x = vec![0.0; n];
    for i in (0..n).rev() {
        x[i] = b[i];
        for j in (i + 1)..n {
            x[i] -= a[i][j] * x[j];
        }
        x[i] /= a[i][i];
    }
    
    Some(x)
}

/// Calculate R-squared matching sklearn's LinearRegression behavior exactly
fn calculate_r_squared_sklearn(x_mat: &[Vec<f64>], y: &[f64], fit_intercept: bool) -> f64 {
    let n = y.len();
    
    // sklearn returns NaN for less than 2 samples
    if n < 2 {
        return f64::NAN;
    }
    
    if x_mat.is_empty() {
        return f64::NAN;
    }
    
    // Build design matrix with intercept if needed
    let design_matrix = if fit_intercept {
        let mut x_with_intercept = Vec::with_capacity(n);
        for (i, row) in x_mat.iter().enumerate() {
            let mut new_row = vec![1.0]; // Intercept term first
            new_row.extend_from_slice(row);
            x_with_intercept.push(new_row);
        }
        x_with_intercept
    } else {
        x_mat.to_vec()
    };
    
    let p = design_matrix[0].len();
    
    // Calculate X'X
    let mut xtx = vec![vec![0.0; p]; p];
    for i in 0..p {
        for j in i..p {
            let mut sum = 0.0;
            for row in &design_matrix {
                sum += row[i] * row[j];
            }
            xtx[i][j] = sum;
            xtx[j][i] = sum; // Symmetric matrix
        }
    }
    
    // Calculate X'y
    let mut xty = vec![0.0; p];
    for i in 0..p {
        let mut sum = 0.0;
        for (j, row) in design_matrix.iter().enumerate() {
            sum += row[i] * y[j];
        }
        xty[i] = sum;
    }
    
    // Solve the system using Gaussian elimination
    let coefficients = match solve_linear_system(&xtx, &xty) {
        Some(b) => b,
        None => return f64::NAN,
    };
    
    // Calculate predictions
    let mut y_pred = vec![0.0; n];
    for (i, row) in design_matrix.iter().enumerate() {
        for (j, &coef) in coefficients.iter().enumerate() {
            y_pred[i] += row[j] * coef;
        }
    }
    
    // Calculate R² using sklearn's formula
    let y_mean = y.iter().sum::<f64>() / n as f64;
    
    let mut numerator = 0.0;
    let mut denominator = 0.0;
    
    for i in 0..n {
        let residual = y[i] - y_pred[i];
        let deviation = y[i] - y_mean;
        numerator += residual * residual;
        denominator += deviation * deviation;
    }
    
    // Handle sklearn's force_finite=True behavior (default)
    if denominator == 0.0 {
        if numerator == 0.0 {
            return 1.0;
        } else {
            return 0.0;
        }
    }
    
    // Check for very small denominator to avoid numerical issues
    if denominator < 1e-10 {
        if numerator < 1e-10 {
            return 1.0;
        } else {
            return 0.0;
        }
    }
    
    // Standard R² formula
    1.0 - (numerator / denominator)
}

/// ARCH model features.
/// 
/// Calculates the R² value of an autoregressive model of order `lags` 
/// applied to the squared values of the time series.
/// 
/// This implementation matches sklearn's LinearRegression().fit().score() behavior.
/// 
/// # What it does
/// 
/// This function measures how predictable changes in volatility are over time.
/// It's like asking: "Can I predict how turbulent tomorrow will be based on 
/// how turbulent the past few days have been?"
/// 
/// # In simple terms
/// 
/// 1. Takes your time series (like daily returns or stock prices)
/// 2. (Optionally) demeans the values so they're centered around zero
/// 3. Squares each value — large moves up or down both show up as "high volatility"
/// 4. Uses the previous `lags` squared values to predict the next one
/// 5. Returns an R² score (0–1) — higher means volatility is more predictable
/// 
/// # Why it matters
/// 
/// - **ARCH effects**: Detects volatility clustering (quiet periods followed by storms)  
/// - **Financial modeling**: Basis for volatility models like GARCH  
/// - **Risk management**: Identifies periods of heightened risk  
/// - **Model diagnostics**: Helps decide if plain OLS is enough or a GARCH model is needed  
/// 
/// # Example
/// 
/// - If R² = 0.3 → about 30% of volatility changes are predictable from recent history  
/// - If R² = 0.05 → volatility is mostly random  
/// 
/// # Parameters
/// - `x`: The time series data  
/// - `lags`: Number of lags for the autoregressive model (default: 12)  
/// - `demean`: Whether to demean the series before processing (default: true)  
/// 
/// # Returns
/// R² value of the autoregressive model applied to x²
pub fn arch_stat(x: &[f64], lags: usize, demean: bool) -> f64 {
    // Check if we have enough data
    if x.len() <= lags + 1 {
        return f64::NAN;
    }
    
    // Demean if requested
    let x_processed: Vec<f64> = if demean {
        let mean = mean_f(x, Some("arithmetic"));
        if mean.is_nan() {
            return f64::NAN;
        }
        x.iter().map(|&val| val - mean).collect()
    } else {
        x.to_vec()
    };
    
    // Square the values
    let x_squared: Vec<f64> = x_processed.iter().map(|&val| val * val).collect();
    
    // Embed the squared series
    let mat = embed(&x_squared, lags + 1);
    
    if mat.is_empty() {
        return f64::NAN;
    }
    
    // Prepare X (all columns except the first) and y (first column)
    let y: Vec<f64> = mat.iter().map(|row| row[0]).collect();
    let x_mat: Vec<Vec<f64>> = mat.iter()
        .map(|row| row[1..].to_vec())
        .collect();
    
    // Calculate R-squared using sklearn-compatible method
    // sklearn's LinearRegression always fits intercept by default (fit_intercept=True)
    calculate_r_squared_sklearn(&x_mat, &y, true)
}

