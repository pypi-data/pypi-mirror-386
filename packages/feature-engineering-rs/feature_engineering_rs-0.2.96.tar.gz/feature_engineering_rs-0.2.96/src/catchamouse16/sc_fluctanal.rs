use crate::helpers::common::*;

// GSL FFI bindings for robust multifit
#[repr(C)]
struct GslVector {
    _private: [u8; 0],
}

#[repr(C)]
struct GslMatrix {
    _private: [u8; 0],
}

#[repr(C)]
struct GslMultifitRobustType {
    _private: [u8; 0],
}

#[repr(C)]
struct GslMultifitRobustWorkspace {
    _private: [u8; 0],
}

#[link(name = "gsl")]
#[link(name = "gslcblas")]
extern "C" {
    static gsl_multifit_robust_bisquare: *const GslMultifitRobustType;
    
    fn gsl_set_error_handler_off();
    
    fn gsl_vector_alloc(n: usize) -> *mut GslVector;
    fn gsl_vector_free(v: *mut GslVector);
    fn gsl_vector_set(v: *mut GslVector, i: usize, x: f64);
    fn gsl_vector_get(v: *const GslVector, i: usize) -> f64;
    
    fn gsl_matrix_alloc(n1: usize, n2: usize) -> *mut GslMatrix;
    fn gsl_matrix_free(m: *mut GslMatrix);
    fn gsl_matrix_set(m: *mut GslMatrix, i: usize, j: usize, x: f64);
    fn gsl_matrix_get(m: *const GslMatrix, i: usize, j: usize) -> f64;
    
    fn gsl_multifit_robust_alloc(
        t: *const GslMultifitRobustType,
        n: usize,
        p: usize,
    ) -> *mut GslMultifitRobustWorkspace;
    fn gsl_multifit_robust_free(w: *mut GslMultifitRobustWorkspace);
    fn gsl_multifit_robust(
        x: *const GslMatrix,
        y: *const GslVector,
        c: *mut GslVector,
        cov: *mut GslMatrix,
        w: *mut GslMultifitRobustWorkspace,
    ) -> i32;
}

// Helper function for polynomial fitting (order 2)
fn polynomialfit(n: usize, x: &[f64], y: &[f64]) -> [f64; 3] {
    // Build normal equations for polynomial of order 2
    let mut s = [0.0; 6]; // sum of x^0, x^1, x^2, x^3, x^4
    let mut t = [0.0; 3]; // sum of y*x^0, y*x^1, y*x^2
    
    for i in 0..n {
        let xi = x[i];
        let yi = y[i];
        let mut xi_pow = 1.0;
        
        for j in 0..6 {
            s[j] += xi_pow;
            if j < 3 {
                t[j] += yi * xi_pow;
            }
            xi_pow *= xi;
        }
    }
    
    // Solve 3x3 system - Gaussian elimination
    let mut aug = [
        [s[0], s[1], s[2], t[0]],
        [s[1], s[2], s[3], t[1]],
        [s[2], s[3], s[4], t[2]],
    ];
    
    // Forward elimination
    for i in 0..3 {
        let pivot = aug[i][i];
        for j in i..4 {
            aug[i][j] /= pivot;
        }
        for k in (i + 1)..3 {
            let factor = aug[k][i];
            for j in i..4 {
                aug[k][j] -= factor * aug[i][j];
            }
        }
    }
    
    // Back substitution
    let mut coeff = [0.0; 3];
    for i in (0..3).rev() {
        coeff[i] = aug[i][3];
        for j in (i + 1)..3 {
            coeff[i] -= aug[i][j] * coeff[j];
        }
    }
    
    coeff
}

pub fn sc_fluctanal_2_dfa_50_2_logi_r2_se2(y: &[f64], normalize: bool) -> f64 {
    // NaN check
    if y.iter().any(|&val| val.is_nan()) {
        return f64::NAN;
    }
    
    let size = y.len();
    let data = if normalize {
        zscore_norm2_f(y)
    } else {
        y.to_vec()
    };
    
    // Generate log spaced tau vector
    let lin_low = (5.0_f64).ln();
    let lin_high = ((size / 2) as f64).ln();
    let n_tau_steps = 50;
    let tau_step = (lin_high - lin_low) / ((n_tau_steps - 1) as f64);
    
    let mut tau: Vec<usize> = (0..n_tau_steps)
        .map(|i| (lin_low + (i as f64) * tau_step).exp().round() as usize)
        .collect();
    
    // Remove duplicates (they're already in ascending order)
    tau.dedup();
    let n_tau = tau.len();
    
    // Fewer than 12 points -> leave
    if n_tau < 12 {
        return 0.0;
    }
    
    // Transform input vector to cumsum - using common.rs helper
    let y_cs = cumsum_f(&data);
    
    // Generate support for regression
    let max_tau = tau[n_tau - 1];
    let x_reg: Vec<f64> = (1..=max_tau).map(|i| i as f64).collect();
    
    // Iterate over taus, cut signal, detrend and save amplitude
    let mut f_vals = vec![0.0; n_tau];
    
    for i in 0..n_tau {
        let tau_i = tau[i];
        let n_buffer = size / tau_i;
        
        f_vals[i] = 0.0;
        
        for j in 0..n_buffer {
            // Polynomial regression of order 2
            let coeff = polynomialfit(tau_i, &x_reg[..tau_i], &y_cs[j * tau_i..(j + 1) * tau_i]);
            
            let mut buffer = vec![0.0; tau_i];
            for k in 0..tau_i {
                let x_k = (k + 1) as f64;
                buffer[k] = y_cs[j * tau_i + k] - (coeff[2] * x_k * x_k + coeff[1] * x_k + coeff[0]);
            }
            
            f_vals[i] += buffer.iter().map(|&v| v * v).sum::<f64>();
        }
        
        f_vals[i] = (f_vals[i] / ((n_buffer * tau_i) as f64)).sqrt();
    }
    
    let log_tt: Vec<f64> = tau.iter().map(|&t| (t as f64).ln()).collect();
    let log_ff: Vec<f64> = f_vals.iter().map(|&f| f.ln()).collect();
    
    let min_points = 6;
    let nsserr = n_tau - 2 * min_points + 1;
    let mut sserr = vec![0.0; nsserr];
    
    for i in min_points..(n_tau - min_points + 1) {
        // Use linreg_f from common.rs
        let (m1, b1) = linreg_f(&log_tt[..i], &log_ff[..i]).unwrap_or((0.0, 0.0));
        let (m2, b2) = linreg_f(&log_tt[i - 1..], &log_ff[i - 1..]).unwrap_or((0.0, 0.0));
        
        let buffer1: Vec<f64> = (0..i).map(|j| log_tt[j] * m1 + b1 - log_ff[j]).collect();
        sserr[i - min_points] = euclidean_norm_f(&buffer1);
        
        // Use the same slice as the regression
        let buffer2: Vec<f64> = log_tt[i - 1..]
            .iter()
            .zip(&log_ff[i - 1..])
            .map(|(&tt, &ff)| tt * m2 + b2 - ff)
            .collect();
        sserr[i - min_points] += euclidean_norm_f(&buffer2);
    }
    
    // Use min_f from common.rs
    let minimum = min_f(&sserr, Some(false));
    // Handle NaN case explicitly since NaN != NaN
    let first_min_ind = if minimum.is_nan() {
        // If minimum is NaN, just use the first index as fallback
        min_points
    } else {
        // Find the index more robustly (avoid exact floating-point equality)
        sserr.iter()
            .enumerate()
            .min_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal))
            .map(|(idx, _)| idx + min_points - 1)
            .unwrap_or(min_points)
    };    
    let r2_len = n_tau - first_min_ind;
    
    unsafe {
        gsl_set_error_handler_off();
        
        let r2_logtt = gsl_vector_alloc(r2_len);
        let r2_logff = gsl_vector_alloc(r2_len);
        
        if r2_logtt.is_null() || r2_logff.is_null() {
            if !r2_logtt.is_null() { gsl_vector_free(r2_logtt); }
            if !r2_logff.is_null() { gsl_vector_free(r2_logff); }
            return f64::NAN;
        }
        
        for i in 0..r2_len {
            gsl_vector_set(r2_logtt, i, log_tt[first_min_ind + i]);
            gsl_vector_set(r2_logff, i, log_ff[first_min_ind + i]);
        }
        
        // Robust fitting with bi-square objective
        let p = 2; // linear fit
        let c = gsl_vector_alloc(p);
        let x_mat = gsl_matrix_alloc(r2_len, p);
        let cov = gsl_matrix_alloc(p, p);
        
        if c.is_null() || x_mat.is_null() || cov.is_null() {
            gsl_vector_free(r2_logtt);
            gsl_vector_free(r2_logff);
            if !c.is_null() { gsl_vector_free(c); }
            if !x_mat.is_null() { gsl_matrix_free(x_mat); }
            if !cov.is_null() { gsl_matrix_free(cov); }
            return f64::NAN;
        }
        
        // Construct design matrix X for linear fit
        for i in 0..r2_len {
            let xi = gsl_vector_get(r2_logtt, i);
            gsl_matrix_set(x_mat, i, 0, 1.0);
            gsl_matrix_set(x_mat, i, 1, xi);
        }
        
        let work = gsl_multifit_robust_alloc(gsl_multifit_robust_bisquare, r2_len, p);
        if work.is_null() {
            gsl_vector_free(r2_logtt);
            gsl_vector_free(r2_logff);
            gsl_vector_free(c);
            gsl_matrix_free(x_mat);
            gsl_matrix_free(cov);
            return f64::NAN;
        }
        
        let status = gsl_multifit_robust(x_mat, r2_logff, c, cov, work);
        
        let out = if status == 0 {
            gsl_matrix_get(cov, 1, 1).sqrt()
        } else {
            f64::NAN
        };
        
        // Cleanup
        gsl_multifit_robust_free(work);
        gsl_matrix_free(x_mat);
        gsl_vector_free(c);
        gsl_matrix_free(cov);
        gsl_vector_free(r2_logtt);
        gsl_vector_free(r2_logff);
        
        out
    }
}