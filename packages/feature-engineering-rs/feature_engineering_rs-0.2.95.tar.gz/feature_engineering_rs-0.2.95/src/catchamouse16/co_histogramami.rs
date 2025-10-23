use crate::catch22::co_auto_corr::co_histogram_ami_even;

pub fn co_histogram_ami_even_10_1(y: &[f64], normalize: bool) -> f64 {
    co_histogram_ami_even(y, 10, 1, normalize)
}

pub fn co_histogram_ami_even_10_3(y: &[f64], normalize: bool) -> f64 {
    co_histogram_ami_even(y, 10, 3, normalize)
}

pub fn co_histogram_ami_even_2_3(y: &[f64], normalize: bool) -> f64 {
    co_histogram_ami_even(y, 2, 3, normalize)
}
