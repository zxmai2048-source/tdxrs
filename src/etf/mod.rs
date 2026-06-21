//! ETF 模块
//!
//! 提供 ETF (交易所交易基金) 数据的解析和获取功能。
//!
//! # 概述
//!
//! ETF 在通达信中与股票共享市场代码，通过代码前缀区分：
//! - 沪市 ETF: 50xxxx, 51xxxx (market=1)
//! - 深市 ETF: 15xxxx, 16xxxx (market=0)
//!
//! 本模块封装了现有的行情客户端，提供 ETF 专用的 API，
//! 自动处理代码验证和系数转换。
//!
//! # 示例
//!
//! ```no_run
//! use tdxrs::etf::client::TdxHqEtfClient;
//! use tdxrs::etf::constants::{MARKET_SH, MARKET_SZ, KLINE_DAILY};
//!
//! // 创建客户端并连接
//! let client = TdxHqEtfClient::new();
//! client.connect_to_any(None).unwrap();
//!
//! // 获取 ETF 列表
//! let sh_etfs = client.get_etf_list(MARKET_SH).unwrap();
//! println!("Found {} ETFs in SH market", sh_etfs.len());
//!
//! // 获取 ETF K线
//! let bars = client.get_etf_bars(KLINE_DAILY, MARKET_SH, "510300", 0, 100).unwrap();
//! for bar in &bars {
//!     println!("{}: O={:.3} C={:.3}", bar.datetime, bar.open, bar.close);
//! }
//!
//! // 获取 ETF 实时行情
//! let quotes = client.get_etf_quotes(&[
//!     (MARKET_SH, "510300"),
//!     (MARKET_SZ, "159915"),
//! ]).unwrap();
//!
//! for q in &quotes {
//!     println!("{}: price={:.3}", q.code, q.price);
//! }
//! ```

pub mod client;
pub mod constants;
pub mod types;
pub mod utils;

// 重新导出常用类型
pub use client::TdxHqEtfClient;
pub use constants::*;
pub use types::*;
pub use utils::*;
