pub mod block;
pub mod constants;
pub mod error;
pub mod error_codes;
pub mod fund;
pub mod helpers;
pub mod logging;
pub mod net;
pub mod profile;
pub mod protocol;
pub mod python;
pub mod reader;

use pyo3::prelude::*;

/// tdxrs - 通达信行情数据解析库
///
/// 提供高性能的 TDX 二进制数据解析，支持 Python 调用。
#[pymodule(name = "_internal")]
fn tdxrs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // 初始化日志系统 (读取 TDXRS_LOG 环境变量)
    logging::init();

    // Reader classes
    m.add_class::<python::py_reader::DailyBarReader>()?;
    m.add_class::<python::py_reader::MinBarReader>()?;
    m.add_class::<python::py_reader::LcMinBarReader>()?;
    m.add_class::<python::py_reader::BlockReader>()?;
    m.add_class::<python::py_reader::FinancialReader>()?;
    // Client classes
    m.add_class::<python::py_client::PyTdxHqClient>()?;
    m.add_class::<python::py_direct_client::PyTdxDirectClient>()?;
    m.add_class::<python::py_async_client::PyAsyncTdxHqClient>()?;
    m.add_class::<python::py_smart_client::PyTdxSmartClient>()?;
    // Fund client
    m.add_class::<python::py_fund::PyTdxHqFundClient>()?;
    // Block client
    m.add_class::<python::py_fund::PyTdxBlockClient>()?;
    // F10 profile client — 需要 --features f10 启用
    #[cfg(feature = "f10")]
    m.add_class::<python::py_profile::PyTdxF10Client>()?;
    // Protocol constants
    python::py_constants::register_constants(m)?;
    Ok(())
}
