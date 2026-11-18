// Rust acceleration backend for ssl_anomaly (Gate G3).
// Implements PhenologyBackend: robust_baseline (median + MAD * 1.4826)
// and whittaker_batch (exact pentadiagonal LDL^T Cholesky solver for d=2).

use ndarray::{Array1, Array2};
use numpy::{IntoPyArray, PyArray1, PyArray2, PyReadonlyArray2, PyReadonlyArray3};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyModule;

const MAD_SCALE: f64 = 1.4826;

fn median_sorted(sorted: &[f64]) -> f64 {
    let n = sorted.len();
    if n == 0 {
        f64::NAN
    } else if n % 2 == 1 {
        sorted[n / 2]
    } else {
        0.5 * (sorted[n / 2 - 1] + sorted[n / 2])
    }
}

fn col_median_mad(values: &mut Vec<f64>, min_n: usize) -> (f64, f64) {
    if values.len() < min_n || values.is_empty() {
        return (f64::NAN, f64::NAN);
    }
    values.sort_by(|a, b| a.total_cmp(b));
    let med = median_sorted(values);
    for v in values.iter_mut() {
        *v = (*v - med).abs();
    }
    values.sort_by(|a, b| a.total_cmp(b));
    let mad = median_sorted(values);
    (med, mad * MAD_SCALE)
}

/// Exact symmetric pentadiagonal LDL^T solver for (diag(w) + lam * D^T D) z = w * y
/// with second-order difference matrix D (d = 2).
fn whittaker_d2_single(y: &[f64], w: &[f64], lam: f64) -> Vec<f64> {
    let n = y.len();
    if n == 0 {
        return Vec::new();
    }
    let mut a0 = vec![0.0_f64; n];
    let mut rhs = vec![0.0_f64; n];
    for i in 0..n {
        if y[i].is_finite() && w[i].is_finite() {
            a0[i] = w[i];
            rhs[i] = w[i] * y[i];
        }
    }
    if n == 1 {
        return vec![if a0[0] != 0.0 { rhs[0] / a0[0] } else { 0.0 }];
    }

    let mut a1 = vec![0.0_f64; n - 1];
    let mut a2 = vec![0.0_f64; n.saturating_sub(2)];

    if n >= 3 && lam != 0.0 {
        for k in 0..(n - 2) {
            a0[k] += lam;
            a0[k + 1] += 4.0 * lam;
            a0[k + 2] += lam;
            a1[k] -= 2.0 * lam;
            a1[k + 1] -= 2.0 * lam;
            a2[k] += lam;
        }
    }

    let mut d = vec![0.0_f64; n];
    let mut l1 = vec![0.0_f64; n];
    let mut l2 = vec![0.0_f64; n];
    let mut u = vec![0.0_f64; n];

    for i in 0..n {
        if i >= 2 {
            l2[i] = a2[i - 2] / d[i - 2];
        }
        if i == 1 {
            l1[1] = a1[0] / d[0];
        } else if i >= 2 {
            l1[i] = (a1[i - 1] - l2[i] * d[i - 2] * l1[i - 1]) / d[i - 1];
        }
        let mut diag = a0[i];
        if i >= 1 {
            diag -= l1[i] * l1[i] * d[i - 1];
        }
        if i >= 2 {
            diag -= l2[i] * l2[i] * d[i - 2];
        }
        d[i] = if diag.abs() < 1e-30 { 1e-30 } else { diag };

        let mut s = rhs[i];
        if i >= 1 {
            s -= l1[i] * u[i - 1];
        }
        if i >= 2 {
            s -= l2[i] * u[i - 2];
        }
        u[i] = s;
    }

    let mut z = vec![0.0_f64; n];
    for i in (0..n).rev() {
        let mut val = u[i] / d[i];
        if i + 1 < n {
            val -= l1[i + 1] * z[i + 1];
        }
        if i + 2 < n {
            val -= l2[i + 2] * z[i + 2];
        }
        z[i] = val;
    }
    z
}

fn as_f64_array<'py>(py: Python<'py>, obj: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
    let np = PyModule::import_bound(py, "numpy")?;
    let dtype = np.getattr("float64")?;
    np.call_method1("asarray", (obj, dtype))
}

fn robust_baseline_3d_impl<'py>(
    py: Python<'py>,
    x_obj: &Bound<'py, PyAny>,
    min_n: usize,
) -> PyResult<(Bound<'py, PyArray2<f64>>, Bound<'py, PyArray2<f64>>)> {
    let x_f64 = as_f64_array(py, x_obj)?;
    let ndim: usize = x_f64.getattr("ndim")?.extract()?;
    if ndim != 3 {
        let shape: Bound<'py, PyAny> = x_f64.getattr("shape")?;
        return Err(PyValueError::new_err(format!(
            "expected 3-D X (cycles, bins, bands); got shape {}",
            shape
        )));
    }
    let x_ro: PyReadonlyArray3<'py, f64> = x_f64.extract()?;
    let arr = x_ro.as_array();
    let (n_cycles, n_bins, n_bands) = (arr.shape()[0], arr.shape()[1], arr.shape()[2]);

    let mut med = Array2::<f64>::from_elem((n_bins, n_bands), f64::NAN);
    let mut scale = Array2::<f64>::from_elem((n_bins, n_bands), f64::NAN);
    let mut buf = Vec::with_capacity(n_cycles);

    for b in 0..n_bins {
        for d in 0..n_bands {
            buf.clear();
            for c in 0..n_cycles {
                let v = arr[[c, b, d]];
                if v.is_finite() {
                    buf.push(v);
                }
            }
            let (m, s) = col_median_mad(&mut buf, min_n);
            med[[b, d]] = m;
            scale[[b, d]] = s;
        }
    }
    Ok((med.into_pyarray_bound(py), scale.into_pyarray_bound(py)))
}

fn whittaker_batch_impl<'py>(
    py: Python<'py>,
    y_obj: &Bound<'py, PyAny>,
    w_obj: &Bound<'py, PyAny>,
    lam: f64,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let np = PyModule::import_bound(py, "numpy")?;
    let mut y_f64 = as_f64_array(py, y_obj)?;
    let mut w_f64 = as_f64_array(py, w_obj)?;
    let y_ndim: usize = y_f64.getattr("ndim")?.extract()?;
    if y_ndim == 1 {
        y_f64 = np.call_method1("atleast_2d", (y_f64,))?;
        w_f64 = np.call_method1("atleast_2d", (w_f64,))?;
    }
    let y_ndim2: usize = y_f64.getattr("ndim")?.extract()?;
    let w_ndim2: usize = w_f64.getattr("ndim")?.extract()?;
    if y_ndim2 != 2 || w_ndim2 != 2 {
        return Err(PyValueError::new_err("expected 1-D or 2-D y and w arrays"));
    }

    let y_ro: PyReadonlyArray2<'py, f64> = y_f64.extract()?;
    let w_ro: PyReadonlyArray2<'py, f64> = w_f64.extract()?;
    let y_arr = y_ro.as_array();
    let w_arr = w_ro.as_array();
    if y_arr.shape() != w_arr.shape() {
        return Err(PyValueError::new_err(
            "y and w must have matching shapes in whittaker_batch",
        ));
    }
    let (batch, t_len) = (y_arr.shape()[0], y_arr.shape()[1]);
    let mut out = Array2::<f64>::zeros((batch, t_len));
    let mut y_buf = vec![0.0_f64; t_len];
    let mut w_buf = vec![0.0_f64; t_len];

    for b in 0..batch {
        for t in 0..t_len {
            y_buf[t] = y_arr[[b, t]];
            w_buf[t] = w_arr[[b, t]];
        }
        let smoothed = whittaker_d2_single(&y_buf, &w_buf, lam);
        for (t, val) in smoothed.into_iter().enumerate() {
            out[[b, t]] = val;
        }
    }
    Ok(out.into_pyarray_bound(py))
}

/// Module-level robust_baseline supporting both 3-D (cycles, bins, bands) and 2-D (samples, features).
#[pyfunction]
#[pyo3(signature = (x, min_n=5))]
fn robust_baseline<'py>(
    py: Python<'py>,
    x: &Bound<'py, PyAny>,
    min_n: usize,
) -> PyResult<(PyObject, PyObject)> {
    let x_f64 = as_f64_array(py, x)?;
    let ndim: usize = x_f64.getattr("ndim")?.extract()?;
    if ndim == 3 {
        let (m, s) = robust_baseline_3d_impl(py, &x_f64, min_n)?;
        return Ok((m.into_py(py), s.into_py(py)));
    }
    if ndim == 2 {
        let x_ro: PyReadonlyArray2<'py, f64> = x_f64.extract()?;
        let arr = x_ro.as_array();
        let (n, m) = (arr.shape()[0], arr.shape()[1]);
        let mut med = Array1::<f64>::from_elem(m, f64::NAN);
        let mut scale = Array1::<f64>::from_elem(m, f64::NAN);
        let mut buf = Vec::with_capacity(n);
        for j in 0..m {
            buf.clear();
            for i in 0..n {
                let v = arr[[i, j]];
                if v.is_finite() {
                    buf.push(v);
                }
            }
            let (mj, sj) = col_median_mad(&mut buf, min_n);
            med[j] = mj;
            scale[j] = sj;
        }
        let m_py: Bound<'py, PyArray1<f64>> = med.into_pyarray_bound(py);
        let s_py: Bound<'py, PyArray1<f64>> = scale.into_pyarray_bound(py);
        return Ok((m_py.into_py(py), s_py.into_py(py)));
    }
    Err(PyValueError::new_err(
        "expected 2-D or 3-D array for robust_baseline",
    ))
}

/// Module-level batched Whittaker smoother (d=2).
#[pyfunction]
fn whittaker_batch<'py>(
    py: Python<'py>,
    y: &Bound<'py, PyAny>,
    w: &Bound<'py, PyAny>,
    lam: f64,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    whittaker_batch_impl(py, y, w, lam)
}

/// PhenologyBackend-compatible Rust backend class used by `ssl_anomaly.backends.get_backend("rust")`.
#[pyclass]
pub struct RustBackend {
    #[pyo3(get)]
    pub name: String,
}

#[pymethods]
impl RustBackend {
    #[new]
    pub fn new() -> Self {
        Self {
            name: "rust".to_string(),
        }
    }

    pub fn whittaker_batch<'py>(
        &self,
        py: Python<'py>,
        y: &Bound<'py, PyAny>,
        w: &Bound<'py, PyAny>,
        lam: f64,
    ) -> PyResult<Bound<'py, PyArray2<f64>>> {
        whittaker_batch_impl(py, y, w, lam)
    }

    #[pyo3(signature = (X, min_n=5))]
    #[allow(non_snake_case)]
    pub fn robust_baseline<'py>(
        &self,
        py: Python<'py>,
        X: &Bound<'py, PyAny>,
        min_n: usize,
    ) -> PyResult<(Bound<'py, PyArray2<f64>>, Bound<'py, PyArray2<f64>>)> {
        robust_baseline_3d_impl(py, X, min_n)
    }
}

#[pymodule]
fn ssl_anomaly_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RustBackend>()?;
    m.add_function(wrap_pyfunction!(robust_baseline, m)?)?;
    m.add_function(wrap_pyfunction!(whittaker_batch, m)?)?;
    Ok(())
}
