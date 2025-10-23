use crate::helpers::common::mean_f;

/// Phillips–Perron unit-root statistic (Zₐ form).
///
/// # What it does
/// - Fits an AR(1) with intercept, applies heteroskedasticity-robust corrections via Bartlett weights,
///   and returns the PP statistic using the default truncation lag `4 * (n / 100)^(1/4)`.
///
/// # In simple terms
/// 1. Test whether differencing is needed.
/// 2. Very negative values suggest stationarity; values near zero indicate a unit root.
///
/// # Why it matters
/// - **Differencing guidance**: Complements KPSS when assessing level stationarity.
/// - **Feature parity**: Matches the `unitroot_pp` feature from the tsfeatures package.
/// - **Automation**: Useful regressor for auto-model selection heuristics.
///
/// # Parameters
/// - `x`: Time-series samples.
/// - `freq`: Present for API compatibility; ignored by the current implementation.
///
/// # Returns
/// Phillips–Perron test statistic, or `NaN` when the auxiliary regression cannot be estimated.

pub fn unitroot_pp(x: &[f64], freq: i32) -> f64 {
    let test_pp = match ur_pp(x) {
        Ok(statistic) => statistic,
        Err(_) => f64::NAN,
    };
    test_pp
}

/// Performs the Phillips and Perron unit root test
/// 
/// # Parameters
/// - `x`: Time series data
/// 
/// # Returns
/// Result containing the test statistic or error
/// 
/// # References
/// Based on https://www.rdocumentation.org/packages/urca/versions/1.3-0/topics/ur.pp
fn ur_pp(x: &[f64]) -> Result<f64, String> {
    let n = x.len();
    if n < 2 {
        return Err("Time series too short".to_string());
    }
    
    // Check for NaN values
    if x.iter().any(|&v| v.is_nan()) {
        return Err("Time series contains NaN values".to_string());
    }
    
    // Calculate lmax (truncation lag)
    let lmax = 4.0 * (n as f64 / 100.0).powf(0.25);
    let lmax = lmax.floor() as usize;
    
    // Create lagged series: y = x[1:], y_l1 = x[:-1]
    let y: Vec<f64> = x[1..].to_vec();
    let y_l1: Vec<f64> = x[..n - 1].to_vec();
    
    let n = n - 1; // Adjust n for the differenced series
    
    // Run OLS regression: y ~ intercept + y_l1
    // We need to add a constant term to y_l1
    let (alpha, intercept, residuals, t_stat) = ols_with_constant(&y, &y_l1)?;
    
    // Calculate s (variance of residuals)
    let res_sum_sq: f64 = residuals.iter().map(|&r| r * r).sum();
    let s = 1.0 / (n as f64 * res_sum_sq);
    
    // Calculate myybar and myy
    let y_mean = mean_f(&y, Some("arithmetic"));
    let myybar = (1.0 / (n * n) as f64) * y.iter().map(|&yi| (yi - y_mean).powi(2)).sum::<f64>();
    
    // Calculate weighted covariances for non-parametric correction
    let mut coprods = Vec::with_capacity(lmax);
    for i in 0..lmax {
        if i + 1 >= n {
            break;
        }
        
        // Calculate product of residuals at lag i+1
        let prod_sum: f64 = residuals[i + 1..]
            .iter()
            .zip(residuals[..n - i - 1].iter())
            .map(|(&a, &b)| a * b)
            .sum();
        
        coprods.push(prod_sum);
    }
    
    // Apply Bartlett weights
    let mut weighted_sum = 0.0;
    for (i, &coprod) in coprods.iter().enumerate() {
        let weight = 1.0 - ((i + 1) as f64) / ((lmax + 1) as f64);
        weighted_sum += weight * coprod;
    }
    
    // Calculate sig (long-run variance)
    let sig = s + (2.0 / n as f64) * weighted_sum;
    
    // Calculate lambda and lambda_prime
    let lambda = 0.5 * (sig - s);
    
    // Calculate Phillips-Perron test statistic
    let test_stat = n as f64 * (alpha - 1.0) - lambda / myybar;
    
    Ok(test_stat)
}

/// Perform OLS regression with constant: y = alpha * x + intercept + error
/// Returns (alpha, intercept, residuals, t_statistic_for_alpha)
fn ols_with_constant(y: &[f64], x: &[f64]) -> Result<(f64, f64, Vec<f64>, f64), String> {
    let n = y.len();
    if n != x.len() {
        return Err("Input vectors must have the same length".to_string());
    }
    
    // Calculate means
    let x_mean = mean_f(x, Some("arithmetic"));
    let y_mean = mean_f(y, Some("arithmetic"));
    
    // Calculate slope (alpha)
    let mut num = 0.0;
    let mut denom = 0.0;
    for i in 0..n {
        num += (x[i] - x_mean) * (y[i] - y_mean);
        denom += (x[i] - x_mean) * (x[i] - x_mean);
    }
    
    if denom == 0.0 {
        return Err("Singular matrix in OLS".to_string());
    }
    
    let alpha = num / denom;
    let intercept = y_mean - alpha * x_mean;
    
    // Calculate residuals
    let mut residuals = Vec::with_capacity(n);
    let mut rss = 0.0;
    for i in 0..n {
        let fitted = alpha * x[i] + intercept;
        let resid = y[i] - fitted;
        residuals.push(resid);
        rss += resid * resid;
    }
    
    // Calculate standard error and t-statistic for alpha
    let sigma_squared = rss / (n - 2) as f64;
    let se_alpha = (sigma_squared / denom).sqrt();
    let t_stat = alpha / se_alpha;
    
    Ok((alpha, intercept, residuals, t_stat))
}
