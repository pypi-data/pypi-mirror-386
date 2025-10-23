use pyo3::prelude::*;

mod dirs;

#[pyfunction]
fn version_info() -> PyResult<String> {
    Ok(format!("_pycmd2 v{}", env!("CARGO_PKG_VERSION")))
}

/// A Python module implemented in Rust.
#[pymodule]
fn _pycmd2(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version_info, m)?)?;

    // dirs
    m.add_function(wrap_pyfunction!(dirs::list_entries, m)?)?;
    m.add_function(wrap_pyfunction!(dirs::list_names, m)?)?;

    Ok(())
}
