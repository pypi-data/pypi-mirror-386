use crate::catch22::histcounts::histcounts;
use crate::{define_feature, feature_registry};
/// DN_HistogramAsymmetry - Measures of distributional asymmetry
///
/// Measures the asymmetry of the histogram distribution of the input data vector.
/// Returns specific asymmetry measure based on the measure_name parameter.
///
/// # Arguments
///
/// * `y` - The input data vector (should be z-scored)
/// * `nbins` - The number of bins to use in the histogram
/// * `measure_name` - Which asymmetry measure to return
///
/// # Returns
///
/// The requested asymmetry measure as f64
/// Returns NaN if the input contains NaN or infinite values.
fn dn_histogramasymmetry(y: &[f64], nbins: usize, measure_name: &str) -> f64 {
    // NaN check
    if y.iter().any(|&val| val.is_nan() || val.is_infinite()) {
        return f64::NAN;
    }

    // Separate positive and negative values
    let y_pos: Vec<f64> = y.iter().filter(|&&val| val > 0.0).copied().collect();
    let y_neg: Vec<f64> = y.iter().filter(|&&val| val < 0.0).copied().collect();
    
    // Count non-zero values for normalization
    let n_nonzero = y.iter().filter(|&&val| val != 0.0).count() as f64;
    
    if n_nonzero == 0.0 {
        return 0.0;
    }

    // Calculate density diff first (this matches)
    let density_diff = y_pos.len() as f64 - y_neg.len() as f64;

    // Compute histograms for positive and negative values
    let (counts_pos, bin_edges_pos) = if !y_pos.is_empty() {
        histcounts(&y_pos, nbins)
    } else {
        (vec![0; nbins], vec![])
    };
    
    let (counts_neg, bin_edges_neg) = if !y_neg.is_empty() {
        histcounts(&y_neg, nbins)
    } else {
        (vec![0; nbins], vec![])
    };

    // Normalize by total non-zero counts (converting i32 to f64)
    let p_pos: Vec<f64> = counts_pos.iter().map(|&c| c as f64 / n_nonzero).collect();
    let p_neg: Vec<f64> = counts_neg.iter().map(|&c| c as f64 / n_nonzero).collect();

    // Compute bin centers from bin edges
    let bin_centers_pos: Vec<f64> = if bin_edges_pos.len() > 1 {
        (0..nbins).map(|i| {
            (bin_edges_pos[i] + bin_edges_pos[i + 1]) / 2.0
        }).collect()
    } else {
        vec![]
    };
    
    let bin_centers_neg: Vec<f64> = if bin_edges_neg.len() > 1 {
        (0..nbins).map(|i| {
            (bin_edges_neg[i] + bin_edges_neg[i + 1]) / 2.0
        }).collect()
    } else {
        vec![]
    };

    // Find maximum probabilities
    let mode_prob_pos = if !p_pos.is_empty() {
        *p_pos.iter().max_by(|a, b| a.partial_cmp(b).unwrap()).unwrap()
    } else {
        0.0
    };
    
    let mode_prob_neg = if !p_neg.is_empty() {
        *p_neg.iter().max_by(|a, b| a.partial_cmp(b).unwrap()).unwrap()
    } else {
        0.0
    };
    
    let mode_diff = mode_prob_pos - mode_prob_neg;

    // Find positions of maximum probabilities
    let pos_mode = if !bin_centers_pos.is_empty() && mode_prob_pos > 0.0 {
        let matching_centers: Vec<f64> = p_pos.iter()
            .enumerate()
            .filter(|(_, &p)| (p - mode_prob_pos).abs() < 1e-10)  // Use epsilon comparison
            .map(|(i, _)| bin_centers_pos[i])
            .collect();
        
        if !matching_centers.is_empty() {
            matching_centers.iter().sum::<f64>() / matching_centers.len() as f64
        } else {
            0.0
        }
    } else {
        0.0
    };

    let neg_mode = if !bin_centers_neg.is_empty() && mode_prob_neg > 0.0 {
        let matching_centers: Vec<f64> = p_neg.iter()
            .enumerate()
            .filter(|(_, &p)| (p - mode_prob_neg).abs() < 1e-10)  // Use epsilon comparison
            .map(|(i, _)| bin_centers_neg[i])
            .collect();
        
        if !matching_centers.is_empty() {
            matching_centers.iter().sum::<f64>() / matching_centers.len() as f64
        } else {
            0.0
        }
    } else {
        0.0
    };

    let mode_asymmetry = pos_mode + neg_mode;

    // Return the requested measure
    match measure_name {
        "densityDiff" => density_diff,
        "modeProbPos" => mode_prob_pos,
        "modeProbNeg" => mode_prob_neg,
        "modeDiff" => mode_diff,
        "posMode" => pos_mode,
        "negMode" => neg_mode,
        "modeAsymmetry" => mode_asymmetry,
        _ => f64::NAN,
    }
}

/////////////////////////////////////////////////////////////
// DN_HistogramAsymmetry_5
pub fn dn_histogramasymmetry_5_densitydiff(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 5, "densityDiff")
}

pub fn dn_histogramasymmetry_5_modeprobpos(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 5, "modeProbPos")
}

pub fn dn_histogramasymmetry_5_modeprobneg(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 5, "modeProbNeg")
}

pub fn dn_histogramasymmetry_5_modediff(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 5, "modeDiff")
}

pub fn dn_histogramasymmetry_5_posmode(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 5, "posMode")
}

pub fn dn_histogramasymmetry_5_negmode(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 5, "negMode")
}

pub fn dn_histogramasymmetry_5_modeasymmetry(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 5, "modeAsymmetry")
}

/////////////////////////////////////////////////////////////
// DN_HistogramAsymmetry_11
pub fn dn_histogramasymmetry_11_densitydiff(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 11, "densityDiff")
}

pub fn dn_histogramasymmetry_11_modeprobpos(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 11, "modeProbPos")
}

pub fn dn_histogramasymmetry_11_modeprobneg(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 11, "modeProbNeg")
}

pub fn dn_histogramasymmetry_11_modediff(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 11, "modeDiff")
}

pub fn dn_histogramasymmetry_11_posmode(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 11, "posMode")
}

pub fn dn_histogramasymmetry_11_negmode(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 11, "negMode")
}

pub fn dn_histogramasymmetry_11_modeasymmetry(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 11, "modeAsymmetry")
}

/////////////////////////////////////////////////////////////
// DN_HistogramAsymmetry_15
pub fn dn_histogramasymmetry_15_densitydiff(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 15, "densityDiff")
}

pub fn dn_histogramasymmetry_15_modeprobpos(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 15, "modeProbPos")
}

pub fn dn_histogramasymmetry_15_modeprobneg(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 15, "modeProbNeg")
}

pub fn dn_histogramasymmetry_15_modediff(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 15, "modeDiff")
}

pub fn dn_histogramasymmetry_15_posmode(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 15, "posMode")
}

pub fn dn_histogramasymmetry_15_negmode(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 15, "negMode")
}

pub fn dn_histogramasymmetry_15_modeasymmetry(y: &[f64]) -> f64 {
    dn_histogramasymmetry(y, 15, "modeAsymmetry")
}


// FEATURE DEFINITIONS  
define_feature!(
    DNHistogramAsymmetry5DensityDiff,
    dn_histogramasymmetry_5_densitydiff,
    "DN_HistogramAsymmetry_5_densityDiff"
);

define_feature!(
    DNHistogramAsymmetry5ModeProbPos,
    dn_histogramasymmetry_5_modeprobpos,
    "DN_HistogramAsymmetry_5_modeProbPos"
);

define_feature!(
    DNHistogramAsymmetry5ModeProbNeg,
    dn_histogramasymmetry_5_modeprobneg,
    "DN_HistogramAsymmetry_5_modeProbNeg"
);

define_feature!(
    DNHistogramAsymmetry5ModeDiff,
    dn_histogramasymmetry_5_modediff,
    "DN_HistogramAsymmetry_5_modeDiff"
);

define_feature!(
    DNHistogramAsymmetry5PosMode,
    dn_histogramasymmetry_5_posmode,
    "DN_HistogramAsymmetry_5_posMode"
);

define_feature!(
    DNHistogramAsymmetry5NegMode,
    dn_histogramasymmetry_5_negmode,
    "DN_HistogramAsymmetry_5_negMode"
);

define_feature!(
    DNHistogramAsymmetry5ModeAsymmetry,
    dn_histogramasymmetry_5_modeasymmetry,
    "DN_HistogramAsymmetry_5_modeAsymmetry"
);

define_feature!(
    DNHistogramAsymmetry11DensityDiff,
    dn_histogramasymmetry_11_densitydiff,
    "DN_HistogramAsymmetry_11_densityDiff"
);

define_feature!(
    DNHistogramAsymmetry11ModeProbPos,
    dn_histogramasymmetry_11_modeprobpos,
    "DN_HistogramAsymmetry_11_modeProbPos"
);

define_feature!(
    DNHistogramAsymmetry11ModeProbNeg,
    dn_histogramasymmetry_11_modeprobneg,
    "DN_HistogramAsymmetry_11_modeProbNeg"
);

define_feature!(
    DNHistogramAsymmetry11ModeDiff,
    dn_histogramasymmetry_11_modediff,
    "DN_HistogramAsymmetry_11_modeDiff"
);

define_feature!(
    DNHistogramAsymmetry11PosMode,
    dn_histogramasymmetry_11_posmode,
    "DN_HistogramAsymmetry_11_posMode"
);

define_feature!(
    DNHistogramAsymmetry11NegMode,
    dn_histogramasymmetry_11_negmode,
    "DN_HistogramAsymmetry_11_negMode"
);

define_feature!(
    DNHistogramAsymmetry11ModeAsymmetry,
    dn_histogramasymmetry_11_modeasymmetry,
    "DN_HistogramAsymmetry_11_modeAsymmetry"
);

define_feature!(
    DNHistogramAsymmetry15DensityDiff,
    dn_histogramasymmetry_15_densitydiff,
    "DN_HistogramAsymmetry_15_densityDiff"
);

define_feature!(
    DNHistogramAsymmetry15ModeProbPos,
    dn_histogramasymmetry_15_modeprobpos,
    "DN_HistogramAsymmetry_15_modeProbPos"
);

define_feature!(
    DNHistogramAsymmetry15ModeProbNeg,
    dn_histogramasymmetry_15_modeprobneg,
    "DN_HistogramAsymmetry_15_modeProbNeg"
);

define_feature!(
    DNHistogramAsymmetry15ModeDiff,
    dn_histogramasymmetry_15_modediff,
    "DN_HistogramAsymmetry_15_modeDiff"
);

define_feature!(
    DNHistogramAsymmetry15PosMode,
    dn_histogramasymmetry_15_posmode,
    "DN_HistogramAsymmetry_15_posMode"
);

define_feature!(
    DNHistogramAsymmetry15NegMode,
    dn_histogramasymmetry_15_negmode,
    "DN_HistogramAsymmetry_15_negMode"
);

define_feature!(
    DNHistogramAsymmetry15ModeAsymmetry,
    dn_histogramasymmetry_15_modeasymmetry,
    "DN_HistogramAsymmetry_15_modeAsymmetry"
);

// FEATURE REGISTRY
feature_registry!(
    DNHistogramAsymmetry5DensityDiff,
    DNHistogramAsymmetry5ModeProbPos,
    DNHistogramAsymmetry5ModeProbNeg,
    DNHistogramAsymmetry5ModeDiff,
    DNHistogramAsymmetry5PosMode,
    DNHistogramAsymmetry5NegMode,
    DNHistogramAsymmetry5ModeAsymmetry,
    DNHistogramAsymmetry11DensityDiff,
    DNHistogramAsymmetry11ModeProbPos,
    DNHistogramAsymmetry11ModeProbNeg,
    DNHistogramAsymmetry11ModeDiff,
    DNHistogramAsymmetry11PosMode,
    DNHistogramAsymmetry11NegMode,
    DNHistogramAsymmetry11ModeAsymmetry,
    DNHistogramAsymmetry15DensityDiff,
    DNHistogramAsymmetry15ModeProbPos,
    DNHistogramAsymmetry15ModeProbNeg,
    DNHistogramAsymmetry15ModeDiff,
    DNHistogramAsymmetry15PosMode,
    DNHistogramAsymmetry15NegMode,
    DNHistogramAsymmetry15ModeAsymmetry,
);
