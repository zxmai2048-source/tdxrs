//! 协议常量暴露 — 消除 Python 端硬编码
//!
//! 在 lib.rs 中调用 `register_constants(m)?` 将所有常量注入模块。

use crate::protocol::constants;
use pyo3::prelude::*;

/// 将协议常量注册到 Python 模块的 __dict__
pub fn register_constants(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // 市场代码
    m.setattr("MARKET_SZ", 0u8)?;
    m.setattr("MARKET_SH", 1u8)?;
    m.setattr("MARKET_BJ", 2u8)?;

    // K线种类
    m.setattr("KLINE_5MIN", constants::KLINE_5MIN)?;
    m.setattr("KLINE_15MIN", constants::KLINE_15MIN)?;
    m.setattr("KLINE_30MIN", constants::KLINE_30MIN)?;
    m.setattr("KLINE_1HOUR", constants::KLINE_1HOUR)?;
    m.setattr("KLINE_DAILY", constants::KLINE_DAILY)?;
    m.setattr("KLINE_WEEKLY", constants::KLINE_WEEKLY)?;
    m.setattr("KLINE_MONTHLY", constants::KLINE_MONTHLY)?;
    m.setattr("KLINE_EXHQ_1MIN", constants::KLINE_EXHQ_1MIN)?;
    m.setattr("KLINE_1MIN", constants::KLINE_1MIN)?;
    m.setattr("KLINE_RI_K", constants::KLINE_RI_K)?;
    m.setattr("KLINE_3MONTH", constants::KLINE_3MONTH)?;
    m.setattr("KLINE_YEARLY", constants::KLINE_YEARLY)?;

    // 复权类型
    m.setattr("FQ_NONE", constants::fq_type::NONE)?;
    m.setattr("FQ_QFQ", constants::fq_type::QFQ)?;
    m.setattr("FQ_HFQ", constants::fq_type::HFQ)?;

    // 限制
    m.setattr("MAX_KLINE_COUNT", constants::MAX_KLINE_COUNT)?;
    m.setattr("MAX_TRANSACTION_COUNT", constants::MAX_TRANSACTION_COUNT)?;

    // 默认配置
    m.setattr("DEFAULT_PORT", constants::DEFAULT_PORT)?;
    m.setattr("DEFAULT_POOL_SIZE", constants::DEFAULT_POOL_SIZE)?;
    m.setattr("FQ_PRICE_PRECISION", constants::FQ_PRICE_PRECISION)?;

    // 板块文件名
    m.setattr("BLOCK_SZ", constants::BLOCK_SZ)?;
    m.setattr("BLOCK_FG", constants::BLOCK_FG)?;
    m.setattr("BLOCK_GN", constants::BLOCK_GN)?;
    m.setattr("BLOCK_DEFAULT", constants::BLOCK_DEFAULT)?;

    Ok(())
}
