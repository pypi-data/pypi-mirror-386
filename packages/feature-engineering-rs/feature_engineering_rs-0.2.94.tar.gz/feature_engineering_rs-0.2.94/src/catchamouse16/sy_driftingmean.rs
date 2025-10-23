use crate::helpers::common::{mean_f, min_f, var_f, zscore_norm2_f};

pub fn sy_driftingmean50_min(y: &[f64], normalize: bool) -> f64 {
    
    if y.iter().any(|&val| val.is_nan()) {
        return f64::NAN;
    }

    let data = if normalize {
        zscore_norm2_f(y)
    } else {
        y.to_vec()
    };

    let l = 50;
    let numfits = data.len() / l;
    
    if numfits == 0 {
        return f64::NAN;
    }
    
    // Create segments of length l
    let mut z: Vec<Vec<f64>> = Vec::with_capacity(numfits);
    for i in 0..numfits {
        let start = i * l;
        let end = start + l;
        z.push(data[start..end].to_vec());
    }
    
    // Calculate mean and variance for each segment
    let mut zm: Vec<f64> = Vec::with_capacity(numfits);
    let mut zv: Vec<f64> = Vec::with_capacity(numfits);
    
    for segment in &z {
        zm.push(mean_f(segment, Some("arithmetic")));
        zv.push(var_f(segment, 1));
    }
    
    let meanvar = mean_f(&zv, Some("arithmetic"));
    let minmean = min_f(&zm, Some(false));
    
    minmean / meanvar
}