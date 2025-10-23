//! Catchamouse16 Python bindings

use pyo3::prelude::*;
use crate::catchamouse16::sy_driftingmean::sy_driftingmean50_min;
use crate::catchamouse16::sy_slidingwindow::sy_slidingwindow;
use crate::catchamouse16::st_localextrema::st_localextrema_n100_diffmaxabsmin;
use crate::catchamouse16::ph_walker::{ph_walker_momentum_5_w_momentumzcross, ph_walker_biasprop_05_01_sw_meanabsdiff};
use crate::catchamouse16::in_automutualinfostats_diff_20_gaussian_ami8::in_automutualinfostats_diff_20_gaussian_ami8;
use crate::catchamouse16::fc_looplocalsimple::fc_looplocalsimple_mean_stderr_chn;
use crate::catchamouse16::co_translateshape::{co_translateshape_circle_35_pts_statav4_m, co_translateshape_circle_35_pts_std};
use crate::catchamouse16::co_histogramami::{co_histogram_ami_even_10_1, co_histogram_ami_even_10_3, co_histogram_ami_even_2_3};
use crate::catchamouse16::co_addnoise::co_addnoise_1_even_10_ami_at_10;
use crate::catchamouse16::co_nonlinearautocorr::{ac_nl_035, ac_nl_036, ac_nl_112};
use crate::catchamouse16::dn_removepoints::dn_removepoints_absclose_05_ac2rat;
use crate::catchamouse16::sc_fluctanal::sc_fluctanal_2_dfa_50_2_logi_r2_se2;

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn sy_driftingmean50_min_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    sy_driftingmean50_min(&y, normalize.unwrap_or(false))
}

#[pyfunction]
pub fn sy_slidingwindow_f(y: Vec<f64>, window_stat: &str, across_win_stat: &str, num_seg: usize, inc_move: usize, normalize: Option<bool>) -> f64 {
    sy_slidingwindow(&y, window_stat, across_win_stat, num_seg, inc_move, normalize.unwrap_or(false))
}

#[pyfunction]
pub fn st_localextrema_n100_diffmaxabsmin_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    st_localextrema_n100_diffmaxabsmin(&y, normalize.unwrap_or(false))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn ph_walker_momentum_5_w_momentumzcross_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    ph_walker_momentum_5_w_momentumzcross(&y, normalize.unwrap_or(false))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn ph_walker_biasprop_05_01_sw_meanabsdiff_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    ph_walker_biasprop_05_01_sw_meanabsdiff(&y, normalize.unwrap_or(false))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn in_automutualinfostats_diff_20_gaussian_ami8_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    in_automutualinfostats_diff_20_gaussian_ami8(&y, normalize.unwrap_or(false))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn fc_looplocalsimple_mean_stderr_chn_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    fc_looplocalsimple_mean_stderr_chn(&y, normalize.unwrap_or(false))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn co_translateshape_circle_35_pts_statav4_m_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    co_translateshape_circle_35_pts_statav4_m(&y, normalize.unwrap_or(false))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn co_translateshape_circle_35_pts_std_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    co_translateshape_circle_35_pts_std(&y, normalize.unwrap_or(false))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn co_histogram_ami_even_10_1_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    co_histogram_ami_even_10_1(&y, normalize.unwrap_or(true))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn co_histogram_ami_even_10_3_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    co_histogram_ami_even_10_3(&y, normalize.unwrap_or(true))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn co_histogram_ami_even_2_3_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    co_histogram_ami_even_2_3(&y, normalize.unwrap_or(true))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn co_addnoise_1_even_10_ami_at_10_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    co_addnoise_1_even_10_ami_at_10(&y, normalize.unwrap_or(true))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn ac_nl_035_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    ac_nl_035(&y, normalize.unwrap_or(true))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn ac_nl_036_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    ac_nl_036(&y, normalize.unwrap_or(true))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn ac_nl_112_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    ac_nl_112(&y, normalize.unwrap_or(true))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn dn_removepoints_absclose_05_ac2rat_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    dn_removepoints_absclose_05_ac2rat(&y, normalize.unwrap_or(true))
}

#[pyfunction]
#[pyo3(signature = (y, normalize=None))]
pub fn sc_fluctanal_2_dfa_50_2_logi_r2_se2_f(y: Vec<f64>, normalize: Option<bool>) -> f64 {
    sc_fluctanal_2_dfa_50_2_logi_r2_se2(&y, normalize.unwrap_or(true))
}
