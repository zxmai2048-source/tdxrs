//! ETF 客户端封装
//!
//! 封装现有的 `TdxHqClient`，提供 ETF 专用的 API。
//! 不修改现有客户端代码，仅通过组合方式扩展功能。

use crate::error::Result;
use crate::net::client::TdxHqClient;
use crate::protocol::types::{MinuteTimePrice, TickData};

use super::constants::{is_etf, MARKET_SH, MARKET_SZ};
use super::types::*;
use super::utils::{validate_etf_code, validate_etf_stocks};

/// ETF 行情客户端
///
/// 封装 `TdxHqClient`，提供 ETF 专用的数据获取方法。
/// 自动处理 ETF 代码验证和系数转换。
///
/// # Example
/// ```no_run
/// use tdxrs::etf::client::TdxHqEtfClient;
/// use tdxrs::etf::constants::{MARKET_SH, MARKET_SZ};
///
/// let client = TdxHqEtfClient::new();
/// client.connect_to_any(None).unwrap();
///
/// // 获取 ETF K线
/// let bars = client.get_etf_bars(KLINE_DAILY, MARKET_SH, "510300", 0, 100).unwrap();
/// println!("Got {} bars", bars.len());
/// ```
pub struct TdxHqEtfClient {
    inner: TdxHqClient,
}

impl TdxHqEtfClient {
    /// 创建新的 ETF 客户端
    pub fn new() -> Self {
        Self {
            inner: TdxHqClient::new(),
        }
    }

    /// 连接到指定服务器
    pub fn connect(&self, ip: &str, port: u16, timeout: Option<f64>) -> Result<bool> {
        self.inner.connect(ip, port, timeout)
    }

    /// 连接到任意可用服务器
    pub fn connect_to_any(&self, timeout: Option<f64>) -> Result<bool> {
        self.inner.connect_to_any(timeout)
    }

    /// 断开连接
    pub fn disconnect(&self) {
        self.inner.disconnect()
    }

    /// 检查是否已连接
    pub fn is_connected(&self) -> bool {
        self.inner.is_connected()
    }

    /// 获取 ETF 列表
    ///
    /// 从证券列表中筛选出 ETF，返回 ETF 基本信息列表。
    ///
    /// # Arguments
    ///
    /// * `market` - 市场代码 (0=深圳, 1=上海)
    ///
    /// # Returns
    ///
    /// 返回 ETF 信息列表，包含代码、名称、昨收价等。
    ///
    /// # Example
    ///
    /// ```no_run
    /// use tdxrs::etf::client::TdxHqEtfClient;
    /// use tdxrs::etf::constants::MARKET_SH;
    ///
    /// let client = TdxHqEtfClient::new();
    /// client.connect_to_any(None).unwrap();
    ///
    /// let sh_etfs = client.get_etf_list(MARKET_SH).unwrap();
    /// println!("Found {} ETFs in SH market", sh_etfs.len());
    /// ```
    pub fn get_etf_list(&self, market: u8) -> Result<Vec<EtfInfo>> {
        let total = self.inner.get_security_count(market)?;
        let mut etfs = Vec::new();
        let page_size = 1000u16;

        for start in (0..total).step_by(page_size as usize) {
            let sec_list = self.inner.get_security_list(market, start)?;
            if sec_list.is_empty() {
                break;
            }

            for item in &sec_list {
                if is_etf(market, &item.code) {
                    etfs.push(EtfInfo {
                        market,
                        code: item.code.clone(),
                        name: item.name.clone(),
                        vol_unit: item.volunit as u32,
                        decimal_point: item.decimal_point as u32,
                        pre_close: item.pre_close,
                    });
                }
            }

            // 如果这一页最后一条已经超出 ETF 范围，提前结束
            if let Some(last) = sec_list.last() {
                let last_is_beyond = match market {
                    MARKET_SH => {
                        !last.code.starts_with("50") && !last.code.starts_with("51")
                            && last.code.as_str() > "519999"
                    }
                    MARKET_SZ => {
                        !last.code.starts_with("15") && !last.code.starts_with("16")
                            && last.code.as_str() > "169999"
                    }
                    _ => false,
                };
                if last_is_beyond && !etfs.is_empty() {
                    break;
                }
            }
        }

        Ok(etfs)
    }

    /// 获取 ETF K线数据
    ///
    /// 支持所有 K线周期 (5分钟、15分钟、日线、周线等)。
    /// 价格已应用 ETF 系数 (0.001)。
    ///
    /// # Arguments
    ///
    /// * `category` - K线种类 (0=5分钟, 1=15分钟, 4=日线, 5=周线 等)
    /// * `market` - 市场代码
    /// * `code` - ETF 代码
    /// * `start` - 起始偏移 (0=最新)
    /// * `count` - 数量 (最大 800)
    ///
    /// # Errors
    ///
    /// 如果代码不是 ETF，返回 `EtfError::InvalidEtfCode`。
    ///
    /// # Example
    ///
    /// ```no_run
    /// use tdxrs::etf::client::TdxHqEtfClient;
    /// use tdxrs::etf::constants::{MARKET_SH, KLINE_DAILY};
    ///
    /// let client = TdxHqEtfClient::new();
    /// client.connect_to_any(None).unwrap();
    ///
    /// let bars = client.get_etf_bars(KLINE_DAILY, MARKET_SH, "510300", 0, 100).unwrap();
    /// for bar in &bars {
    ///     println!("{}: O={:.3} C={:.3}", bar.datetime, bar.open, bar.close);
    /// }
    /// ```
    pub fn get_etf_bars(
        &self,
        category: u8,
        market: u8,
        code: &str,
        start: u32,
        count: u16,
    ) -> Result<Vec<EtfBar>> {
        validate_etf_code(market, code).map_err(|e| {
            crate::error::TdxError::ResponseParse(e.to_string())
        })?;

        let bars = self.inner.get_security_bars(category, market, code, start, count, 0)?;
        Ok(bars.iter().map(EtfBar::from_security_bar).collect())
    }

    /// 获取 ETF K线数据 (自动分页)
    ///
    /// 自动翻页获取指定数量的 K线数据。
    ///
    /// # Arguments
    ///
    /// * `category` - K线种类
    /// * `market` - 市场代码
    /// * `code` - ETF 代码
    /// * `count` - 总数量 (超过 800 自动分页)
    pub fn get_etf_bars_all(
        &self,
        category: u8,
        market: u8,
        code: &str,
        count: u16,
    ) -> Result<Vec<EtfBar>> {
        validate_etf_code(market, code).map_err(|e| {
            crate::error::TdxError::ResponseParse(e.to_string())
        })?;

        let bars = self.inner.get_security_bars_all(category, market, code, count, 0)?;
        Ok(bars.iter().map(EtfBar::from_security_bar).collect())
    }

    /// 获取 ETF 实时行情
    ///
    /// 批量获取多只 ETF 的实时报价。
    ///
    /// # Arguments
    ///
    /// * `stocks` - ETF 列表 [(market, code), ...]
    ///
    /// # Example
    ///
    /// ```no_run
    /// use tdxrs::etf::client::TdxHqEtfClient;
    /// use tdxrs::etf::constants::{MARKET_SH, MARKET_SZ};
    ///
    /// let client = TdxHqEtfClient::new();
    /// client.connect_to_any(None).unwrap();
    ///
    /// let quotes = client.get_etf_quotes(&[
    ///     (MARKET_SH, "510300"),
    ///     (MARKET_SZ, "159915"),
    /// ]).unwrap();
    ///
    /// for q in &quotes {
    ///     println!("{}: {:.3}", q.code, q.price);
    /// }
    /// ```
    pub fn get_etf_quotes(&self, stocks: &[(u8, &str)]) -> Result<Vec<EtfQuote>> {
        validate_etf_stocks(stocks).map_err(|e| {
            crate::error::TdxError::ResponseParse(e.to_string())
        })?;

        let quotes = self.inner.get_security_quotes(stocks)?;
        Ok(quotes.iter().map(EtfQuote::from_security_quote).collect())
    }

    /// 获取 ETF 分时数据
    ///
    /// 获取当日分时数据 (仅交易时段有数据)。
    pub fn get_etf_minute_time_data(&self, market: u8, code: &str) -> Result<Vec<MinuteTimePrice>> {
        validate_etf_code(market, code).map_err(|e| {
            crate::error::TdxError::ResponseParse(e.to_string())
        })?;

        self.inner.get_minute_time_data(market, code)
    }

    /// 获取 ETF 历史分时数据
    ///
    /// # Arguments
    ///
    /// * `market` - 市场代码
    /// * `code` - ETF 代码
    /// * `date` - 日期 (YYYYMMDD 格式，如 20260618)
    pub fn get_etf_history_minute_time_data(
        &self,
        market: u8,
        code: &str,
        date: u32,
    ) -> Result<Vec<MinuteTimePrice>> {
        validate_etf_code(market, code).map_err(|e| {
            crate::error::TdxError::ResponseParse(e.to_string())
        })?;

        self.inner.get_history_minute_time_data(market, code, date)
    }

    /// 获取 ETF 逐笔成交
    ///
    /// 仅交易时段有数据。
    pub fn get_etf_transaction_data(
        &self,
        market: u8,
        code: &str,
        start: u16,
        count: u16,
    ) -> Result<Vec<TickData>> {
        validate_etf_code(market, code).map_err(|e| {
            crate::error::TdxError::ResponseParse(e.to_string())
        })?;

        self.inner.get_transaction_data(market, code, start, count)
    }

    /// 获取 ETF 历史逐笔成交
    pub fn get_etf_history_transaction_data(
        &self,
        market: u8,
        code: &str,
        start: u16,
        count: u16,
        date: u32,
    ) -> Result<Vec<TickData>> {
        validate_etf_code(market, code).map_err(|e| {
            crate::error::TdxError::ResponseParse(e.to_string())
        })?;

        self.inner
            .get_history_transaction_data(market, code, start, count, date)
    }

    /// 获取 ETF 除权除息信息
    ///
    /// ETF 通常只有分红记录 (category=1)，无送配股。
    pub fn get_etf_xdxr_info(&self, market: u8, code: &str) -> Result<Vec<EtfXdXrInfo>> {
        validate_etf_code(market, code).map_err(|e| {
            crate::error::TdxError::ResponseParse(e.to_string())
        })?;

        let xdxr = self.inner.get_xdxr_info(market, code)?;
        Ok(xdxr.iter().map(EtfXdXrInfo::from_xdxr_info).collect())
    }

    /// 获取 ETF 财务信息
    ///
    /// 注意: ETF 财务数据仅包含部分有意义的字段。
    pub fn get_etf_finance_info(&self, market: u8, code: &str) -> Result<EtfFinanceInfo> {
        validate_etf_code(market, code).map_err(|e| {
            crate::error::TdxError::ResponseParse(e.to_string())
        })?;

        let info = self.inner.get_finance_info(market, code)?;
        Ok(EtfFinanceInfo::from_finance_info(&info))
    }
}

impl Default for TdxHqEtfClient {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::protocol::constants::KLINE_DAILY;

    #[test]
    fn test_etf_client_creation() {
        let client = TdxHqEtfClient::new();
        assert!(!client.is_connected());
    }

    #[test]
    fn test_etf_client_default() {
        let client = TdxHqEtfClient::default();
        assert!(!client.is_connected());
    }

    #[test]
    fn test_get_etf_bars_invalid_code() {
        let client = TdxHqEtfClient::new();
        // 不连接服务器，只测试代码验证
        let result = client.get_etf_bars(KLINE_DAILY, 1, "600519", 0, 10);
        assert!(result.is_err());
    }

    #[test]
    fn test_get_etf_quotes_invalid_code() {
        let client = TdxHqEtfClient::new();
        let result = client.get_etf_quotes(&[(1, "600519")]);
        assert!(result.is_err());
    }

    #[test]
    fn test_get_etf_xdxr_info_invalid_code() {
        let client = TdxHqEtfClient::new();
        let result = client.get_etf_xdxr_info(1, "600519");
        assert!(result.is_err());
    }

    #[test]
    fn test_get_etf_finance_info_invalid_code() {
        let client = TdxHqEtfClient::new();
        let result = client.get_etf_finance_info(1, "600519");
        assert!(result.is_err());
    }
}
