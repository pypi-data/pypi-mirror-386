use crate::helpers::common::{zscore_norm2_f};

/// Terasvirta neural-network nonlinearity test statistic (scaled as in tsfeatures).
///
/// # What it does
/// - Optionally z-score normalizes the series and embeds lagged copies.
/// - Runs the Terasvirta two-stage OLS with quadratic and cubic interaction terms.
/// - Returns `10 * test / len(x)`, matching the Python tsfeatures implementation.
///
/// # In simple terms
/// 1. Fit a linear autoregression.
/// 2. Add neural-network-style interaction terms and refit.
/// 3. Compare the fits; large values mean the series departs from linear dynamics.
///
/// # Why it matters
/// - **Nonlinearity screening**: Flags when linear forecasting models may be insufficient.
/// - **Feature parity**: Matches `tsfeatures.nonlinearity` used in forecasting packages.
/// - **Workflow integration**: Feed the score into threshold-based model selection heuristics.
///
/// # Parameters
/// - `x`: Time-series samples (cloned internally); NaN or ±∞ returns `NaN`.
///
/// # Returns
/// Scaled Terasvirta test statistic, or `NaN` when the regression pipeline fails.

pub fn nonlinearity(x: Vec<f64>) -> f64 {
     
    // NaN/infinite check
    if x.iter().any(|&val| val.is_nan() || val.is_infinite()) {
        return f64::NAN;
    }
    
    match terasvirta_test(&x, 1, true) {
        Ok(test) => {
            let test_stat = 10.0 * test / x.len() as f64;
            test_stat
        }
        Err(_) => {
           return f64::NAN;
        }
    }
    
}

fn terasvirta_test(x: &[f64], lag: usize, normalize: bool) -> Result<f64, Box<dyn std::error::Error>> {
    // Scale the time series if needed
    let x_scaled = if normalize {
        zscore_norm2_f(x)
    } else {
        x.to_vec()
    };
    
    let size_x = x_scaled.len();
    
    // Create embedded matrix (lagged values)
    let y_matrix = embed(&x_scaled, lag + 1)?;
    
    // Check if we have enough data points
    if y_matrix.is_empty() {
        return Err("Insufficient data for embedding".into());
    }
    
    // Split into y (response) and X (predictors)
    let y_response = &y_matrix[0];  // First column
    let x_predictors: Vec<Vec<f64>> = (1..=lag)
        .map(|i| y_matrix[i].clone())
        .collect();
    
    // Add constant term (intercept) to X
    let x_with_constant = add_constant_to_matrix(&x_predictors);
    
    // First OLS regression: y ~ X
    let (residuals_1, ssr0) = ols_regression(y_response, &x_with_constant)?;
    
    // Create interaction terms
    let x_nn = create_interaction_terms(&x_predictors, lag);
    
    // Combine original X with interaction terms
    let mut x_combined = x_with_constant.clone();
    for term in x_nn {
        x_combined.push(term);
    }
    
    // Second OLS regression: residuals ~ [X, X_nn]
    let (residuals_2, ssr) = ols_regression(&residuals_1, &x_combined)?;
    
    // Calculate test statistic
    let stat = size_x as f64 * (ssr0 / ssr).ln();
    
    Ok(stat)
}

fn embed(x: &[f64], dimension: usize) -> Result<Vec<Vec<f64>>, Box<dyn std::error::Error>> {
    if dimension > x.len() {
        return Err("Dimension larger than series length".into());
    }
    
    let n = x.len() - dimension + 1;
    let mut embedded = vec![vec![0.0; n]; dimension];
    
    for i in 0..dimension {
        for j in 0..n {
            embedded[dimension - i - 1][j] = x[i + j];
        }
    }
    
    Ok(embedded)
}

fn add_constant_to_matrix(x: &[Vec<f64>]) -> Vec<Vec<f64>> {
    if x.is_empty() || x[0].is_empty() {
        return vec![vec![1.0]];
    }
    
    let n = x[0].len();
    let mut result = vec![vec![1.0; n]];  // Constant term
    
    for row in x {
        result.push(row.clone());
    }
    
    result
}

fn create_interaction_terms(x: &[Vec<f64>], lag: usize) -> Vec<Vec<f64>> {
    let mut terms = Vec::new();
    let n = if !x.is_empty() { x[0].len() } else { 0 };
    
    // Second-order interactions (Xi * Xj)
    for i in 0..lag {
        for j in i..lag {
            let mut interaction = vec![0.0; n];
            for k in 0..n {
                interaction[k] = x[i][k] * x[j][k];
            }
            terms.push(interaction);
        }
    }
    
    // Third-order interactions (Xi * Xj * Xk)
    for i in 0..lag {
        for j in i..lag {
            for k in j..lag {
                let mut interaction = vec![0.0; n];
                for m in 0..n {
                    interaction[m] = x[i][m] * x[j][m] * x[k][m];
                }
                terms.push(interaction);
            }
        }
    }
    
    terms
}

fn ols_regression(y: &[f64], x: &[Vec<f64>]) -> Result<(Vec<f64>, f64), Box<dyn std::error::Error>> {
    let n = y.len();
    let p = x.len();  // number of predictors (including constant)
    
    if n == 0 || p == 0 {
        return Err("Empty input data".into());
    }
    
    // Check dimensions match
    for predictor in x {
        if predictor.len() != n {
            return Err("Dimension mismatch".into());
        }
    }
    
    // Create X'X matrix
    let mut xtx = vec![vec![0.0; p]; p];
    for i in 0..p {
        for j in 0..p {
            let mut sum = 0.0;
            for k in 0..n {
                sum += x[i][k] * x[j][k];
            }
            xtx[i][j] = sum;
        }
    }
    
    // Create X'y vector
    let mut xty = vec![0.0; p];
    for i in 0..p {
        let mut sum = 0.0;
        for j in 0..n {
            sum += x[i][j] * y[j];
        }
        xty[i] = sum;
    }
    
    // Solve normal equations (X'X)β = X'y
    // Using simple Gaussian elimination for small matrices
    let beta = solve_linear_system(&xtx, &xty)?;
    
    // Calculate residuals
    let mut residuals = vec![0.0; n];
    let mut ssr = 0.0;
    
    for i in 0..n {
        let mut y_pred = 0.0;
        for j in 0..p {
            y_pred += beta[j] * x[j][i];
        }
        residuals[i] = y[i] - y_pred;
        ssr += residuals[i] * residuals[i];
    }
    
    Ok((residuals, ssr))
}

fn solve_linear_system(a: &[Vec<f64>], b: &[f64]) -> Result<Vec<f64>, Box<dyn std::error::Error>> {
    let n = a.len();
    if n == 0 || a[0].len() != n || b.len() != n {
        return Err("Invalid matrix dimensions".into());
    }
    
    // Create augmented matrix
    let mut aug = vec![vec![0.0; n + 1]; n];
    for i in 0..n {
        for j in 0..n {
            aug[i][j] = a[i][j];
        }
        aug[i][n] = b[i];
    }
    
    // Forward elimination with partial pivoting
    for i in 0..n {
        // Find pivot
        let mut max_row = i;
        for k in (i + 1)..n {
            if aug[k][i].abs() > aug[max_row][i].abs() {
                max_row = k;
            }
        }
        aug.swap(i, max_row);
        
        // Check for singular matrix
        if aug[i][i].abs() < 1e-10 {
            return Err("Singular matrix".into());
        }
        
        // Eliminate column
        for k in (i + 1)..n {
            let factor = aug[k][i] / aug[i][i];
            for j in i..=n {
                aug[k][j] -= factor * aug[i][j];
            }
        }
    }
    
    // Back substitution
    let mut x = vec![0.0; n];
    for i in (0..n).rev() {
        x[i] = aug[i][n];
        for j in (i + 1)..n {
            x[i] -= aug[i][j] * x[j];
        }
        x[i] /= aug[i][i];
    }
    
    Ok(x)
}