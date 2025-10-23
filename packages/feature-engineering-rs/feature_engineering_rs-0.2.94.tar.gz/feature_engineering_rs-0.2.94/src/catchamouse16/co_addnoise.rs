use crate::helpers::common::{linspace_f, zscore_norm2_f};
use crate::catchamouse16::co_histogramami::co_histogram_ami_even_10_1;

// GSL FFI bindings
#[repr(C)]
struct GslRngType {
    _private: [u8; 0],
}

#[repr(C)]
struct GslRng {
    _private: [u8; 0],
}

#[link(name = "gsl")]
extern "C" {
    static gsl_rng_mt19937: *const GslRngType;
    
    fn gsl_rng_env_setup();
    fn gsl_rng_alloc(t: *const GslRngType) -> *mut GslRng;
    fn gsl_rng_set(r: *mut GslRng, seed: u64);
    fn gsl_rng_free(r: *mut GslRng);
    fn gsl_ran_gaussian_ziggurat(r: *mut GslRng, sigma: f64) -> f64;
}

pub fn co_addnoise_1_even_10_ami_at_10(y: &[f64], normalize: bool) -> f64 {
    if y.iter().any(|&val| val.is_nan()) {
        return f64::NAN;
    }

    let size = y.len();
    let data = if normalize {
        zscore_norm2_f(y)
    } else {
        y.to_vec()
    };

    unsafe {
        // Initialize GSL RNG
        gsl_rng_env_setup();
        let rng = gsl_rng_alloc(gsl_rng_mt19937);
        if rng.is_null() {
            return f64::NAN;
        }
        
        let seed: u64 = 0;
        gsl_rng_set(rng, seed);

        // Generate noise using GSL
        let noise: Vec<f64> = (0..size)
            .map(|_| gsl_ran_gaussian_ziggurat(rng, 1.0))
            .collect();

        let num_repeats = 50;
        let noise_range = linspace_f(0.0, 3.0, num_repeats);

        let mut amis = vec![0.0; num_repeats];
        let mut yn = vec![0.0; size];

        for i in 0..num_repeats {
            for j in 0..size {
                yn[j] = data[j] + (noise_range[i] * noise[j]);
            }

            amis[i] = co_histogram_ami_even_10_1(&yn, false);

            if amis[i].is_nan() {
                gsl_rng_free(rng);
                return f64::NAN;
            }
        }

        // Find the first index where noise_range >= 1.0
        let result = (0..num_repeats)
            .find(|&i| noise_range[i] >= 1.0)
            .map(|i| {
                amis[i]
            })
            .unwrap_or(f64::NAN);

        // Clean up GSL RNG
        gsl_rng_free(rng);

        result
    }
}