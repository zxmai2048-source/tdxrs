pub mod constants;
pub mod error;
pub mod helpers;
pub mod logging;
pub mod net;
pub mod protocol;
pub mod python;
pub mod reader;

use pyo3::prelude::*;

/// tdxrs - 通达信行情数据解析库
///
/// 提供高性能的 TDX 二进制数据解析，支持 Python 调用。
#[pymodule(name = "_internal")]
fn tdxrs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Reader classes
    m.add_class::<python::py_reader::DailyBarReader>()?;
    m.add_class::<python::py_reader::MinBarReader>()?;
    m.add_class::<python::py_reader::LcMinBarReader>()?;
    m.add_class::<python::py_reader::BlockReader>()?;
    m.add_class::<python::py_reader::FinancialReader>()?;
    // Client classes
    m.add_class::<python::py_client::PyTdxHqClient>()?;
    m.add_class::<python::py_direct_client::PyTdxDirectClient>()?;
    // Protocol constants
    python::py_constants::register_constants(m)?;
    Ok(())
}
