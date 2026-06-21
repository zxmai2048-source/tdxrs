//! ETF 模块常量定义
//!
//! 定义 ETF 代码前缀、类型标识、价格系数等常量。
//! ETF 与股票共享市场代码，通过代码前缀区分。

/// 沪市 ETF 代码前缀
pub const SH_ETF_PREFIXES: &[&str] = &["50", "51"];

/// 深市 ETF 代码前缀
pub const SZ_ETF_PREFIXES: &[&str] = &["15", "16"];

/// ETF 价格系数 (3位小数，比 A 股更精细)
pub const ETF_PRICE_COEFFICIENT: f64 = 0.001;

/// ETF 成交量系数 (沪市)
pub const SH_ETF_VOL_COEFFICIENT: f64 = 1.0;

/// ETF 成交量系数 (深市)
pub const SZ_ETF_VOL_COEFFICIENT: f64 = 0.01;

// 市场代码: 复用 crate::protocol::constants::{MARKET_SZ, MARKET_SH, MARKET_BJ}
pub use crate::protocol::constants::{MARKET_SZ, MARKET_SH, MARKET_BJ};

/// 判断是否为沪市 ETF
///
/// 沪市 ETF 代码前缀: 50, 51
///
/// # Example
/// ```
/// use tdxrs::etf::constants::is_etf;
/// use tdxrs::etf::constants::MARKET_SH;
/// assert!(is_etf(MARKET_SH, "510300"));
/// assert!(!is_etf(MARKET_SH, "600519"));
/// ```
fn is_sh_etf(code: &str) -> bool {
    SH_ETF_PREFIXES.iter().any(|p| code.starts_with(p))
}

/// 判断是否为深市 ETF
///
/// 深市 ETF 代码前缀: 15, 16
fn is_sz_etf(code: &str) -> bool {
    SZ_ETF_PREFIXES.iter().any(|p| code.starts_with(p))
}

/// 判断是否为 ETF
///
/// 根据市场代码和代码前缀判断是否为 ETF。
///
/// # Example
/// ```
/// use tdxrs::etf::constants::{is_etf, MARKET_SH, MARKET_SZ};
/// assert!(is_etf(MARKET_SH, "510300"));
/// assert!(is_etf(MARKET_SZ, "159915"));
/// assert!(!is_etf(MARKET_SH, "600519"));
/// assert!(!is_etf(MARKET_SZ, "000858"));
/// ```
pub fn is_etf(market: u8, code: &str) -> bool {
    match market {
        MARKET_SH => is_sh_etf(code),
        MARKET_SZ => is_sz_etf(code),
        _ => false,
    }
}

/// 自动判断市场代码
///
/// 根据代码前缀自动判断市场:
/// - 以 0, 3, 15, 16, 20 开头 → 深圳 (0)
/// - 以 5, 6, 9 开头 → 上海 (1)
///
/// # Example
/// ```
/// use tdxrs::etf::constants::{auto_market_code, MARKET_SH, MARKET_SZ};
/// assert_eq!(auto_market_code("510300"), MARKET_SH);
/// assert_eq!(auto_market_code("159915"), MARKET_SZ);
/// assert_eq!(auto_market_code("600519"), MARKET_SH);
/// ```
pub fn auto_market_code(code: &str) -> u8 {
    match code.chars().next() {
        Some('0') | Some('3') | Some('1') | Some('2') => MARKET_SZ,
        Some('5') | Some('6') | Some('9') => MARKET_SH,
        _ => MARKET_SZ, // 默认深圳
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_etf() {
        assert!(is_etf(MARKET_SH, "510300"));
        assert!(is_etf(MARKET_SZ, "159915"));
        assert!(!is_etf(MARKET_SH, "600519"));
        assert!(!is_etf(MARKET_SZ, "000858"));
        assert!(!is_etf(2, "510300")); // 北京市场
    }

    #[test]
    fn test_auto_market_code() {
        assert_eq!(auto_market_code("510300"), MARKET_SH);
        assert_eq!(auto_market_code("600519"), MARKET_SH);
        assert_eq!(auto_market_code("159915"), MARKET_SZ);
        assert_eq!(auto_market_code("000858"), MARKET_SZ);
        assert_eq!(auto_market_code("300750"), MARKET_SZ);
    }
}
