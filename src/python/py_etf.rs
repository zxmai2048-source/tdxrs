use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::etf::client::TdxHqEtfClient;
use crate::etf::constants as etf_const;

/// ETF 行情客户端 - Python 绑定
///
/// 封装 TdxHqClient，提供 ETF 专用的 API。
/// 自动处理 ETF 代码验证和系数转换。
///
/// # Example
///
/// ```python
/// from tdxrs import TdxHqEtfClient
/// from tdxrs.constants import MARKET_SH, MARKET_SZ, KLINE_DAILY
///
/// client = TdxHqEtfClient()
/// client.connect_to_any()
///
/// # 获取 ETF 列表
/// sh_etfs = client.get_etf_list(MARKET_SH)
/// print(f"Found {len(sh_etfs)} ETFs")
///
/// # 获取 ETF K线
/// bars = client.get_etf_bars(KLINE_DAILY, MARKET_SH, "510300", 0, 100)
/// for bar in bars:
///     print(f"{bar['datetime']}: {bar['open']:.3f}")
///
/// # 获取 ETF 实时行情
/// quotes = client.get_etf_quotes([(MARKET_SH, "510300"), (MARKET_SZ, "159915")])
/// for q in quotes:
///     print(f"{q['code']}: {q['price']:.3f}")
/// ```
#[pyclass(name = "TdxHqEtfClient")]
pub struct PyTdxHqEtfClient {
    client: TdxHqEtfClient,
}

#[pymethods]
impl PyTdxHqEtfClient {
    /// 创建新的 ETF 客户端
    #[new]
    fn new() -> Self {
        Self {
            client: TdxHqEtfClient::new(),
        }
    }

    /// 连接到 TDX 服务器
    #[pyo3(signature = (ip, port, timeout=None))]
    fn connect(&self, ip: &str, port: u16, timeout: Option<f64>) -> PyResult<bool> {
        self.client
            .connect(ip, port, timeout)
            .map_err(|e| pyo3::exceptions::PyConnectionError::new_err(e.to_string()))
    }

    /// 连接到任意可用服务器
    #[pyo3(signature = (timeout=None))]
    fn connect_to_any(&self, timeout: Option<f64>) -> PyResult<bool> {
        self.client
            .connect_to_any(timeout)
            .map_err(|e| pyo3::exceptions::PyConnectionError::new_err(e.to_string()))
    }

    /// 断开连接
    fn disconnect(&self) {
        self.client.disconnect();
    }

    /// 是否已连接
    fn is_connected(&self) -> bool {
        self.client.is_connected()
    }

    /// 获取 ETF 列表
    ///
    /// 从证券列表中筛选出 ETF，返回 ETF 信息列表。
    ///
    /// Args:
    ///     market: 市场代码 (0=深圳, 1=上海)
    ///
    /// Returns:
    ///     list[dict]: ETF 信息列表，每项包含:
    ///         - market: 市场代码
    ///         - code: ETF 代码
    ///         - name: ETF 名称
    ///         - vol_unit: 每手股数
    ///         - decimal_point: 小数点位数
    ///         - pre_close: 昨收价
    #[pyo3(signature = (market,))]
    fn get_etf_list(&self, py: Python<'_>, market: u8) -> PyResult<Py<PyAny>> {
        let etfs = self
            .client
            .get_etf_list(market)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for etf in &etfs {
            let dict = PyDict::new(py);
            dict.set_item("market", etf.market)?;
            dict.set_item("code", &etf.code)?;
            dict.set_item("name", &etf.name)?;
            dict.set_item("vol_unit", etf.vol_unit)?;
            dict.set_item("decimal_point", etf.decimal_point)?;
            dict.set_item("pre_close", etf.pre_close)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取 ETF K线数据
    ///
    /// 支持所有 K线周期 (5分钟、15分钟、日线、周线等)。
    /// 价格已应用 ETF 系数 (0.001)。
    ///
    /// Args:
    ///     category: K线种类 (0=5分钟, 1=15分钟, 4=日线, 5=周线 等)
    ///     market: 市场代码 (0=深圳, 1=上海)
    ///     code: ETF 代码
    ///     start: 起始偏移 (0=最新)
    ///     count: 数量 (最大 800)
    ///
    /// Returns:
    ///     list[dict]: K线数据列表
    #[pyo3(signature = (category, market, code, start=0, count=800))]
    fn get_etf_bars(
        &self,
        py: Python<'_>,
        category: u8,
        market: u8,
        code: &str,
        start: u32,
        count: u16,
    ) -> PyResult<Py<PyAny>> {
        let bars = self
            .client
            .get_etf_bars(category, market, code, start, count)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for b in &bars {
            let dict = PyDict::new(py);
            dict.set_item("open", b.open)?;
            dict.set_item("close", b.close)?;
            dict.set_item("high", b.high)?;
            dict.set_item("low", b.low)?;
            dict.set_item("vol", b.vol)?;
            dict.set_item("amount", b.amount)?;
            dict.set_item("year", b.year)?;
            dict.set_item("month", b.month)?;
            dict.set_item("day", b.day)?;
            dict.set_item("hour", b.hour)?;
            dict.set_item("minute", b.minute)?;
            dict.set_item("datetime", &b.datetime)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取 ETF K线数据 (自动分页)
    #[pyo3(signature = (category, market, code, count=800))]
    fn get_etf_bars_all(
        &self,
        py: Python<'_>,
        category: u8,
        market: u8,
        code: &str,
        count: u16,
    ) -> PyResult<Py<PyAny>> {
        let bars = self
            .client
            .get_etf_bars_all(category, market, code, count)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for b in &bars {
            let dict = PyDict::new(py);
            dict.set_item("open", b.open)?;
            dict.set_item("close", b.close)?;
            dict.set_item("high", b.high)?;
            dict.set_item("low", b.low)?;
            dict.set_item("vol", b.vol)?;
            dict.set_item("amount", b.amount)?;
            dict.set_item("year", b.year)?;
            dict.set_item("month", b.month)?;
            dict.set_item("day", b.day)?;
            dict.set_item("hour", b.hour)?;
            dict.set_item("minute", b.minute)?;
            dict.set_item("datetime", &b.datetime)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取 ETF 实时行情
    ///
    /// 批量获取多只 ETF 的实时报价。
    ///
    /// Args:
    ///     stocks: ETF 列表 [(market, code), ...]
    ///
    /// Returns:
    ///     list[dict]: 行情列表
    #[pyo3(signature = (stocks,))]
    fn get_etf_quotes(&self, py: Python<'_>, stocks: Vec<(u8, String)>) -> PyResult<Py<PyAny>> {
        let stock_refs: Vec<(u8, &str)> = stocks.iter().map(|(m, c)| (*m, c.as_str())).collect();
        let quotes = self
            .client
            .get_etf_quotes(&stock_refs)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for q in &quotes {
            let dict = PyDict::new(py);
            dict.set_item("market", q.market)?;
            dict.set_item("code", &q.code)?;
            dict.set_item("price", q.price)?;
            dict.set_item("last_close", q.last_close)?;
            dict.set_item("open", q.open)?;
            dict.set_item("high", q.high)?;
            dict.set_item("low", q.low)?;
            dict.set_item("vol", q.vol)?;
            dict.set_item("amount", q.amount)?;
            dict.set_item("bid1", q.bid1)?;
            dict.set_item("bid_vol1", q.bid_vol1)?;
            dict.set_item("bid2", q.bid2)?;
            dict.set_item("bid_vol2", q.bid_vol2)?;
            dict.set_item("bid3", q.bid3)?;
            dict.set_item("bid_vol3", q.bid_vol3)?;
            dict.set_item("bid4", q.bid4)?;
            dict.set_item("bid_vol4", q.bid_vol4)?;
            dict.set_item("bid5", q.bid5)?;
            dict.set_item("bid_vol5", q.bid_vol5)?;
            dict.set_item("ask1", q.ask1)?;
            dict.set_item("ask_vol1", q.ask_vol1)?;
            dict.set_item("ask2", q.ask2)?;
            dict.set_item("ask_vol2", q.ask_vol2)?;
            dict.set_item("ask3", q.ask3)?;
            dict.set_item("ask_vol3", q.ask_vol3)?;
            dict.set_item("ask4", q.ask4)?;
            dict.set_item("ask_vol4", q.ask_vol4)?;
            dict.set_item("ask5", q.ask5)?;
            dict.set_item("ask_vol5", q.ask_vol5)?;
            dict.set_item("servertime", &q.servertime)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取 ETF 分时数据
    #[pyo3(signature = (market, code))]
    fn get_etf_minute_time_data(
        &self,
        py: Python<'_>,
        market: u8,
        code: &str,
    ) -> PyResult<Py<PyAny>> {
        let data = self
            .client
            .get_etf_minute_time_data(market, code)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for item in &data {
            let dict = PyDict::new(py);
            dict.set_item("price", item.price)?;
            dict.set_item("vol", item.vol)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取 ETF 历史分时数据
    #[pyo3(signature = (market, code, date))]
    fn get_etf_history_minute_time_data(
        &self,
        py: Python<'_>,
        market: u8,
        code: &str,
        date: u32,
    ) -> PyResult<Py<PyAny>> {
        let data = self
            .client
            .get_etf_history_minute_time_data(market, code, date)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for item in &data {
            let dict = PyDict::new(py);
            dict.set_item("price", item.price)?;
            dict.set_item("vol", item.vol)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取 ETF 逐笔成交
    #[pyo3(signature = (market, code, start=0, count=2000))]
    fn get_etf_transaction_data(
        &self,
        py: Python<'_>,
        market: u8,
        code: &str,
        start: u16,
        count: u16,
    ) -> PyResult<Py<PyAny>> {
        let data = self
            .client
            .get_etf_transaction_data(market, code, start, count)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for item in &data {
            let dict = PyDict::new(py);
            dict.set_item("time", &item.time)?;
            dict.set_item("price", item.price)?;
            dict.set_item("vol", item.vol)?;
            dict.set_item("num", item.num)?;
            dict.set_item("buyorsell", item.buyorsell)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取 ETF 历史逐笔成交
    #[pyo3(signature = (market, code, start, count, date))]
    fn get_etf_history_transaction_data(
        &self,
        py: Python<'_>,
        market: u8,
        code: &str,
        start: u16,
        count: u16,
        date: u32,
    ) -> PyResult<Py<PyAny>> {
        let data = self
            .client
            .get_etf_history_transaction_data(market, code, start, count, date)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for item in &data {
            let dict = PyDict::new(py);
            dict.set_item("time", &item.time)?;
            dict.set_item("price", item.price)?;
            dict.set_item("vol", item.vol)?;
            dict.set_item("buyorsell", item.buyorsell)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取 ETF 除权除息信息
    #[pyo3(signature = (market, code))]
    fn get_etf_xdxr_info(
        &self,
        py: Python<'_>,
        market: u8,
        code: &str,
    ) -> PyResult<Py<PyAny>> {
        let data = self
            .client
            .get_etf_xdxr_info(market, code)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for item in &data {
            let dict = PyDict::new(py);
            dict.set_item("year", item.year)?;
            dict.set_item("month", item.month)?;
            dict.set_item("day", item.day)?;
            dict.set_item("category", item.category)?;
            dict.set_item("fenhong", item.fenhong)?;
            dict.set_item("peigujia", item.peigujia)?;
            dict.set_item("songzhuangu", item.songzhuangu)?;
            dict.set_item("peigu", item.peigu)?;
            dict.set_item("suogu", item.suogu)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取 ETF 财务信息
    ///
    /// 注意: ETF 财务数据仅包含部分有意义的字段。
    #[pyo3(signature = (market, code))]
    fn get_etf_finance_info(
        &self,
        py: Python<'_>,
        market: u8,
        code: &str,
    ) -> PyResult<Py<PyAny>> {
        let info = self
            .client
            .get_etf_finance_info(market, code)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let dict = PyDict::new(py);
        dict.set_item("market", info.market)?;
        dict.set_item("code", &info.code)?;
        dict.set_item("zongguben", info.zongguben)?;
        dict.set_item("liutongguben", info.liutongguben)?;
        dict.set_item("meigujingzichan", info.meigujingzichan)?;
        dict.set_item("zongzichan", info.zongzichan)?;
        dict.set_item("jingzichan", info.jingzichan)?;
        Ok(dict.into())
    }

    /// 判断是否为 ETF 代码
    ///
    /// Args:
    ///     market: 市场代码
    ///     code: 证券代码
    ///
    /// Returns:
    ///     bool: 是否为 ETF
    #[staticmethod]
    fn is_etf(market: u8, code: &str) -> bool {
        etf_const::is_etf(market, code)
    }

    /// 自动判断市场代码
    ///
    /// 根据代码前缀自动判断市场:
    /// - 以 0, 3, 15, 16, 20 开头 → 深圳 (0)
    /// - 以 5, 6, 9 开头 → 上海 (1)
    ///
    /// Args:
    ///     code: 证券代码
    ///
    /// Returns:
    ///     int: 市场代码
    #[staticmethod]
    fn auto_market_code(code: &str) -> u8 {
        etf_const::auto_market_code(code)
    }
}

impl Default for PyTdxHqEtfClient {
    fn default() -> Self {
        Self::new()
    }
}
