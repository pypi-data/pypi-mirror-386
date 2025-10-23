use crate::{define_feature, feature_registry};
use crate::helpers::common::{max_f, min_f, linspace_f, quantile_f};
use crate::catch22::histcounts::{histbinassign, histcount_edges};

pub fn co_histogram_ami(y: &[f64], method: &str, num_bins: usize, tau: usize) -> f64 {
    // NaN and infinite check - return NaN for both
    if y.iter().any(|&val| val.is_nan() || val.is_infinite()) {
        return f64::NAN;
    }

    let size = y.len();

    if size <= 1 || tau >= size {
        return f64::NAN;
    }

    // Form time-delay vectors
    let mut y1 = Vec::with_capacity(size - tau);
    let mut y2 = Vec::with_capacity(size - tau);

    for i in 0..size - tau {
        y1.push(y[i]);
        y2.push(y[i + tau]);
    }

    // Calculate bin edges based on method
    let bin_edges = match method {
        "even" => {
            let max_value = max_f(y, Some(false));
            let min_value = min_f(y, Some(false));
            
            // linspace from min to max
            let mut edges = linspace_f(min_value, max_value, num_bins + 1);
            // Add buffer to ensure all points are included
            edges[0] -= 0.1;
            edges[num_bins] += 0.1;
            edges
        }
        
        "std1" => {
            // Bins out to +/- 1 std (assuming data is normalized)
            let mut edges = linspace_f(-1.0, 1.0, num_bins + 1);
            
            let min_val = min_f(y, Some(false));
            let max_val = max_f(y, Some(false));
            
            // Add extra bins if data extends beyond ±1
            if min_val < -1.0 {
                edges.insert(0, min_val - 0.1);
            }
            if max_val > 1.0 {
                edges.push(max_val + 0.1);
            }
            edges
        }
        
        "std2" => {
            // Bins out to +/- 2 std (assuming data is normalized)
            let mut edges = linspace_f(-2.0, 2.0, num_bins + 1);
            
            let min_val = min_f(y, Some(false));
            let max_val = max_f(y, Some(false));
            
            // Add extra bins if data extends beyond ±2
            if min_val < -2.0 {
                edges.insert(0, min_val - 0.1);
            }
            if max_val > 2.0 {
                edges.push(max_val + 0.1);
            }
            edges
        }
        
        "quantiles" => {
            // Use quantiles with ~equal number in each bin
            let quantile_positions = linspace_f(0.0, 1.0, num_bins + 1);
            let mut edges: Vec<f64> = quantile_positions.iter()
                .map(|&q| quantile_f(y, q))
                .collect();
            
            // Add buffer
            edges[0] -= 0.1;
            let last_idx = edges.len() - 1;
            edges[last_idx] += 0.1;
            edges
        }
        
        _ => panic!("Unknown binning method: {}", method),
    };

    // Update num_bins in case extra bins were added (for std1/std2)
    let num_bins = bin_edges.len() - 1;

    // Count histogram bin contents
    let bins1 = histbinassign(&y1, &bin_edges);
    let bins2 = histbinassign(&y2, &bin_edges);

    // Create joint bins (linearized)
    let mut bins12 = Vec::with_capacity(size - tau);
    let mut bin_edges12 = Vec::with_capacity((num_bins + 1) * (num_bins + 1));

    for i in 0..size - tau {
        bins12.push((bins1[i] - 1) * (num_bins + 1) as i32 + bins2[i]);
    }

    for i in 0..(num_bins + 1) * (num_bins + 1) {
        bin_edges12.push(i as f64 + 1.0);
    }

    // Joint histogram
    let joint_hist_linear = histcount_edges(
        &bins12.iter().map(|&x| x as f64).collect::<Vec<f64>>(),
        &bin_edges12,
    );

    // Transfer to 2D histogram (no last bin, as in original implementation)
    let mut pij = vec![vec![0.0; num_bins]; num_bins];
    let mut sum_bins = 0;

    for i in 0..num_bins {
        for j in 0..num_bins {
            pij[j][i] = joint_hist_linear[i * (num_bins + 1) + j] as f64;
            sum_bins += joint_hist_linear[i * (num_bins + 1) + j];
        }
    }

    // Normalize joint distribution
    if sum_bins == 0 {
        return f64::NAN;
    }
    
    for i in 0..num_bins {
        for j in 0..num_bins {
            pij[j][i] /= sum_bins as f64;
        }
    }

    // Compute marginal distributions
    let mut pi = vec![0.0; num_bins];
    let mut pj = vec![0.0; num_bins];

    for i in 0..num_bins {
        for j in 0..num_bins {
            pi[i] += pij[i][j];
            pj[j] += pij[i][j];
        }
    }

    // Calculate automutual information
    let mut ami = 0.0;
    for i in 0..num_bins {
        for j in 0..num_bins {
            if pij[i][j] > 0.0 && pi[i] > 0.0 && pj[j] > 0.0 {
                ami += pij[i][j] * (pij[i][j] / (pj[j] * pi[i])).ln();
            }
        }
    }

    ami
}

// STD1
pub fn co_histogram_ami_std1_2bin_ami1(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 2, 1)
}

pub fn co_histogram_ami_std1_2bin_ami2(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 2, 2)
}

pub fn co_histogram_ami_std1_2bin_ami3(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 2, 3)
}

pub fn co_histogram_ami_std1_2bin_ami4(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 2, 4)
}

pub fn co_histogram_ami_std1_2bin_ami5(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 2, 5)
}

pub fn co_histogram_ami_std1_5bin_ami1(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 5, 1)
}

pub fn co_histogram_ami_std1_5bin_ami2(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 5, 2)
}

pub fn co_histogram_ami_std1_5bin_ami3(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 5, 3)
}

pub fn co_histogram_ami_std1_5bin_ami4(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 5, 4)
}

pub fn co_histogram_ami_std1_5bin_ami5(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 5, 5)
}

pub fn co_histogram_ami_std1_10bin_ami1(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 10, 1)
}

pub fn co_histogram_ami_std1_10bin_ami2(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 10, 2)
}

pub fn co_histogram_ami_std1_10bin_ami3(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 10, 3)
}

pub fn co_histogram_ami_std1_10bin_ami4(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 10, 4)
}

pub fn co_histogram_ami_std1_10bin_ami5(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std1", 10, 5)
}

// STD2
pub fn co_histogram_ami_std2_2bin_ami1(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 2, 1)
}

pub fn co_histogram_ami_std2_2bin_ami2(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 2, 2)
}

pub fn co_histogram_ami_std2_2bin_ami3(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 2, 3)
}

pub fn co_histogram_ami_std2_2bin_ami4(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 2, 4)
}

pub fn co_histogram_ami_std2_2bin_ami5(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 2, 5)
}

pub fn co_histogram_ami_std2_5bin_ami1(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 5, 1)
}

pub fn co_histogram_ami_std2_5bin_ami2(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 5, 2)
}

pub fn co_histogram_ami_std2_5bin_ami3(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 5, 3)
}

pub fn co_histogram_ami_std2_5bin_ami4(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 5, 4)
}

pub fn co_histogram_ami_std2_5bin_ami5(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 5, 5)
}

pub fn co_histogram_ami_std2_10bin_ami1(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 10, 1)
}

pub fn co_histogram_ami_std2_10bin_ami2(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 10, 2)
}

pub fn co_histogram_ami_std2_10bin_ami3(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 10, 3)
}

pub fn co_histogram_ami_std2_10bin_ami4(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 10, 4)
}

pub fn co_histogram_ami_std2_10bin_ami5(y: &[f64]) -> f64 {
    co_histogram_ami(y, "std2", 10, 5)
}


// EVEN
pub fn co_histogram_ami_even_2bin_ami1(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 2, 1)
}

pub fn co_histogram_ami_even_2bin_ami2(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 2, 2)
}

pub fn co_histogram_ami_even_2bin_ami3(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 2, 3)
}

pub fn co_histogram_ami_even_2bin_ami4(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 2, 4)
}

pub fn co_histogram_ami_even_2bin_ami5(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 2, 5)
}

pub fn co_histogram_ami_even_5bin_ami1(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 5, 1)
}

pub fn co_histogram_ami_even_5bin_ami2(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 5, 2)
}

pub fn co_histogram_ami_even_5bin_ami3(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 5, 3)
}

pub fn co_histogram_ami_even_5bin_ami4(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 5, 4)
}

pub fn co_histogram_ami_even_5bin_ami5(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 5, 5)
}

pub fn co_histogram_ami_even_10bin_ami1(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 10, 1)
}

pub fn co_histogram_ami_even_10bin_ami2(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 10, 2)
}

pub fn co_histogram_ami_even_10bin_ami3(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 10, 3)
}

pub fn co_histogram_ami_even_10bin_ami4(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 10, 4)
}

pub fn co_histogram_ami_even_10bin_ami5(y: &[f64]) -> f64 {
    co_histogram_ami(y, "even", 10, 5)
}

// Quantiles
pub fn co_histogram_ami_quantiles_2bin_ami1(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 2, 1)
}

pub fn co_histogram_ami_quantiles_2bin_ami2(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 2, 2)
}

pub fn co_histogram_ami_quantiles_2bin_ami3(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 2, 3)
}

pub fn co_histogram_ami_quantiles_2bin_ami4(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 2, 4)
}

pub fn co_histogram_ami_quantiles_2bin_ami5(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 2, 5)
}

pub fn co_histogram_ami_quantiles_5bin_ami1(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 5, 1)
}

pub fn co_histogram_ami_quantiles_5bin_ami2(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 5, 2)
}

pub fn co_histogram_ami_quantiles_5bin_ami3(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 5, 3)
}

pub fn co_histogram_ami_quantiles_5bin_ami4(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 5, 4)
}

pub fn co_histogram_ami_quantiles_5bin_ami5(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 5, 5)
}

pub fn co_histogram_ami_quantiles_10bin_ami1(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 10, 1)
}

pub fn co_histogram_ami_quantiles_10bin_ami2(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 10, 2)
}

pub fn co_histogram_ami_quantiles_10bin_ami3(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 10, 3)
}

pub fn co_histogram_ami_quantiles_10bin_ami4(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 10, 4)
}

pub fn co_histogram_ami_quantiles_10bin_ami5(y: &[f64]) -> f64 {
    co_histogram_ami(y, "quantiles", 10, 5)
}

define_feature!(
    COHistogramAMISTD121,
    co_histogram_ami_std1_2bin_ami1,
    "CO_HistogramAMI_std1_2bin_ami1"
);

define_feature!(
    COHistogramAMISTD122,
    co_histogram_ami_std1_2bin_ami2,
    "CO_HistogramAMI_std1_2bin_ami2"
);

define_feature!(
    COHistogramAMISTD123,
    co_histogram_ami_std1_2bin_ami3,
    "CO_HistogramAMI_std1_2bin_ami3"
);

define_feature!(
    COHistogramAMISTD124,
    co_histogram_ami_std1_2bin_ami4,
    "CO_HistogramAMI_std1_2bin_ami4"
);

define_feature!(
    COHistogramAMISTD125,
    co_histogram_ami_std1_2bin_ami5,
    "CO_HistogramAMI_std1_2bin_ami5"
);

define_feature!(
    COHistogramAMISTD151,
    co_histogram_ami_std1_5bin_ami1,
    "CO_HistogramAMI_std1_5bin_ami1"
);

define_feature!(
    COHistogramAMISTD152,
    co_histogram_ami_std1_5bin_ami2,
    "CO_HistogramAMI_std1_5bin_ami2"
);

define_feature!(
    COHistogramAMISTD153,
    co_histogram_ami_std1_5bin_ami3,
    "CO_HistogramAMI_std1_5bin_ami3"
);

define_feature!(
    COHistogramAMISTD154,
    co_histogram_ami_std1_5bin_ami4,
    "CO_HistogramAMI_std1_5bin_ami4"
);

define_feature!(
    COHistogramAMISTD155,
    co_histogram_ami_std1_5bin_ami5,
    "CO_HistogramAMI_std1_5bin_ami5"
);

define_feature!(
    COHistogramAMISTD1101,
    co_histogram_ami_std1_10bin_ami1,
    "CO_HistogramAMI_std1_10bin_ami1"
);

define_feature!(
    COHistogramAMISTD1102,
    co_histogram_ami_std1_10bin_ami2,
    "CO_HistogramAMI_std1_10bin_ami2"
);

define_feature!(
    COHistogramAMISTD1103,
    co_histogram_ami_std1_10bin_ami3,
    "CO_HistogramAMI_std1_10bin_ami3"
);

define_feature!(
    COHistogramAMISTD1104,
    co_histogram_ami_std1_10bin_ami4,
    "CO_HistogramAMI_std1_10bin_ami4"
);

define_feature!(
    COHistogramAMISTD1105,
    co_histogram_ami_std1_10bin_ami5,
    "CO_HistogramAMI_std1_10bin_ami5"
);

define_feature!(
    COHistogramAMISTD221,
    co_histogram_ami_std2_2bin_ami1,
    "CO_HistogramAMI_std2_2bin_ami1"
);

define_feature!(
    COHistogramAMISTD222,
    co_histogram_ami_std2_2bin_ami2,
    "CO_HistogramAMI_std2_2bin_ami2"
);

define_feature!(
    COHistogramAMISTD223,
    co_histogram_ami_std2_2bin_ami3,
    "CO_HistogramAMI_std2_2bin_ami3"
);

define_feature!(
    COHistogramAMISTD224,
    co_histogram_ami_std2_2bin_ami4,
    "CO_HistogramAMI_std2_2bin_ami4"
);

define_feature!(
    COHistogramAMISTD225,
    co_histogram_ami_std2_2bin_ami5,
    "CO_HistogramAMI_std2_2bin_ami5"
);

define_feature!(
    COHistogramAMISTD251,
    co_histogram_ami_std2_5bin_ami1,
    "CO_HistogramAMI_std2_5bin_ami1"
);

define_feature!(
    COHistogramAMISTD252,
    co_histogram_ami_std2_5bin_ami2,
    "CO_HistogramAMI_std2_5bin_ami2"
);

define_feature!(
    COHistogramAMISTD253,
    co_histogram_ami_std2_5bin_ami3,
    "CO_HistogramAMI_std2_5bin_ami3"
);

define_feature!(
    COHistogramAMISTD254,
    co_histogram_ami_std2_5bin_ami4,
    "CO_HistogramAMI_std2_5bin_ami4"
);

define_feature!(
    COHistogramAMISTD255,
    co_histogram_ami_std2_5bin_ami5,
    "CO_HistogramAMI_std2_5bin_ami5"
);

define_feature!(
    COHistogramAMISTD2101,
    co_histogram_ami_std2_10bin_ami1,
    "CO_HistogramAMI_std2_10bin_ami1"
);

define_feature!(
    COHistogramAMISTD2102,
    co_histogram_ami_std2_10bin_ami2,
    "CO_HistogramAMI_std2_10bin_ami2"
);

define_feature!(
    COHistogramAMISTD2103,
    co_histogram_ami_std2_10bin_ami3,
    "CO_HistogramAMI_std2_10bin_ami3"
);

define_feature!(
    COHistogramAMISTD2104,
    co_histogram_ami_std2_10bin_ami4,
    "CO_HistogramAMI_std2_10bin_ami4"
);

define_feature!(
    COHistogramAMISTD2105,
    co_histogram_ami_std2_10bin_ami5,
    "CO_HistogramAMI_std2_10bin_ami5"
);

define_feature!(
    COHistogramAMIEven21,
    co_histogram_ami_even_2bin_ami1,
    "CO_HistogramAMI_even_2bin_ami1"
);

define_feature!(
    COHistogramAMIEven22,
    co_histogram_ami_even_2bin_ami2,
    "CO_HistogramAMI_quantiles_10bin_ami2"
);

define_feature!(
    COHistogramAMIEven23,
    co_histogram_ami_even_2bin_ami3,
    "CO_HistogramAMI_even_2bin_ami3"
);

define_feature!(
    COHistogramAMIEven24,
    co_histogram_ami_even_2bin_ami4,
    "CO_HistogramAMI_even_2bin_ami4"
);

define_feature!(
    COHistogramAMIEven25,
    co_histogram_ami_even_2bin_ami5,
    "CO_HistogramAMI_even_2bin_ami5"
);

define_feature!(
    COHistogramAMIEven51,
    co_histogram_ami_even_5bin_ami1,
    "CO_HistogramAMI_even_5bin_ami1"
);

define_feature!(
    COHistogramAMIEven52,
    co_histogram_ami_even_5bin_ami2,
    "CO_HistogramAMI_even_5bin_ami2"
);

define_feature!(
    COHistogramAMIEven53,
    co_histogram_ami_even_5bin_ami3,
    "CO_HistogramAMI_even_5bin_ami3"
);

define_feature!(
    COHistogramAMIEven54,
    co_histogram_ami_even_5bin_ami4,
    "CO_HistogramAMI_even_5bin_ami4"
);

define_feature!(
    COHistogramAMIEven55,
    co_histogram_ami_even_5bin_ami5,
    "CO_HistogramAMI_even_5bin_ami5"
);

define_feature!(
    COHistogramAMIEven101,
    co_histogram_ami_even_10bin_ami1,
    "CO_HistogramAMI_even_10bin_ami1"
);

define_feature!(
    COHistogramAMIEven102,
    co_histogram_ami_even_10bin_ami2,
    "CO_HistogramAMI_even_10bin_ami2"
);

define_feature!(
    COHistogramAMIEven103,
    co_histogram_ami_even_10bin_ami3,
    "CO_HistogramAMI_even_10bin_ami3"
);

define_feature!(
    COHistogramAMIEven104,
    co_histogram_ami_even_10bin_ami4,
    "CO_HistogramAMI_even_10bin_ami4"
);

define_feature!(
    COHistogramAMIEven105,
    co_histogram_ami_even_10bin_ami5,
    "CO_HistogramAMI_even_10bin_ami5"
);

define_feature!(
    COHistogramAMIQUANTILES21,
    co_histogram_ami_quantiles_2bin_ami1,
    "CO_HistogramAMI_quantiles_2bin_ami1"
);

define_feature!(
    COHistogramAMIQUANTILES22,
    co_histogram_ami_quantiles_2bin_ami2,
    "CO_HistogramAMI_quantiles_2bin_ami2"
);

define_feature!(
    COHistogramAMIQUANTILES23,
    co_histogram_ami_quantiles_2bin_ami3,
    "CO_HistogramAMI_quantiles_2bin_ami3"
);

define_feature!(
    COHistogramAMIQUANTILES24,
    co_histogram_ami_quantiles_2bin_ami4,
    "CO_HistogramAMI_quantiles_2bin_ami4"
);

define_feature!(
    COHistogramAMIQUANTILES25,
    co_histogram_ami_quantiles_2bin_ami5,
    "CO_HistogramAMI_quantiles_2bin_ami5"
);

define_feature!(
    COHistogramAMIQUANTILES51,
    co_histogram_ami_quantiles_5bin_ami1,
    "CO_HistogramAMI_quantiles_5bin_ami1"
);

define_feature!(
    COHistogramAMIQUANTILES52,
    co_histogram_ami_quantiles_5bin_ami2,
    "CO_HistogramAMI_quantiles_5bin_ami2"
);

define_feature!(
    COHistogramAMIQUANTILES53,
    co_histogram_ami_quantiles_5bin_ami3,
    "CO_HistogramAMI_quantiles_5bin_ami3"
);

define_feature!(
    COHistogramAMIQUANTILES54,
    co_histogram_ami_quantiles_5bin_ami4,
    "CO_HistogramAMI_quantiles_5bin_ami4"
);

define_feature!(
    COHistogramAMIQUANTILES55,
    co_histogram_ami_quantiles_5bin_ami5,
    "CO_HistogramAMI_quantiles_5bin_ami5"
);

define_feature!(
    COHistogramAMIQUANTILES101,
    co_histogram_ami_quantiles_10bin_ami1,
    "CO_HistogramAMI_quantiles_10bin_ami1"
);

define_feature!(
    COHistogramAMIQUANTILES102,
    co_histogram_ami_quantiles_10bin_ami2,
    "CO_HistogramAMI_quantiles_10bin_ami2"
);

define_feature!(
    COHistogramAMIQUANTILES103,
    co_histogram_ami_quantiles_10bin_ami3,
    "CO_HistogramAMI_quantiles_10bin_ami3"
);

define_feature!(
    COHistogramAMIQUANTILES104,
    co_histogram_ami_quantiles_10bin_ami4,
    "CO_HistogramAMI_quantiles_10bin_ami4"
);

define_feature!(
    COHistogramAMIQUANTILES105,
    co_histogram_ami_quantiles_10bin_ami5,
    "CO_HistogramAMI_quantiles_10bin_ami5"
);

feature_registry!(
    COHistogramAMISTD121,
    COHistogramAMISTD122,
    COHistogramAMISTD123,
    COHistogramAMISTD124,
    COHistogramAMISTD125,
    COHistogramAMISTD151,
    COHistogramAMISTD152,
    COHistogramAMISTD153,
    COHistogramAMISTD154,
    COHistogramAMISTD155,
    COHistogramAMISTD1101,
    COHistogramAMISTD1102,
    COHistogramAMISTD1103,
    COHistogramAMISTD1104,
    COHistogramAMISTD1105,
    COHistogramAMISTD221,
    COHistogramAMISTD222,
    COHistogramAMISTD223,
    COHistogramAMISTD224,
    COHistogramAMISTD225,
    COHistogramAMISTD251,
    COHistogramAMISTD252,
    COHistogramAMISTD253,
    COHistogramAMISTD254,
    COHistogramAMISTD255,
    COHistogramAMISTD2101,
    COHistogramAMISTD2102,
    COHistogramAMISTD2103,
    COHistogramAMISTD2104,
    COHistogramAMISTD2105,
    COHistogramAMIEven21,
    COHistogramAMIEven22,
    COHistogramAMIEven23,
    COHistogramAMIEven24,
    COHistogramAMIEven25,
    COHistogramAMIEven51,
    COHistogramAMIEven52,
    COHistogramAMIEven53,
    COHistogramAMIEven54,
    COHistogramAMIEven55,
    COHistogramAMIEven101,
    COHistogramAMIEven102,
    COHistogramAMIEven103,
    COHistogramAMIEven104,
    COHistogramAMIEven105,
    COHistogramAMIQUANTILES21,
    COHistogramAMIQUANTILES22,
    COHistogramAMIQUANTILES23,
    COHistogramAMIQUANTILES24,
    COHistogramAMIQUANTILES25,
    COHistogramAMIQUANTILES51,
    COHistogramAMIQUANTILES52,
    COHistogramAMIQUANTILES53,
    COHistogramAMIQUANTILES54,
    COHistogramAMIQUANTILES55,
    COHistogramAMIQUANTILES101,
    COHistogramAMIQUANTILES102,
    COHistogramAMIQUANTILES103,
    COHistogramAMIQUANTILES104,
    COHistogramAMIQUANTILES105,
);
