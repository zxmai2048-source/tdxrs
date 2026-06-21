//! ETF 工具函数
//!
//! 提供 ETF 代码验证等辅助功能。

#[cfg(test)]
use super::constants::{MARKET_SH, MARKET_SZ};
use super::constants::is_etf;

/// ETF 代码验证错误
#[derive(Debug, Clone)]
pub enum EtfError {
    /// 不是有效的 ETF 代码
    InvalidEtfCode(String),
}

impl std::fmt::Display for EtfError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            EtfError::InvalidEtfCode(code) => write!(f, "Invalid ETF code: {}", code),
        }
    }
}

impl std::error::Error for EtfError {}

/// 验证 ETF 代码
///
/// 检查给定的市场代码和代码是否为有效的 ETF。
///
/// # Errors
///
/// 如果不是有效的 ETF 代码，返回 `EtfError::InvalidEtfCode`。
///
/// # Example
/// ```
/// use tdxrs::etf::utils::validate_etf_code;
/// use tdxrs::etf::constants::{MARKET_SH, MARKET_SZ};
///
/// assert!(validate_etf_code(MARKET_SH, "510300").is_ok());
/// assert!(validate_etf_code(MARKET_SZ, "159915").is_ok());
/// assert!(validate_etf_code(MARKET_SH, "600519").is_err());
/// ```
pub fn validate_etf_code(market: u8, code: &str) -> Result<(), EtfError> {
    if !is_etf(market, code) {
        return Err(EtfError::InvalidEtfCode(format!(
            "{}:{} is not an ETF",
            market, code
        )));
    }
    Ok(())
}

/// 批量验证 ETF 代码
///
/// # Example
/// ```
/// use tdxrs::etf::utils::validate_etf_stocks;
/// use tdxrs::etf::constants::{MARKET_SH, MARKET_SZ};
///
/// let valid = vec![(MARKET_SH, "510300"), (MARKET_SZ, "159915")];
/// assert!(validate_etf_stocks(&valid).is_ok());
///
/// let invalid = vec![(MARKET_SH, "510300"), (MARKET_SH, "600519")];
/// assert!(validate_etf_stocks(&invalid).is_err());
/// ```
pub fn validate_etf_stocks(stocks: &[(u8, &str)]) -> Result<(), EtfError> {
    for (market, code) in stocks {
        validate_etf_code(*market, code)?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_etf_code() {
        assert!(validate_etf_code(MARKET_SH, "510300").is_ok());
        assert!(validate_etf_code(MARKET_SZ, "159915").is_ok());
        assert!(validate_etf_code(MARKET_SH, "600519").is_err());
        assert!(validate_etf_code(MARKET_SZ, "000858").is_err());
    }

    #[test]
    fn test_validate_etf_stocks() {
        let valid = vec![(MARKET_SH, "510300"), (MARKET_SZ, "159915")];
        assert!(validate_etf_stocks(&valid).is_ok());

        let invalid = vec![(MARKET_SH, "510300"), (MARKET_SH, "600519")];
        assert!(validate_etf_stocks(&invalid).is_err());
    }
}
