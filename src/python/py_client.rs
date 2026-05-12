use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};
use pyo3::IntoPyObjectExt;

use crate::net::client::TdxHqClient;

/// TDX 行情客户端 - Python 绑定
#[pyclass(name = "TdxHqClient")]
pub struct PyTdxHqClient {
    client: TdxHqClient,
}

#[pymethods]
impl PyTdxHqClient {
    #[new]
    fn new() -> Self {
        Self {
            client: TdxHqClient::new(),
        }
    }

    /// 连接到 TDX 服务器
    #[pyo3(signature = (ip, port, timeout=None))]
    fn connect(&self, ip: &str, port: u16, timeout: Option<f64>) -> PyResult<bool> {
        self.client
            .connect(ip, port, timeout)
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

    /// 连接到任意可用服务器 (从默认列表中选择)
    #[pyo3(signature = (timeout=None))]
    fn connect_to_any(&self, timeout: Option<f64>) -> PyResult<bool> {
        self.client
            .connect_to_any(timeout)
            .map_err(|e| pyo3::exceptions::PyConnectionError::new_err(e.to_string()))
    }

    /// 设置是否自动重试
    fn set_auto_retry(&self, enabled: bool) {
        self.client.set_auto_retry(enabled);
    }

    /// 设置缓存 TTL (秒)
    fn set_cache_ttl(&self, ttl_secs: u64) {
        self.client.set_cache_ttl(ttl_secs);
    }

    /// 设置连接超时 (秒)
    fn set_connect_timeout(&self, timeout: f64) {
        self.client.set_connect_timeout(timeout);
    }

    /// 设置自定义优先服务器列表
    ///
    /// servers: list of (name, ip, port) tuples, e.g. [("海通8", "58.63.254.191", 7709), ...]
    fn set_servers(&self, servers: Vec<(String, String, u16)>) {
        let refs: Vec<(&str, &str, u16)> =
            servers.iter().map(|(n, i, p)| (n.as_str(), i.as_str(), *p)).collect();
        self.client.set_servers(&refs);
    }

    /// 在优先列表头部添加一台服务器
    fn add_server(&self, name: &str, ip: &str, port: u16) {
        self.client.add_server(name, ip, port);
    }

    /// 按响应时间重排优先服务器
    ///
    /// servers: 从 probe_servers() 返回的排序结果, 取前N个
    fn reorder_servers(&self, servers: Vec<(String, String, u16)>) {
        let refs: Vec<(&str, &str, u16)> =
            servers.iter().map(|(n, i, p)| (n.as_str(), i.as_str(), *p)).collect();
        self.client.reorder_servers(&refs);
    }

    /// 探测全部已知服务器, 返回按 API 响应时间排序的结果
    ///
    /// 返回: list of (name, ip, port, tcp_ms, hs_ms, api_ms)
    /// 不会自动修改优先列表, 用户根据结果自行调用 reorder_servers()
    #[pyo3(signature = (timeout=3.0))]
    fn probe_servers(
        &self,
        py: Python<'_>,
        timeout: f64,
    ) -> PyResult<Py<PyAny>> {
        let results = self.client.probe_servers(timeout);
        let list = PyList::empty(py);
        for (name, ip, port, tcp_ms, hs_ms, api_ms) in &results {
            let tuple = PyTuple::new(py, &[
                name.into_py_any(py)?,
                ip.into_py_any(py)?,
                port.into_py_any(py)?,
                tcp_ms.into_py_any(py)?,
                hs_ms.into_py_any(py)?,
                api_ms.into_py_any(py)?,
            ])?;
            list.append(tuple)?;
        }
        Ok(list.into())
    }

    /// 获取连接池状态
    fn pool_stats(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let stats = self.client.pool_stats();
        let dict = PyDict::new(py);
        dict.set_item("idle", stats.idle)?;
        dict.set_item("active", stats.active)?;
        dict.set_item("total", stats.total)?;
        dict.set_item("max_size", stats.max_size)?;
        Ok(dict.into())
    }

    /// 获取K线数据
    ///
    /// fq: 复权类型, 0=未复权 1=前复权(默认) 2=后复权
    #[pyo3(signature = (category, market, code, start=0, count=800, fq=1))]
    fn get_security_bars(
        &self,
        py: Python<'_>,
        category: u8,
        market: u8,
        code: &str,
        start: u32,
        count: u16,
        fq: u8,
    ) -> PyResult<Py<PyAny>> {
        let bars = self
            .client
            .get_security_bars(category, market, code, start, count, fq)
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

    /// 获取K线数据 (自动分页)
    #[pyo3(signature = (category, market, code, count=800, fq=1))]
    fn get_security_bars_all(
        &self,
        py: Python<'_>,
        category: u8,
        market: u8,
        code: &str,
        count: u16,
        fq: u8,
    ) -> PyResult<Py<PyAny>> {
        let bars = self
            .client
            .get_security_bars_all(category, market, code, count, fq)
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

    /// 获取指数K线
    #[pyo3(signature = (category, market, code, start=0, count=800, fq=1))]
    fn get_index_bars(
        &self,
        py: Python<'_>,
        category: u8,
        market: u8,
        code: &str,
        start: u32,
        count: u16,
        fq: u8,
    ) -> PyResult<Py<PyAny>> {
        let bars = self
            .client
            .get_index_bars(category, market, code, start, count, fq)
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
            dict.set_item("up_count", b.up_count)?;
            dict.set_item("down_count", b.down_count)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取指数K线 (自动分页)
    #[pyo3(signature = (category, market, code, count=800, fq=1))]
    fn get_index_bars_all(
        &self,
        py: Python<'_>,
        category: u8,
        market: u8,
        code: &str,
        count: u16,
        fq: u8,
    ) -> PyResult<Py<PyAny>> {
        let bars = self
            .client
            .get_index_bars_all(category, market, code, count, fq)
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
            dict.set_item("up_count", b.up_count)?;
            dict.set_item("down_count", b.down_count)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取实时行情
    fn get_security_quotes(
        &self,
        py: Python<'_>,
        all_stock: Vec<(u8, String)>,
    ) -> PyResult<Py<PyAny>> {
        let refs: Vec<(u8, &str)> = all_stock.iter().map(|(m, c)| (*m, c.as_str())).collect();
        let quotes = self
            .client
            .get_security_quotes(&refs)
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
            dict.set_item("servertime", &q.servertime)?;
            dict.set_item("vol", q.vol)?;
            dict.set_item("cur_vol", q.cur_vol)?;
            dict.set_item("amount", q.amount)?;
            dict.set_item("s_vol", q.s_vol)?;
            dict.set_item("b_vol", q.b_vol)?;
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
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取证券列表
    #[pyo3(signature = (market, start=0))]
    fn get_security_list(
        &self,
        py: Python<'_>,
        market: u8,
        start: u16,
    ) -> PyResult<Py<PyAny>> {
        let list_data = self
            .client
            .get_security_list(market, start)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for s in &list_data {
            let dict = PyDict::new(py);
            dict.set_item("code", &s.code)?;
            dict.set_item("volunit", s.volunit)?;
            dict.set_item("decimal_point", s.decimal_point)?;
            dict.set_item("name", &s.name)?;
            dict.set_item("pre_close", s.pre_close)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取证券数量
    fn get_security_count(&self, market: u8) -> PyResult<u16> {
        self.client
            .get_security_count(market)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    /// 获取分时数据
    fn get_minute_time_data(
        &self,
        py: Python<'_>,
        market: u8,
        code: &str,
    ) -> PyResult<Py<PyAny>> {
        let data = self
            .client
            .get_minute_time_data(market, code)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for d in &data {
            let dict = PyDict::new(py);
            dict.set_item("price", d.price)?;
            dict.set_item("vol", d.vol)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取历史分时数据
    fn get_history_minute_time_data(
        &self,
        py: Python<'_>,
        market: u8,
        code: &str,
        date: u32,
    ) -> PyResult<Py<PyAny>> {
        let data = self
            .client
            .get_history_minute_time_data(market, code, date)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for d in &data {
            let dict = PyDict::new(py);
            dict.set_item("price", d.price)?;
            dict.set_item("vol", d.vol)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取逐笔成交
    #[pyo3(signature = (market, code, start=0, count=2000))]
    fn get_transaction_data(
        &self,
        py: Python<'_>,
        market: u8,
        code: &str,
        start: u16,
        count: u16,
    ) -> PyResult<Py<PyAny>> {
        let data = self
            .client
            .get_transaction_data(market, code, start, count)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for d in &data {
            let dict = PyDict::new(py);
            dict.set_item("time", &d.time)?;
            dict.set_item("price", d.price)?;
            dict.set_item("vol", d.vol)?;
            dict.set_item("num", d.num)?;
            dict.set_item("buyorsell", d.buyorsell)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取历史逐笔成交
    #[pyo3(signature = (market, code, start=0, count=2000, date=0))]
    fn get_history_transaction_data(
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
            .get_history_transaction_data(market, code, start, count, date)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for d in &data {
            let dict = PyDict::new(py);
            dict.set_item("time", &d.time)?;
            dict.set_item("price", d.price)?;
            dict.set_item("vol", d.vol)?;
            dict.set_item("buyorsell", d.buyorsell)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取财务信息
    fn get_finance_info(
        &self,
        py: Python<'_>,
        market: u8,
        code: &str,
    ) -> PyResult<Py<PyAny>> {
        let info = self
            .client
            .get_finance_info(market, code)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let dict = PyDict::new(py);
        dict.set_item("market", info.market)?;
        dict.set_item("code", &info.code)?;
        dict.set_item("liutongguben", info.liutongguben)?;
        dict.set_item("province", info.province)?;
        dict.set_item("industry", info.industry)?;
        dict.set_item("updated_date", info.updated_date)?;
        dict.set_item("ipo_date", info.ipo_date)?;
        dict.set_item("zongguben", info.zongguben)?;
        dict.set_item("guojiagu", info.guojiagu)?;
        dict.set_item("faqirenfarengu", info.faqirenfarengu)?;
        dict.set_item("farengu", info.farengu)?;
        dict.set_item("bgu", info.bgu)?;
        dict.set_item("hgu", info.hgu)?;
        dict.set_item("zhigonggu", info.zhigonggu)?;
        dict.set_item("zongzichan", info.zongzichan)?;
        dict.set_item("liudongzichan", info.liudongzichan)?;
        dict.set_item("gudingzichan", info.gudingzichan)?;
        dict.set_item("wuxingzichan", info.wuxingzichan)?;
        dict.set_item("gudongrenshu", info.gudongrenshu)?;
        dict.set_item("liudongfuzhai", info.liudongfuzhai)?;
        dict.set_item("changqifuzhai", info.changqifuzhai)?;
        dict.set_item("zibengongjijin", info.zibengongjijin)?;
        dict.set_item("jingzichan", info.jingzichan)?;
        dict.set_item("zhuyingshouru", info.zhuyingshouru)?;
        dict.set_item("zhuyinglirun", info.zhuyinglirun)?;
        dict.set_item("yingshouzhangkuan", info.yingshouzhangkuan)?;
        dict.set_item("yingyelirun", info.yingyelirun)?;
        dict.set_item("touzishouyu", info.touzishouyu)?;
        dict.set_item("jingyingxianjinliu", info.jingyingxianjinliu)?;
        dict.set_item("zongxianjinliu", info.zongxianjinliu)?;
        dict.set_item("cunhuo", info.cunhuo)?;
        dict.set_item("lirunzonghe", info.lirunzonghe)?;
        dict.set_item("shuihoulirun", info.shuihoulirun)?;
        dict.set_item("jinglirun", info.jinglirun)?;
        dict.set_item("weifenpeilirun", info.weifenpeilirun)?;
        dict.set_item("meigujingzichan", info.meigujingzichan)?;
        Ok(dict.into())
    }

    /// 获取除权除息
    fn get_xdxr_info(
        &self,
        py: Python<'_>,
        market: u8,
        code: &str,
    ) -> PyResult<Py<PyAny>> {
        let data = self
            .client
            .get_xdxr_info(market, code)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for d in &data {
            let dict = PyDict::new(py);
            dict.set_item("year", d.year)?;
            dict.set_item("month", d.month)?;
            dict.set_item("day", d.day)?;
            dict.set_item("category", d.category)?;
            dict.set_item("name", &d.name)?;
            dict.set_item("fenhong", d.fenhong)?;
            dict.set_item("peigujia", d.peigujia)?;
            dict.set_item("songzhuangu", d.songzhuangu)?;
            dict.set_item("peigu", d.peigu)?;
            dict.set_item("suogu", d.suogu)?;
            dict.set_item("panqianliutong", d.panqianliutong)?;
            dict.set_item("panhouliutong", d.panhouliutong)?;
            dict.set_item("qianzongguben", d.qianzongguben)?;
            dict.set_item("houzongguben", d.houzongguben)?;
            dict.set_item("fenshu", d.fenshu)?;
            dict.set_item("xingquanjia", d.xingquanjia)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取并解析板块信息
    fn get_and_parse_block_info(
        &self,
        py: Python<'_>,
        block_file: &str,
    ) -> PyResult<Py<PyAny>> {
        let data = self
            .client
            .get_and_parse_block_info(block_file)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for d in &data {
            let dict = PyDict::new(py);
            dict.set_item("blockname", &d.blockname)?;
            dict.set_item("block_type", d.block_type)?;
            dict.set_item("code_index", d.code_index)?;
            dict.set_item("code", &d.code)?;
            list.append(dict)?;
        }
        Ok(list.into())
    }

    /// 获取K线数据，返回 list of tuple (高性能模式)
    /// tuple: (open, close, high, low, vol, amount, year, month, day, hour, minute, datetime)
    #[pyo3(signature = (category, market, code, start=0, count=800, fq=1))]
    fn get_security_bars_tuples(
        &self,
        py: Python<'_>,
        category: u8,
        market: u8,
        code: &str,
        start: u32,
        count: u16,
        fq: u8,
    ) -> PyResult<Py<PyAny>> {
        let bars = self
            .client
            .get_security_bars(category, market, code, start, count, fq)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for b in &bars {
            let items: Vec<Py<PyAny>> = vec![
                b.open.into_py_any(py)?, b.close.into_py_any(py)?,
                b.high.into_py_any(py)?, b.low.into_py_any(py)?,
                b.vol.into_py_any(py)?, b.amount.into_py_any(py)?,
                b.year.into_py_any(py)?, b.month.into_py_any(py)?,
                b.day.into_py_any(py)?, b.hour.into_py_any(py)?,
                b.minute.into_py_any(py)?, b.datetime.as_str().into_py_any(py)?,
            ];
            let tuple = PyTuple::new(py, &items)?;
            list.append(tuple)?;
        }
        Ok(list.into())
    }

    /// 获取指数K线，返回 list of tuple (高性能模式)
    /// tuple: (open, close, high, low, vol, amount, year, month, day, hour, minute, datetime, up_count, down_count)
    #[pyo3(signature = (category, market, code, start=0, count=800, fq=1))]
    fn get_index_bars_tuples(
        &self,
        py: Python<'_>,
        category: u8,
        market: u8,
        code: &str,
        start: u32,
        count: u16,
        fq: u8,
    ) -> PyResult<Py<PyAny>> {
        let bars = self
            .client
            .get_index_bars(category, market, code, start, count, fq)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for b in &bars {
            let items: Vec<Py<PyAny>> = vec![
                b.open.into_py_any(py)?, b.close.into_py_any(py)?,
                b.high.into_py_any(py)?, b.low.into_py_any(py)?,
                b.vol.into_py_any(py)?, b.amount.into_py_any(py)?,
                b.year.into_py_any(py)?, b.month.into_py_any(py)?,
                b.day.into_py_any(py)?, b.hour.into_py_any(py)?,
                b.minute.into_py_any(py)?, b.datetime.as_str().into_py_any(py)?,
                b.up_count.into_py_any(py)?, b.down_count.into_py_any(py)?,
            ];
            let tuple = PyTuple::new(py, &items)?;
            list.append(tuple)?;
        }
        Ok(list.into())
    }

    /// 获取实时行情，返回 list of tuple (高性能模式)
    /// tuple: (market, code, price, last_close, open, high, low, vol, cur_vol, amount,
    ///         s_vol, b_vol, bid1, bid_vol1, ask1, ask_vol1, ..., bid5, bid_vol5, ask5, ask_vol5)
    fn get_security_quotes_tuples(
        &self,
        py: Python<'_>,
        all_stock: Vec<(u8, String)>,
    ) -> PyResult<Py<PyAny>> {
        let refs: Vec<(u8, &str)> = all_stock.iter().map(|(m, c)| (*m, c.as_str())).collect();
        let quotes = self
            .client
            .get_security_quotes(&refs)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let list = PyList::empty(py);
        for q in &quotes {
            let items: Vec<Py<PyAny>> = vec![
                q.market.into_py_any(py)?, q.code.as_str().into_py_any(py)?,
                q.price.into_py_any(py)?, q.last_close.into_py_any(py)?,
                q.open.into_py_any(py)?, q.high.into_py_any(py)?, q.low.into_py_any(py)?,
                q.vol.into_py_any(py)?, q.cur_vol.into_py_any(py)?, q.amount.into_py_any(py)?,
                q.s_vol.into_py_any(py)?, q.b_vol.into_py_any(py)?,
                q.bid1.into_py_any(py)?, q.bid_vol1.into_py_any(py)?,
                q.ask1.into_py_any(py)?, q.ask_vol1.into_py_any(py)?,
                q.bid2.into_py_any(py)?, q.bid_vol2.into_py_any(py)?,
                q.ask2.into_py_any(py)?, q.ask_vol2.into_py_any(py)?,
                q.bid3.into_py_any(py)?, q.bid_vol3.into_py_any(py)?,
                q.ask3.into_py_any(py)?, q.ask_vol3.into_py_any(py)?,
                q.bid4.into_py_any(py)?, q.bid_vol4.into_py_any(py)?,
                q.ask4.into_py_any(py)?, q.ask_vol4.into_py_any(py)?,
                q.bid5.into_py_any(py)?, q.bid_vol5.into_py_any(py)?,
                q.ask5.into_py_any(py)?, q.ask_vol5.into_py_any(py)?,
            ];
            let tuple = PyTuple::new(py, &items)?;
            list.append(tuple)?;
        }
        Ok(list.into())
    }

    // ============================================================
    // DataFrame 输出 (列式, 高性能)
    // ============================================================

    /// 获取K线数据, 返回 pandas DataFrame
    #[pyo3(signature = (category, market, code, start=0, count=800, fq=1))]
    fn get_security_bars_dataframe(
        &self, py: Python<'_>, category: u8, market: u8, code: &str,
        start: u32, count: u16, fq: u8,
    ) -> PyResult<Py<PyAny>> {
        let bars = self.client
            .get_security_bars(category, market, code, start, count, fq)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        crate::python::py_dataframe::security_bars_to_df(py, &bars)
    }

    /// 获取指数K线, 返回 pandas DataFrame
    #[pyo3(signature = (category, market, code, start=0, count=800, fq=1))]
    fn get_index_bars_dataframe(
        &self, py: Python<'_>, category: u8, market: u8, code: &str,
        start: u32, count: u16, fq: u8,
    ) -> PyResult<Py<PyAny>> {
        let bars = self.client
            .get_index_bars(category, market, code, start, count, fq)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        crate::python::py_dataframe::index_bars_to_df(py, &bars)
    }

    /// 获取实时行情, 返回 pandas DataFrame
    fn get_security_quotes_dataframe(
        &self, py: Python<'_>, all_stock: Vec<(u8, String)>,
    ) -> PyResult<Py<PyAny>> {
        let refs: Vec<(u8, &str)> = all_stock.iter().map(|(m, c)| (*m, c.as_str())).collect();
        let quotes = self.client
            .get_security_quotes(&refs)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        crate::python::py_dataframe::quotes_to_df(py, &quotes)
    }

    /// 获取多只股票的财务信息, 返回 pandas DataFrame
    fn get_finance_info_dataframe(
        &self, py: Python<'_>, stocks: Vec<(u8, String)>,
    ) -> PyResult<Py<PyAny>> {
        let mut infos = Vec::new();
        for (market, code) in &stocks {
            let info = self.client
                .get_finance_info(*market, code)
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
            infos.push((info,));
        }
        crate::python::py_dataframe::finance_to_df(py, &infos)
    }
}
