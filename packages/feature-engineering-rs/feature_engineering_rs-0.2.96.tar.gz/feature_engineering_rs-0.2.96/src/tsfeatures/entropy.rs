use crate::helpers::common::mean_f;
use crate::helpers::common_types::Cplx;
use rustfft::FftPlanner;

pub fn spectral_entropy(x: &[f64], sf: f64, method: &str, normalize: bool) -> f64 {
    // Handle NaN/infinite values
    if x.iter().any(|&val| val.is_nan() || val.is_infinite()) {
        return f64::NAN;
    }
    
    if x.len() < 2 {
        return f64::NAN;
    }
    
    // Compute power spectral density
    let psd = match method {
        "fft" => periodogram(x, sf),
        // "welch" => welch_psd(x, sf),
        _ => return f64::NAN,
    };
    
    if psd.is_empty() {
        return f64::NAN;
    }
    
    // Normalize PSD to get probability distribution
    let psd_sum: f64 = psd.iter().sum();
    if psd_sum <= 0.0 || psd_sum.is_nan() || psd_sum.is_infinite() {
        return f64::NAN;
    }
    
    let psd_norm: Vec<f64> = psd.iter().map(|&p| p / psd_sum).collect();

    // Compute Shannon entropy: -sum(p * log2(p))
    let mut se = 0.0;
    for &p in &psd_norm {
        if p > 0.0 && p <= 1.0 {  
            se -= p * p.log2();
        }
    }
    // Handle potential NaN from entropy calculation
    if se.is_nan() {
        return f64::NAN;
    }
    
    // Normalize if requested (divide by log2 of number of frequency bins)
    if normalize {
        let max_entropy = (psd_norm.len() as f64).log2();
        if max_entropy > 0.0 {
            se /= max_entropy;
        }
    }
    
    se
}

pub fn dft(x: &[Cplx]) -> Vec<Cplx> {
    let mut planner = FftPlanner::new();
    let fft = planner.plan_fft_forward(x.len());
    
    let mut buffer: Vec<Cplx> = x.iter()
        .map(|c| Cplx::new(c.re, c.im))
        .collect();
    
    fft.process(&mut buffer);
    
    buffer.into_iter()
        .map(|c| Cplx::new(c.re, c.im))
        .collect()
}


pub fn periodogram(x: &[f64], sf: f64) -> Vec<f64> {
    let n = x.len();
    
    // Apply detrend='constant' (remove mean)
    let mean_x = mean_f(x, Some("arithmetic"));
    
    let data: Vec<Cplx> = x.iter()
        .map(|&val| Cplx::new(val - mean_x, 0.0))
        .collect();
    
    let fft_data = dft(&data);
    
    // Compute power spectral density (one-sided)
    let mut psd = Vec::with_capacity(n / 2 + 1);
    
    // Scipy uses scale = 1.0 / (fs * sum(window**2))
    // For boxcar window (all 1s), sum(window**2) = n
    let scale = 1.0 / (sf * n as f64);
    
    // DC component (index 0)
    psd.push(fft_data[0].norm_sqr() * scale);
    
    // Positive frequencies (multiply by 2 for one-sided spectrum)
    for i in 1..n / 2 {
        psd.push(2.0 * fft_data[i].norm_sqr() * scale);
    }
    
    // Nyquist frequency (if n is even, don't multiply by 2)
    if n % 2 == 0 {
        psd.push(fft_data[n / 2].norm_sqr() * scale);
    } else {
        // If n is odd, include the last positive frequency with factor 2
        psd.push(2.0 * fft_data[n / 2].norm_sqr() * scale);
    }
        
    psd
}

/// Normalized spectral entropy of a time series.
///
/// # What it does
/// - Removes the mean, estimates the one-sided power spectral density via FFT,
///   and converts it into a probability mass function.
/// - Applies base-2 Shannon entropy and, when requested, rescales by the log of the
///   number of frequency bins so the result spans 0–1.
///
/// # In simple terms
/// 1. Look at how the signal's energy is distributed across frequencies.
/// 2. Return 0 when the spectrum is concentrated in a few bins (very periodic).
/// 3. Return 1 when the spectrum is flat and energy is spread everywhere (very noisy).
///
/// # Why it matters
/// - **Signal complexity**: Captures whether the series behaves like a pure tone or broadband noise.
/// - **Feature parity**: Matches Python `tsfeatures.spectral_entropy` defaults (`sf=1`, `method="fft"`, `normalize=True`).
/// - **Downstream modeling**: Supports heuristics that pick different models for smooth vs chaotic signals.
///
/// # Parameters
/// - `x`: Time-series samples; any NaN or ±∞ short-circuits to `NaN`.
///
/// # Returns
/// Normalized spectral entropy in `[0, 1]`, or `NaN` if the spectrum cannot be computed.
pub fn entropy(x: &[f64]) -> f64 {
    // The Python version uses sf=1 and normalize=True
    spectral_entropy(x, 1.0, "fft", true)
}


// pub fn welch_psd(x: &[f64], sf: f64) -> Vec<f64> {
//     let n = x.len();
    
//     // Default nperseg = 256 (scipy default) or length of signal if shorter
//     let nperseg = n.min(256);
    
//     if nperseg < 4 {  // Need at least 4 samples for meaningful spectrum
//         return periodogram(x, sf);
//     }
    
//     // Overlap = 50% (scipy default)
//     let noverlap = nperseg / 2;
//     let step = nperseg - noverlap;
    
//     // Calculate number of segments
//     let n_segments = if n >= nperseg {
//         1 + (n - nperseg) / step
//     } else {
//         0
//     };
    
//     if n_segments == 0 {
//         return periodogram(x, sf);
//     }
    
//     // Generate Hann window
//     let window = hann_window(nperseg);
    
//     // Calculate window power for proper scaling
//     let window_power: f64 = window.iter().map(|&w| w * w).sum();
    
//     // Initialize PSD accumulator
//     let n_freqs = nperseg / 2 + 1;
//     let mut psd_sum = vec![0.0; n_freqs];
//     let mut actual_segments = 0;
    
//     // Process each segment
//     for seg_idx in 0..n_segments {
//         let start = seg_idx * step;
//         let end = start + nperseg;
        
//         if end > n {
//             break;
//         }
        
//         // Extract segment and apply window
//         let windowed: Vec<f64> = x[start..end]
//             .iter()
//             .zip(window.iter())
//             .map(|(&x_val, &w)| x_val * w)
//             .collect();
        
//         // Compute periodogram for this segment
//         let segment_psd = periodogram_windowed(&windowed, sf, window_power);
        
//         // Accumulate PSD
//         for (i, &psd_val) in segment_psd.iter().enumerate() {
//             if i < psd_sum.len() {
//                 psd_sum[i] += psd_val;
//             }
//         }
        
//         actual_segments += 1;
//     }
    
//     // Average the PSDs
//     if actual_segments > 0 {
//         psd_sum.iter_mut().for_each(|p| *p /= actual_segments as f64);
//     }
    
//     psd_sum
// }

// // Helper function for computing periodogram with pre-windowed data
// fn periodogram_windowed(x: &[f64], sf: f64, window_power: f64) -> Vec<f64> {
//     let n = x.len();
//     let n_fft = next_power_of_2(n);
    
//     // Data is already windowed, just convert to complex
//     let mut data: Vec<Cplx> = x.iter()
//         .map(|&val| Cplx::new(val, 0.0))
//         .collect();
    
//     // Zero-pad to n_fft
//     data.resize(n_fft, Cplx::new(0.0, 0.0));
    
//     // Compute FFT
//     let tw = twiddles(n_fft);
//     fft(&mut data, &tw);
    
//     // Compute power spectral density with proper window scaling
//     let mut psd = Vec::with_capacity(n_fft / 2 + 1);
    
//     // Scaling for windowed periodogram: 1/(fs * window_power)
//     let scale = 1.0 / (sf * window_power);
    
//     // DC component
//     psd.push(data[0].norm_sqr() * scale);
    
//     // Positive frequencies (multiply by 2 for one-sided spectrum)
//     for i in 1..n_fft / 2 {
//         psd.push(2.0 * data[i].norm_sqr() * scale);
//     }
    
//     // Nyquist frequency
//     if n_fft % 2 == 0 {
//         psd.push(data[n_fft / 2].norm_sqr() * scale);
//     }
    
//     psd
// }

// pub fn hann_window(n: usize) -> Vec<f64> {
//     (0..n).map(|i| {
//         let arg = 2.0 * PI * i as f64 / (n - 1) as f64;
//         0.5 * (1.0 - arg.cos())
//     }).collect()
// }

// pub fn next_power_of_2(n: usize) -> usize {
//     if n <= 1 { 
//         return 1; 
//     }
//     let mut power = 1;
//     while power < n {
//         power <<= 1;
//     }
//     power
// }

