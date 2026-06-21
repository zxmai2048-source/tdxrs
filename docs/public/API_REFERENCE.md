# tdxrs API 参考

> 本文档覆盖 Python 公开 API。Rust 侧 API 请参见源码文档注释。
>
> 版本: v0.5.0 | 更新日期: 2026-06-21

---

## 快速索引

| 功能 | 对应章节 |
|------|---------|
| K线数据 (核心) | [TdxHqClient — K线](#数据获取--k线) |
| K线种类 | [category 对照表](#k线种类-category) |
| 复权 | [fq 参数](#复权类型-fq) |
| 实时行情 | [TdxHqClient — 实时行情](#数据获取--实时行情) |
| 分时 / 逐笔 | [TdxHqClient — 分时与逐笔](#数据获取--分时与逐笔) |
| 财务 / 除权 / 板块 | [TdxHqClient — 财务与除权](#数据获取--财务与除权) |
| 连接池 / 服务器管理 | [TdxHqClient — 连接管理](#连接管理) |
| 裸连接方案 | [TdxDirectClient](#tdxdirectclient) |
| ETF 数据 | [TdxHqEtfClient](#tdxhqetfclient) |
| F10 公司资料 | [TdxF10Client](#tdxf10client) |
| 本地文件 | [Reader 类](#reader-类) |
| 常量 | [常量子模块](#常量-tdxrsconstants) |

---

## Reader 类

### DailyBarReader

日线数据解析器（`.day` 文件）。

```python
from tdxrs import DailyBarReader
reader = DailyBarReader(coefficient=0.01)
```

| 参数 | 类型 | 默认 | 说明 |
|------|------|:--:|------|
| `coefficient` | float | 0.01 | 价格系数: A股=0.01, B股=0.001, 指数=0.01 |

| 方法 | 返回 | 说明 |
|------|------|------|
| `parse_data(data: bytes)` | `list[dict]` | 解析二进制日线数据 |
| `parse_file(path: str)` | `list[dict]` | 从文件读取并解析 |
| `parse_data_tuples(data: bytes)` | `list[tuple]` | 解析为 tuple 列表 (高性能) |
| `parse_file_tuples(path: str)` | `list[tuple]` | 文件 → tuple 列表 |
| `to_dataframe(data: bytes)` | `DataFrame` | 解析为 pandas DataFrame |
| `to_dataframe_file(path: str)` | `DataFrame` | 文件 → DataFrame |

**返回字段 (dict 模式)**: `date`, `open`, `high`, `low`, `close`, `amount`, `volume`, `year`, `month`, `day`

**Tuple 顺序**: `(date, open, high, low, close, amount, volume, year, month, day)`

### MinBarReader / LcMinBarReader

分钟线解析器（`.lc5` / `.lc1` 文件）。

```python
from tdxrs import MinBarReader, LcMinBarReader
```

| Reader | 格式 | 适用 |
|--------|------|------|
| MinBarReader | 整数价格 (×1000) | 常规 5 分钟线 |
| LcMinBarReader | 浮点价格 | LC 格式分钟线 |

| 方法 | 返回 | 说明 |
|------|------|------|
| `parse_data(data: bytes)` | `list[dict]` | 解析分钟线二进制数据 |
| `parse_file(path: str)` | `list[dict]` | 从文件读取并解析 |
| `parse_data_tuples(data: bytes)` | `list[tuple]` | 高性能 tuple 模式 |
| `parse_file_tuples(path: str)` | `list[tuple]` | 文件 → tuple |
| `to_dataframe(data: bytes)` | `DataFrame` | → pandas DataFrame |

返回额外字段: `hour`, `minute`

### BlockReader

板块数据解析器（`.dat` 文件）。

```python
from tdxrs import BlockReader
reader = BlockReader()
```

| 方法 | 返回 | 说明 |
|------|------|------|
| `parse_data(data: bytes)` | `list[dict]` | 扁平模式 (每只股票一行) |
| `parse_data_group(data: bytes)` | `list[dict]` | 分组模式 (每板块一行) |
| `parse_file(path: str)` | `list[dict]` | 从文件读取并解析 |

### FinancialReader

财务 gpcw 数据解析器。

```python
from tdxrs import FinancialReader
reader = FinancialReader()
```

| 方法 | 返回 | 说明 |
|------|------|------|
| `parse_data(data: bytes)` | `list[dict]` | 解析 gpcw 二进制财务数据 |
| `parse_file(path: str)` | `list[dict]` | 从文件读取并解析 |

返回: `[{"code": str, "report_date": int, "fields": [float, ...]}, ...]`

> `fields` 为 f32 财务指标值数组。部分字段含义待验证。

---

## 客户端类

### TdxHqClient

连接池行情客户端（主力）。支持自动心跳、断线重连、数据缓存、自动分页。

```python
from tdxrs import TdxHqClient
client = TdxHqClient()
```

#### 连接管理

| 方法 | 返回 | 说明 |
|------|------|------|
| `connect(ip, port, timeout=None)` | `bool` | 连接到指定服务器 |
| `connect_to_any(timeout=None)` | `bool` | 自动探测可用服务器 (优先→主→全部三级遍历) |
| `disconnect()` | — | 断开连接、停止心跳、清空连接池 |
| `is_connected()` | `bool` | 是否已连接 |

```python
client = TdxHqClient()
# 自动选择可用服务器 (推荐)
client.connect_to_any()
# 或指定服务器
client.connect("119.147.212.81", 7709, timeout=5.0)
```

#### 服务器管理

| 方法 | 说明 |
|------|------|
| `set_servers(servers: list[(name, ip, port)])` | 替换自定义优先服务器列表 |
| `add_server(name, ip, port)` | 在优先列表头部插入一台 |
| `reorder_servers(results)` | 按 `probe_servers()` 排序结果重排优先列表 |
| `probe_servers(timeout=3.0)` → `list[(name, ip, port, tcp_ms, hs_ms, api_ms)]` | 探测全部已知服务器，返回延迟排序 |

#### 配置

| 方法 | 说明 |
|------|------|
| `set_auto_retry(enabled: bool)` | 启用/禁用内置重试 (生产环境建议关闭，用上层重试) |
| `set_cache_ttl(secs: int)` | 缓存有效期 (秒)，影响 `get_security_count` / `get_security_list` |
| `set_connect_timeout(secs: float)` | 连接超时 (秒) |
| `pool_stats()` → `{"idle": int, "active": int, "total": int, "max_size": int}` | 连接池状态 |

---

#### 数据获取 — K线

K 线是 tdxrs 核心功能，提供个股和指数的 OHLCV 数据。

##### 方法签名

```python
# 个股 K 线
get_security_bars(category, market, code, start=0, count=800, fq=1) -> list[dict]
get_security_bars_all(category, market, code, count=800, fq=1) -> list[dict]

# 指数 K 线 — 指数不存在复权概念，fq 参数无论传什么值均强制为 0
get_index_bars(category, market, code, start=0, count=800, fq=0) -> list[dict]
get_index_bars_all(category, market, code, count=800, fq=0) -> list[dict]

# DataFrame 模式 (直出 pandas)
get_security_bars_dataframe(category, market, code, start=0, count=800, fq=1) -> DataFrame
get_index_bars_dataframe(category, market, code, start=0, count=800, fq=0) -> DataFrame

# Tuple 高性能模式
get_security_bars_tuples(category, market, code, start=0, count=800, fq=1) -> list[tuple]
get_index_bars_tuples(category, market, code, start=0, count=800, fq=0) -> list[tuple]
```

##### 参数说明

| 参数 | 类型 | 默认 | 说明 |
|------|------|:--:|------|
| `category` | int | — | K 线种类，见下方 [对照表](#k线种类-category) |
| `market` | int | — | 市场代码，见 [市场代码](#市场代码) |
| `code` | str | — | 股票代码或指数代码，如 `"600519"` `"300750"` `"000001"` |
| `start` | int | 0 | 起始偏移位置 (0=最新数据开始)。设为 N 则跳过最近 N 根 |
| `count` | int | 800 | 请求数量。单次上限受 `MAX_KLINE_COUNT`(800) 限制 |
| `fq` | int | 1 | 复权类型（指数 K 线忽略此参数，强制 fq=0），见下方 |

##### 分页机制

TDX 服务端单次最多返回 **800 根** K 线。如需更多：

| 方法 | 行为 |
|------|------|
| `get_security_bars(..., count=N)` | 单次请求，N > 800 会被服务端截断为 800 |
| `get_security_bars_all(..., count=N)` | 自动分页，内部循环请求直到获取 N 根或数据耗尽 |

```python
# 获取全部历史数据 (自动分页)
all_bars = client.get_security_bars_all(KLINE_DAILY, MARKET_SH, "600519", count=5000)

# 手动分页 (精确控制)
bars = client.get_security_bars(KLINE_DAILY, MARKET_SH, "600519", start=0, count=800)
more = client.get_security_bars(KLINE_DAILY, MARKET_SH, "600519", start=800, count=800)
```

##### K线种类 (category)

| 值 | Python 常量 | 含义 | 支持 fq=0 | 说明 |
|:--:|------|------|:--:|------|
| 0 | `KLINE_5MIN` | 5 分钟线 | ✅ | — |
| 1 | `KLINE_15MIN` | 15 分钟线 | ✅ | — |
| 2 | `KLINE_30MIN` | 30 分钟线 | ✅ | — |
| 3 | `KLINE_1HOUR` | 60 分钟线 | ✅ | — |
| 4 | `KLINE_DAILY` | 日 K 线 (完整) | ✅ | **推荐用于日线**。vol=股数 |
| 5 | `KLINE_WEEKLY` | 周 K 线 | ✅ | — |
| 6 | `KLINE_MONTHLY` | 月 K 线 | ✅ | — |
| 7 | `KLINE_EXHQ_1MIN` | 扩展 1 分钟线 | ✅ | — |
| 8 | `KLINE_1MIN` | 1 分钟线 | ✅ | — |
| 9 | `KLINE_RI_K` | 日 K 线 (精简) | ❌ | 不支持 fq=0。vol=**手数** (÷100)。含分钟字段 |
| 10 | `KLINE_3MONTH` | 季 K 线 | ✅ | — |
| 11 | `KLINE_YEARLY` | 年 K 线 | ✅ | — |

> **推荐**: 日线使用 `category=4` (`KLINE_DAILY`) 而非 `category=9`，因为前者支持未复权 (`fq=0`) 查询。

##### 复权类型 (fq)

| 值 | Python 常量 | 名称 | 行为 |
|:--:|------|------|------|
| 0 | `FQ_NONE` | 未复权 | 返回交易所原始价格。除权除息日会出现价格跳空。仅 `category=4` 支持。 |
| 1 | `FQ_QFQ` | **前复权** (默认) | 历史价格按后续除权因子向下调整，最新价保持不变。适合技术分析和回测。 |
| 2 | `FQ_HFQ` | 后复权 | 近期价格按历史除权因子向上调整，首日价保持不变。 |

```python
# 前复权 (默认)
bars = client.get_security_bars(4, 1, "600519", 0, 100, fq=1)

# 未复权 (原始数据)
raw = client.get_security_bars(4, 1, "600519", 0, 100, fq=0)

# 后复权
hfq = client.get_security_bars(4, 1, "600519", 0, 100, fq=2)
```

> **实现**: `fq>0` 时客户端自动拉取 `get_xdxr_info()` 获取除权除息历史，调用 `src/protocol/adjuster.rs` 在客户端侧完成复权计算。`fq=0` 不触发除权查询，零额外开销。详参 [复权算法文档](../ADJUSTER_ALGORITHM.md)。

##### 返回字段

**个股 K 线 (SecurityBar)**:

| 字段 (dict key) | 类型 | 说明 |
|------|:--:|------|
| `open` | float | 开盘价 |
| `close` | float | 收盘价 |
| `high` | float | 最高价 |
| `low` | float | 最低价 |
| `vol` | float | 成交量 (股数, category=9 时为手数) |
| `amount` | float | 成交额 (元) |
| `year` | int | 年份 |
| `month` | int | 月份 |
| `day` | int | 日 |
| `hour` | int | 时 (日线为 0) |
| `minute` | int | 分 (日线为 0) |
| `datetime` | str | ISO 格式日期时间 "YYYY-MM-DD HH:MM" |

**Tuple 顺序**: `(open, close, high, low, vol, amount, year, month, day, hour, minute, datetime)`

**DataFrame 列名**: `open`, `close`, `high`, `low`, `vol`, `amount`, `year`, `month`, `day`, `hour`, `minute`, `datetime`

**指数 K 线 (IndexBar)**: 在 SecurityBar 基础上增加 (vol 单位同样分 cat=4 股数 / cat=9 手数):

| 字段 (dict key) | 类型 | 说明 |
|------|:--:|------|
| `up_count` | int | 上涨家数 |
| `down_count` | int | 下跌家数 |

##### 批量获取示例

```python
from tdxrs import TdxHqClient
from tdxrs.constants import MARKET_SH, MARKET_SZ, KLINE_DAILY, KLINE_WEEKLY, FQ_QFQ, FQ_NONE

client = TdxHqClient()
client.connect_to_any()

# 1. 贵州茅台最近 200 条前复权日K线 → DataFrame
df = client.get_security_bars_dataframe(KLINE_DAILY, MARKET_SH, "600519", 0, 200, FQ_QFQ)

# 2. 多只股票批量获取 (tuple 高性能模式)
stocks = [(MARKET_SH, "600519"), (MARKET_SZ, "000858"), (MARKET_SZ, "300750")]
for mkt, code in stocks:
    bars = client.get_security_bars_tuples(KLINE_DAILY, mkt, code, 0, 100)
    print(f"{code}: {len(bars)} bars")

# 3. 指数周K线 + 全部历史 (指数不复权，fq 被忽略)
index_bars = client.get_index_bars_all(KLINE_WEEKLY, MARKET_SH, "000001", count=5000)

# 4. 未复权原始数据 (用于除权研究)
raw = client.get_security_bars(KLINE_DAILY, MARKET_SH, "600519", 0, 100, FQ_NONE)

# 5. 准确获取最后 N 条 — 用 start=0
latest_50 = client.get_security_bars(KLINE_DAILY, MARKET_SH, "600519", start=0, count=50)

client.disconnect()
```

##### 获取更多历史数据

```python
# count > 800 时使用 _all 方法
all_daily = client.get_security_bars_all(KLINE_DAILY, MARKET_SH, "600519", count=5000)

# start > 0 跳过最近 N 条，获取更早数据
older = client.get_security_bars(KLINE_DAILY, MARKET_SH, "600519", start=800, count=800)
```

---

#### 数据获取 — 实时行情

```python
get_security_quotes(stocks: list[(market, code)]) -> list[dict]
get_security_quotes_dataframe(stocks) -> DataFrame
get_security_quotes_tuples(stocks) -> list[tuple]
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `stocks` | `list[(market, code)]` | 股票列表，如 `[(1, "600519"), (0, "000858")]` |

**返回字段 (dict)**: `market`, `code`, `price`, `last_close`, `open`, `high`, `low`, `vol`, `cur_vol`, `amount`, `s_vol`, `b_vol`, `bid1`～`bid5`, `ask1`～`ask5`, `bid_vol1`～`bid_vol5`, `ask_vol1`～`ask_vol5`, `servertime`

> 行情无缓存，每次实时查询。

```python
# 单只
q = client.get_security_quotes([(1, "600519")])
print(q[0]["price"], q[0]["bid1"])

# 批量
quotes = client.get_security_quotes([
    (1, "600519"), (0, "000858"), (0, "300750")
])
for q in quotes:
    print(f"{q['code']}: {q['price']} (昨收{q['last_close']})")

# DataFrame
df = client.get_security_quotes_dataframe([
    (1, "600519"), (0, "000858")
])
```

---

#### 数据获取 — 证券信息

```python
get_security_list(market, start=0) -> list[dict]
get_security_count(market) -> int
```

**缓存**: `start=0` 时 `get_security_list` 和 `get_security_count` 使用 TTL 缓存 (默认 30s)。非 0 偏移不缓存。

**get_security_list 返回字段**: `code`, `name`, `pre_close`, `volunit`, `decimal_point`

```python
# 上海市场证券数量
count = client.get_security_count(MARKET_SH)

# 深圳市场证券列表 (第一页)
stocks = client.get_security_list(MARKET_SZ, start=0)

# 翻页
page2 = client.get_security_list(MARKET_SZ, start=1000)
```

---

#### 数据获取 — 分时与逐笔

```python
# 分时数据
get_minute_time_data(market, code) -> list[dict]             # 当日
get_history_minute_time_data(market, code, date) -> list[dict]  # 历史

# 逐笔成交
get_transaction_data(market, code, start=0, count=2000) -> list[dict]             # 当日
get_history_transaction_data(market, code, start, count, date) -> list[dict]    # 历史
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `market` | int | 市场代码 |
| `code` | str | 股票代码 |
| `start` | int | 起始位移 |
| `count` | int | 请求数量，上限 `MAX_TRANSACTION_COUNT`(2000) |
| `date` | int | 日期，格式 `YYYYMMDD` (如 `20260421`) |

**分时返回**: `[{"price": float, "vol": float}, ...]`

**逐笔返回**: `[{"time": "HH:MM", "price": float, "vol": float, "num": int, "buyorsell": int}, ...]`

---

#### 数据获取 — 财务与除权

```python
# 实时财务 (34 字段)
get_finance_info(market, code) -> dict
get_finance_info_dataframe(stocks: list[(market, code)]) -> DataFrame

# 除权除息
get_xdxr_info(market, code) -> list[dict]

# 板块数据
get_and_parse_block_info(block_file: str) -> list[dict]
```

**场代码**:
| 值 | 常量 | 说明 |
|:--:|------|------|
| 0 | `MARKET_SZ` | 深圳 |
| 1 | `MARKET_SH` | 上海 |
| 2 | `MARKET_BJ` | 北京 |

**`get_finance_info` 返回字段** (34 项, TDX 原始值, 未做单位转换):

| 分类 | 字段 | 含义 | 典型数量级 |
|------|------|------|:--:|
| 股本 | `zongguben` | 总股本 | ~10⁵ (万股) |
| | `liutongguben` | 流通股本 | ~10⁵ (万股) |
| | `guojiagu` / `farengu` / `bgu` / `hgu` | 国家股/法人股/B股/H股 | ~10⁴-10⁵ |
| 资产 | `zongzichan` / `jingzichan` | 总资产 / 净资产 | ~10⁸ (万元) |
| | `liudongzichan` / `gudingzichan` / `wuxingzichan` | 流动/固定/无形资产 | ~10⁷-10⁸ |
| 负债 | `liudongfuzhai` / `changqifuzhai` | 流动/长期负债 | ~10⁷-10⁸ |
| 利润 | `zhuyingshouru` / `zhuyinglirun` | 主营收入 / 主营利润 | ~10⁷-10⁸ |
| | `yingyelirun` / `lirunzonghe` / `jinglirun` | 营业利润 / 利润总额 / 净利润 | ~10⁷ |
| 现金流 | `jingyingxianjinliu` / `zongxianjinliu` | 经营/总现金流 | ~10⁷-10⁸ |
| 其他 | `meigujingzichan` | 每股净资产 (元) | ~10¹-10² |
| | `gudongrenshu` | 股东人数 | ~10⁵ (户) |
| | `updated_date` / `ipo_date` | 更新日期 / 上市日期 | YYYYMMDD |
| | `province` / `industry` | 省份 / 行业代码 | — |

> **v0.5.1 变更**: 所有财务字段现返回 TDX **原始值**，不再做 ×10000 单位转换。不同字段单位可能不同（元/万元/千元），由用户根据实际数据自行判断。45 个英文命名指标请使用 `TdxFinanceClient.get_finance_indicators()` (Rust API)。

### 命名财务指标 (Rust TdxFinanceClient)

从 gpcw 数据中提取 45 个核心财务指标，英文命名，TDX 原始值。

```rust
use tdxrs::net::finance_client::TdxFinanceClient;

let fc = TdxFinanceClient::new("120.76.152.87", 7709, None);
// 获取命名指标 (英文 key)
let ind = fc.get_finance_indicators("gpcw20260331.dat", filesize, "600519")?;
// ind["eps"], ind["roe_weighted"], ind["total_assets"], ...

// 获取带中文标签 (适合校验)
let labeled = fc.get_finance_indicators_labeled("gpcw20260331.dat", filesize, "600519")?;
// (en_name, zh_name, value)
```

**45 个核心指标**:

| 分类 | 字段 (en) | 中文 | gpcw idx |
|------|------|------|:--:|
| 每股 | `eps` | 基本每股收益 | 1 |
| | `bvps` | 每股净资产 | 4 |
| | `ocf_ps` | 每股经营现金流 | 7 |
| 盈利 | `roe_weighted` | 加权净资产收益率 | 281 |
| | `roe_diluted` | 净资产收益率(摊薄) | 6 |
| | `gross_margin` | 销售毛利率 | 202 |
| | `net_margin` | 销售净利率 | 199 |
| | `roa` | 总资产净利率 | 200 |
| | `ebit` / `ebitda` | 息税前利润 / EBITDA | 207/208 |
| 成长 | `revenue_yoy` | 营收增长率 | 183 |
| | `net_profit_yoy` | 净利增长率 | 184 |
| 偿债 | `current_ratio` / `quick_ratio` | 流动/速动比率 | 159/160 |
| | `debt_ratio` | 资产负债率 | 210 |
| 营运 | `asset_turnover` | 总资产周转率 | 175 |
| | `inventory_turnover` | 存货周转率 | 173 |
| 规模 | `total_assets` | 资产总计 | 40 |
| | `revenue` | 营业收入 | 74 |
| | `net_profit_is` | 净利润(利润表) | 95 |
| | `parent_net_profit` | 归母净利润 | 96 |
| | `operating_cf` | 经营活动CF | 107 |
| 其他 | `total_shares` | 总股本 | 238 |
| | `employees` | 员工人数 | 320 |
| | `revenue_ttm` | 营收TTM | 319 |

> 完整 45 字段定义见 `src/protocol/finance_fields.rs::INDICATORS`。部分银行/非银字段可能为 0。未对齐字段（197/134/232）已标注在源码中。

---

### TdxDirectClient

裸连接客户端。每次 API 调用独立建立 TCP 连接 + 握手，无连接池、无重试、无心跳、无缓存。

```python
from tdxrs import TdxDirectClient
dc = TdxDirectClient(ip, port=7709, timeout=5.0)
```

| 方法 | 说明 |
|------|------|
| `TdxDirectClient(ip, port, timeout)` | 构造，设置服务器地址和超时 |
| `set_server(ip, port)` | 更新服务器地址 |
| `set_timeout(secs)` | 更新超时 |
| `get_security_bars(...)` | 个股K线 (同 TdxHqClient 签名) |
| `get_index_bars(...)` | 指数K线 |
| `get_security_quotes(...)` | 实时行情 |
| `get_security_list(...)` | 证券列表 |
| `get_security_count(...)` | 证券数量 |
| `get_minute_time_data(...)` | 分时 |
| `get_history_minute_time_data(...)` | 历史分时 |
| `get_transaction_data(...)` | 逐笔 |
| `get_history_transaction_data(...)` | 历史逐笔 |
| `get_finance_info(...)` | 财务信息 |
| `get_xdxr_info(...)` | 除权除息 |
| `get_and_parse_block_info(...)` | 板块数据 |

**适用场景**:
- 偶发请求 (<1次/分钟)，无需维护长连接
- 高并发 (多线程独立连接，天然并行，60 用户无退化)
- 不需要重试/缓存/心跳的场景

**与 TdxHqClient 差异**:
- ❌ 无 `_all` 自动分页方法
- ❌ 无 `_dataframe` / `_tuples` 直接输出
- ❌ 无 `__init__()` 无参数构造 (必须指定 IP)
- ❌ 无服务器管理、池状态等

```python
dc = TdxDirectClient("119.147.212.81", 7709, timeout=10.0)
bars = dc.get_security_bars(KLINE_DAILY, MARKET_SH, "600519", 0, 100, FQ_QFQ)
dc.set_server("180.153.18.17", 7709)  # 切换服务器
```

---

### TdxHqEtfClient

ETF 行情客户端 (扩展模块)。封装 `TdxHqClient`，自动处理 ETF 代码验证。

```python
from tdxrs.pro import TdxHqEtfClient
from tdxrs.constants import MARKET_SH

client = TdxHqEtfClient()
client.connect_to_any()
```

完整 API 详见 [ETF 模块文档](ETF.md)。

| 方法 | 返回 | 说明 |
|------|------|------|
| `get_etf_list(market)` | `list[dict]` | ETF 列表 |
| `get_etf_bars(cat, mkt, code, start, count)` | `list[dict]` | ETF K线 |
| `get_etf_bars_all(cat, mkt, code, count)` | `list[dict]` | 自动分页 |
| `get_etf_quotes(stocks)` | `list[dict]` | 实时行情 (五档) |
| `get_etf_minute_time_data(mkt, code)` | `list[dict]` | 分时数据 |
| `get_etf_transaction_data(mkt, code, start, count)` | `list[dict]` | 逐笔成交 |
| `get_etf_xdxr_info(mkt, code)` | `list[dict]` | 除权除息 |
| `get_etf_finance_info(mkt, code)` | `dict` | 财务信息 |
| `is_etf(market, code)` | `bool` | 静态: 判断 ETF |
| `auto_market_code(code)` | `int` | 静态: 自动市场 |

---

### TdxF10Client

> ⚠️ 源码编译专用 (`--features f10`)，pip 包不包含此模块。

F10 公司资料客户端。独立连接，不占用共享连接池。

```python
# 需从源码编译: maturin develop --release --features f10
from tdxrs.pro import TdxF10Client

client = TdxF10Client("180.153.18.170", 7709)
```

完整 API 详见 [F10 模块文档](F10.md)。

| 方法 | 返回 | 说明 |
|------|------|------|
| `get_category(market, code)` | `list[dict]` | 分类列表 |
| `get_content(market, code, category_dict)` | `str` | 指定分类内容 |
| `get_all_contents(market, code)` | `dict[str, str]` | 全部内容 |
| `get_all_data(market, code)` | `dict` | 结构化全量数据 |
| `parse_f10(text)` | `dict` | 静态: 解析 F10 文本 |
| `extract_basic_info(text)` | `dict` | 静态: 提取基本资料 |
| `is_valid_code(code)` | `bool` | 静态: 验证代码 |
| `auto_market_code(code)` | `int` | 静态: 自动市场 |

---

## 常量 (`tdxrs.constants`)

```python
from tdxrs.constants import (
    # ═══ 市场代码 ═══
    MARKET_SZ,   # 0 — 深圳
    MARKET_SH,   # 1 — 上海
    MARKET_BJ,   # 2 — 北京

    # ═══ K线种类 (category) ═══
    KLINE_5MIN,      # 0  — 5分钟线
    KLINE_15MIN,     # 1  — 15分钟线
    KLINE_30MIN,     # 2  — 30分钟线
    KLINE_1HOUR,     # 3  — 60分钟线
    KLINE_DAILY,     # 4  — 日K线 (完整, 推荐)
    KLINE_WEEKLY,    # 5  — 周K线
    KLINE_MONTHLY,   # 6  — 月K线
    KLINE_EXHQ_1MIN, # 7  — 扩展1分钟线
    KLINE_1MIN,      # 8  — 1分钟线
    KLINE_RI_K,      # 9  — 日K线 (精简, 不支持fq=0)
    KLINE_3MONTH,    # 10 — 季K线
    KLINE_YEARLY,    # 11 — 年K线

    # ═══ 复权类型 (fq) ═══
    FQ_NONE,  # 0 — 未复权
    FQ_QFQ,   # 1 — 前复权 (默认)
    FQ_HFQ,   # 2 — 后复权

    # ═══ 限制 ═══
    MAX_KLINE_COUNT,        # 800  — 单次K线最大条数
    MAX_TRANSACTION_COUNT,  # 2000 — 单次逐笔最大条数

    # ═══ 默认配置 ═══
    DEFAULT_PORT,          # 7709 — TDX 行情端口
    DEFAULT_POOL_SIZE,     # 5    — 连接池大小
    FQ_PRICE_PRECISION,    # 3    — 复权小数位数
)
```

---

## 输出格式对照

三种输出格式各有适用场景：

| 格式 | 方法后缀 | 速度 | 内存 | 适用 |
|------|:------:|:----:|:----:|------|
| **dict** | (默认) | 基准 | 中等 | 调试、少量数据 |
| **tuple** | `_tuples()` | **快 40-60%** | 低 | 遍历、批量处理 |
| **DataFrame** | `_dataframe()` | 慢 | 高 | 数据分析、回测 |

```python
# dict 模式 — 字段名访问
for bar in client.get_security_bars(4, 1, "600519", 0, 100):
    print(bar["datetime"], bar["close"])

# tuple 模式 — 位置访问, 更快
for t in client.get_security_bars_tuples(4, 1, "600519", 0, 100):
    open_, close, high, low, vol, amount, y, m, d, h, mi, dt = t

# DataFrame — pandas 分析
df = client.get_security_bars_dataframe(4, 1, "600519", 0, 500)
df["ma20"] = df["close"].rolling(20).mean()
```

---

## 最佳实践

### 客户端选择

| 使用场景 | 推荐客户端 | 理由 |
|----------|:--------:|------|
| 单个脚本顺序拉取数千条 K 线 | `TdxHqClient` | 连接复用免握手，4× 快于裸连；`_all` 自动分页 |
| 回测引擎，多线程并发跑不同品种 | `TdxDirectClient` | 每线程独立连接天然并行，60 线程 12× 快于池 |
| Web 服务，单请求单响应 | `TdxHqClient` | 连接复用 + 重试兜底 + 缓存减少网络往返 |
| 定时任务，每 N 分钟查一次行情 | `TdxHqClient` | 心跳保活，免去每次建连 200ms 开销 |
| 一次性查询，用完即弃 | `TdxDirectClient` | 无需管理连接生命周期 |
| 下载 gpcw 历史财务文件 | `TdxFinanceClient` | 独立超时 15s + 磁盘缓存，不与行情连接争抢 |

> 决策要点: 请求是**顺序的**还是**同时并发的**？顺序选池，并发选裸连。需要心跳/重试/缓存/分页 → 池。偶发 → 裸连。
> 详见 [性能基准](BENCHMARKS.md)。

### 高频 K 线调用建议

**1. 重用客户端实例，避免反复 `connect`**

```python
# ✅ 正确: 初始化一次，复用
client = TdxHqClient()
client.connect_to_any()
for code in stock_list:
    bars = client.get_security_bars(4, mkt, code, 0, 100)

# ❌ 错误: 每次循环重新连接
for code in stock_list:
    c = TdxHqClient()
    c.connect_to_any()
    bars = c.get_security_bars(...)
    c.disconnect()
```

**2. 批量请求使用 `_tuples()` 模式**

```python
# ✅ 典型回测场景 — 省 40-60% 时间
for code in watchlist:
    bars = client.get_security_bars_tuples(KLINE_DAILY, mkt, code, 0, 500)
    # bars 是 list[tuple], tuple 解构即用
```

**3. 需要分析时用 `_dataframe()`**

```python
# ✅ 分析场景 — 直出 DataFrame，免手动构造
df = client.get_security_bars_dataframe(KLINE_DAILY, MARKET_SH, "600519", 0, 500)
df["returns"] = df["close"].pct_change()
df["ma20"] = df["close"].rolling(20).mean()
```

**4. 选对 `category`，避免踩坑**

```python
# ✅ 日线 — 用 category=4, 支持未复权
bars = client.get_security_bars(KLINE_DAILY, mkt, code, 0, 800, FQ_QFQ)

# ❌ 日线精简 — category=9, 不支持 fq=0
# 当需要对比原始数据时此选项不可用
```

**5. 需要复权和原始数据对比时**

```python
# 一次获取，两份数据
adjusted = client.get_security_bars(KLINE_DAILY, mkt, code, 0, 800, FQ_QFQ)
raw = client.get_security_bars(KLINE_DAILY, mkt, code, 0, 800, FQ_NONE)
# 可用于验证除权因子: adjusted.close / raw.close = cumulative_factor
```

**6. 多股票行情 — 一次调用批量获取**

```python
# ✅ 批量: 一次网络往返取全部
quotes = client.get_security_quotes([
    (MARKET_SH, "600519"),
    (MARKET_SZ, "000858"),
    (MARKET_SZ, "300750"),
])

# ❌ 逐个: 3 次网络往返
for mkt, code in stocks:
    q = client.get_security_quotes([(mkt, code)])
```

**7. 翻页获取历史数据**

```python
# 方法 A: 自动分页 (简单)
all_bars = client.get_security_bars_all(KLINE_DAILY, mkt, code, count=3000)

# 方法 B: 手动翻页 (精确控制, 可中断)
bars = client.get_security_bars(KLINE_DAILY, mkt, code, start=0, count=800)
older = client.get_security_bars(KLINE_DAILY, mkt, code, start=800, count=800)
oldest = client.get_security_bars(KLINE_DAILY, mkt, code, start=1600, count=800)
```

### 异常处理

```python
from tdxrs import TdxHqClient

client = TdxHqClient()
client.set_auto_retry(False)  # 生产环境关闭内置重试

try:
    client.connect_to_any(timeout=5.0)
except ValueError as e:
    print(f"所有服务器不通: {e}")
    # fallback: 重试或告警
else:
    try:
        bars = client.get_security_bars(KLINE_DAILY, MARKET_SH, "600519", 0, 100)
    except ValueError as e:
        print(f"请求失败: {e}")
        # 可自行重试
finally:
    client.disconnect()
```

### 生产环境配置建议

```python
client = TdxHqClient()
client.set_auto_retry(False)       # 关闭内置重试, 由上层控制
client.set_cache_ttl(120)          # 证券列表缓存延长到 2 分钟
client.set_connect_timeout(3.0)    # 缩短连接超时, 快速失败
client.connect_to_any(timeout=5.0)
```

---

## 注意事项

1. **K线种类选择**: 日线推荐 `category=4` (KLINE_DAILY) 而非 `category=9` (KLINE_RI_K)，前者支持未复权查询。
2. **复权精度**: 价格四舍五入到 `FQ_PRICE_PRECISION`(3) 位小数，成交量不调整。
3. **分页上限**: 单次 `count > 800` 请求会被截断，使用 `_all` 方法自动分页。
4. **连接管理**: 长时间不用连接池会自动心跳保活 (10s)，生产环境建议关闭 `set_auto_retry(False)` 用上层重试逻辑。
5. **并发**: 高并发场景推荐 `TdxDirectClient` (每线程独立连接)，连接池在高并发下退化严重。
6. **异步**: `AsyncTdxHqClient` 暂无 Python 绑定，需通过 Rust 侧调用。

---

## 安装

```bash
pip install maturin
git clone <repo-url> && cd tdxrs
maturin develop --release
```

详细安装说明见 [INSTALL.md](../INSTALL.md)。
