use crate::{define_feature, feature_registry};
use rustfft::FftPlanner;
use rustfft::num_complex::Complex;

fn nextpow2(n: usize) -> usize {
    if n == 0 {
        return 1;
    }
    n.next_power_of_two()
}

/// Compute the autocorrelation of an input time series
///
/// # Arguments
///
/// * `y` - A scalar time series column vector
/// * `tau` - The time-delay. If tau is a scalar, returns autocorrelation for y at that
///           lag. If tau is a vector, returns autocorrelations for y at that set of
///           lags. Can set tau empty, [], to return the full function for the
///           'Fourier' estimation method.
///
/// # Returns
///
/// The autocorrelation at the given time lag(s).
///
/// # Notes
///
/// Specifying whatMethod = 'TimeDomain' can tolerate NaN values in the time
/// series.
///
/// Computing mean/std across the full time series makes a significant difference
/// for short time series, but can produce values outside [-1,+1]. The
/// filtering-based method used by Matlab's autocorr, is probably the best for
/// short time series, and is implemented here by specifying: whatMethod =
/// 'Fourier'.
///
/// This implementation uses the Fourier method (Wiener-Khinchin theorem) for
/// efficient computation of autocorrelation via FFT.
pub fn co_autocorr(y: &[f64], tau: Option<&[usize]>) -> Vec<f64> {

    if y.iter().any(|&val| val.is_nan()) {
        return vec![f64::NAN];
    }

    let n = y.len();
    
    // Compute mean
    let m: f64 = y.iter().sum::<f64>() / n as f64;
    
    // FFT size: 2^(nextpow2(N)+1)
    let n_fft = nextpow2(n) * 2;
    
    // Create mean-centered, zero-padded buffer
    let mut buffer: Vec<Complex<f64>> = y.iter()
        .map(|&val| Complex::new(val - m, 0.0))
        .collect();
    buffer.resize(n_fft, Complex::new(0.0, 0.0));
    
    // Setup FFT planner
    let mut planner = FftPlanner::new();
    let fft = planner.plan_fft_forward(n_fft);
    let ifft = planner.plan_fft_inverse(n_fft);
    
    // Forward FFT
    fft.process(&mut buffer);
    
    // Multiply by complex conjugate: F.*conj(F)
    for val in buffer.iter_mut() {
        *val = *val * val.conj();
    }
    
    // Inverse FFT (Wiener-Khinchin theorem)
    ifft.process(&mut buffer);
    
    // rustfft doesn't normalize IFFT, so we need to divide by n_fft
    let scale = 1.0 / n_fft as f64;
    for val in buffer.iter_mut() {
        *val *= scale;
    }
    
    // Normalize by acf(0) and extract real parts (first N values)
    let acf_zero = buffer[0].re;
    let acf: Vec<f64> = buffer.iter()
        .take(n)
        .map(|c| c.re / acf_zero)
        .collect();
    
    // Return autocorrelation at requested lags
    match tau {
        None => {
            // Return the full autocorrelation function
            acf
        }
        Some(lags) => {
            // Return autocorrelation at requested lags
            lags.iter()
                .map(|&lag| {
                    if lag < acf.len() {
                        acf[lag]
                    } else {
                        f64::NAN
                    }
                })
                .collect()
        }
    }

}

pub fn ac_1(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[1]))[0]
}

pub fn ac_2(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[2]))[0]
}

pub fn ac_3(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[3]))[0]
}

pub fn ac_4(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[4]))[0]
}

pub fn ac_5(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[5]))[0]
}

pub fn ac_6(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[6]))[0]
}

pub fn ac_7(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[7]))[0]
}

pub fn ac_8(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[8]))[0]
}

pub fn ac_9(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[9]))[0]
}

pub fn ac_10(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[10]))[0]
}

pub fn ac_11(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[11]))[0]
}

pub fn ac_12(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[12]))[0]
}

pub fn ac_13(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[13]))[0]
}

pub fn ac_14(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[14]))[0]
}

pub fn ac_15(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[15]))[0]
}

pub fn ac_16(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[16]))[0]
}

pub fn ac_17(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[17]))[0]
}

pub fn ac_18(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[18]))[0]
}

pub fn ac_19(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[19]))[0]
}

pub fn ac_20(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[20]))[0]
}

pub fn ac_21(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[21]))[0]
}

pub fn ac_22(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[22]))[0]
}

pub fn ac_23(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[23]))[0]
}

pub fn ac_24(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[24]))[0]
}

pub fn ac_25(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[25]))[0]
}

pub fn ac_26(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[26]))[0]
}

pub fn ac_27(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[27]))[0]
}

pub fn ac_28(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[28]))[0]
}

pub fn ac_29(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[29]))[0]
}

pub fn ac_30(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[30]))[0]
}

pub fn ac_31(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[31]))[0]
}

pub fn ac_32(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[32]))[0]
}

pub fn ac_33(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[33]))[0]
}

pub fn ac_34(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[34]))[0]
}

pub fn ac_35(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[35]))[0]
}

pub fn ac_36(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[36]))[0]
}   

pub fn ac_37(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[37]))[0]
}

pub fn ac_38(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[38]))[0]
}

pub fn ac_39(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[39]))[0]
}

pub fn ac_40(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[40]))[0]
}

pub fn ac_52(y: &[f64]) -> f64 {
    co_autocorr(y, Some(&[52]))[0]
}

define_feature!(
    AC1,
    ac_1,
    "AC_1"
);

define_feature!(
    AC2,
    ac_2,
    "AC_2"
);

define_feature!(
    AC3,
    ac_3,
    "AC_3"
);

define_feature!(
    AC4,
    ac_4,
    "AC_4"
);

define_feature!(
    AC5,
    ac_5,
    "AC_5"
);

define_feature!(
    AC6,
    ac_6,
    "AC_6"
);

define_feature!(
    AC7,
    ac_7,
    "AC_7"
);

define_feature!(
    AC8,
    ac_8,
    "AC_8"
);

define_feature!(
    AC9,
    ac_9,
    "AC_9"
);

define_feature!(
    AC10,
    ac_10,
    "AC_10"
);

define_feature!(
    AC11,
    ac_11,
    "AC_11"
);

define_feature!(
    AC12,
    ac_12,
    "AC_12"
);

define_feature!(
    AC13,
    ac_13,
    "AC_13"
);

define_feature!(
    AC14,
    ac_14,
    "AC_14"
);

define_feature!(
    AC15,
    ac_15,
    "AC_15"
);

define_feature!(
    AC16,
    ac_16,
    "AC_16"
);

define_feature!(
    AC17,
    ac_17,
    "AC_17"
);

define_feature!(
    AC18,
    ac_18,
    "AC_18"
);

define_feature!(
    AC19,
    ac_19,
    "AC_19"
);

define_feature!(
    AC20,
    ac_20,
    "AC_20"
);

define_feature!(
    AC21,
    ac_21,
    "AC_21"
);

define_feature!(
    AC22,
    ac_22,
    "AC_22"
);

define_feature!(
    AC23,
    ac_23,
    "AC_23"
);

define_feature!(
    AC24,
    ac_24,
    "AC_24"
);

define_feature!(
    AC25,
    ac_25,
    "AC_25"
);

define_feature!(
    AC26,
    ac_26,
    "AC_26"
);

define_feature!(
    AC27,
    ac_27,
    "AC_27"
);

define_feature!(
    AC28,
    ac_28,
    "AC_28"
);

define_feature!(
    AC29,
    ac_29,
    "AC_29"
);

define_feature!(
    AC30,
    ac_30,
    "AC_30"
);

define_feature!(
    AC31,
    ac_31,
    "AC_31"
);

define_feature!(
    AC32,
    ac_32,
    "AC_32"
);

define_feature!(
    AC33,
    ac_33,
    "AC_33"
);

define_feature!(
    AC34,
    ac_34,
    "AC_34"
);

define_feature!(
    AC35,
    ac_35,
    "AC_35"
);

define_feature!(
    AC36,
    ac_36,
    "AC_36"
);

define_feature!(
    AC37,
    ac_37,
    "AC_37"
);

define_feature!(
    AC38,
    ac_38,
    "AC_38"
);

define_feature!(
    AC39,
    ac_39,
    "AC_39"
);

define_feature!(
    AC40,
    ac_40,
    "AC_40"
);

define_feature!(
    AC52,
    ac_52,
    "AC_52"
);

feature_registry!(
    AC1, AC2, AC3, AC4, AC5, AC6,
    AC7, AC8, AC9, AC10, AC11, AC12,
    AC14, AC15, AC16, AC17, AC18, AC19, AC20,
    AC21, AC22, AC23, AC24, AC25, AC26, AC27,
    AC28, AC29, AC30, AC31, AC32, AC33, AC34,
    AC35, AC36, AC37, AC38, AC39, AC40,
    AC52, // Not in HCTSA used for weekly so it compares with 52 weeks before the correlation
);