# tdxrs Python 最佳实践

> 面向实际使用场景的调用指南。侧重限流规则、客户端选择、性能优化、常见反模式。
>
> 完整 API 列表请参见 [API 参考](API_REFERENCE.md)。
>
> 版本: v0.6.5 | 更新日期: 2026-07-02

---

## 目录

1. [客户端选择](#1-客户端选择)
2. [限流规则](#2-限流规则)
3. [输出格式选择](#3-输出格式选择)
4. [批量请求优化](#4-批量请求优化)
5. [基金数据获取](#5-基金数据获取)
6. [配置建议](#6-配置建议)
7. [常见反模式](#7-常见反模式)
8. [场景速查表](#8-场景速查表)

---

## 1. 客户端选择

tdxrs 提供 3 种行情客户端，适用于不同场景：

| 客户端 | 连接方式 | 并发能力 | 适用场景 |
|--------|----------|----------|----------|
| `TdxHqClient` | 连接池 (5) | 中 | **首选**。通用场景，自动心跳/重连/缓存 |
| `AsyncTdxHqClient` | 通道化连接池 (4) | 高 | 批量并发请求，tokio 生态集成 |
| `TdxDirectClient` | 每次新建 TCP | 高 (多线程) | 偶发请求，无状态场景 |

**选择原则**:

- **不确定用哪个** → `TdxHqClient`。它是主力客户端，覆盖 90% 场景。
- **需要批量并发** → `AsyncTdxHqClient`。4 连接通道化池，连接间真正并行。
- **偶发一次性请求** → `TdxDirectClient`。无连接池开销，用完即弃。

```python
# 通用场景 — 首选
from tdxrs import TdxHqClient
client = TdxHqClient()
client.connect_to_any()

# 批量并发 — 多只股票同时查询
from tdxrs import AsyncTdxHqClient
aclient = AsyncTdxHqClient()
aclient.connect_to_any()

# 偶发请求 — 无需维护连接
from tdxrs import TdxDirectClient
dc = TdxDirectClient("180.153.18.170", 7709)
```

---

## 2. 限流规则

### 2.1 三档自动限流

tdxrs 根据交易时段自动调整请求速率，保护服务器：

| 时段 | RPS (每连接) | 4 连接池实际吞吐 | 触发条件 |
|------|:---:|:---:|------|
| **Trading** (盘中) | 15 | 60 | 工作日 9:30-15:00 |
| **PrePost** (盘前盘后) | 30 | 120 | 工作日其他时段 |
| **Closed** (休市) | 60 | 240 | 周末 / 节假日 |

> 限流基于本地时间 (UTC+8)，不考量法定假期。盘中时段按 9:30-15:00 整段计算，不区分午盘休息。

### 2.2 限流是按请求计数，不是按股票计数

```python
# 这是 1 次请求 (批量查询 5 只股票)
quotes = client.get_security_quotes([
    (1, "600519"), (0, "000858"), (0, "300750"),
    (1, "601318"), (0, "000001"),
])

# 这是 5 次请求 (循环调用，每只股票 1 次)
for market, code in stocks:
    q = client.get_security_quotes([(market, code)])  # ❌ 浪费
```

**批量接口** (`get_security_quotes` 接受列表) 只算 1 次请求。循环调用每只股票算 N 次。

### 2.3 手动调整限流

```python
client = TdxHqClient()
client.connect_to_any()

# 查看当前阶段
phase = client.auto_detect_phase()  # 仅 AsyncTdxHqClient

# 手动设置 RPS (上限 200)
client.set_rate_limit(100)       # 通用接口
client.set_rate_limit_daily(30)  # 日K 接口

# 关闭限流 (不推荐，可能触发服务器封禁)
client.set_rate_limit(0)
```

### 2.4 AsyncTdxHqClient 限流配置

```python
aclient = AsyncTdxHqClient()
aclient.connect_to_any()

# 自动检测交易阶段
phase = aclient.auto_detect_phase()
print(f"当前阶段: {phase}")  # "closed" / "trading" / "prepost"

# 手动指定阶段
aclient.set_phase("closed")   # 60 req/s per connection
aclient.set_phase("trading")  # 15 req/s per connection
```

---

## 3. 输出格式选择

每种数据 API 提供 3 种输出格式，按需选择：

| 格式 | 方法后缀 | 速度 | 适用场景 |
|------|---------|:---:|----------|
| `list[dict]` | (无) | ★★ | 调试打印、JSON 序列化、少量数据 |
| `list[tuple]` | `_tuples` | ★★★ | 遍历处理、中等数据量 |
| `DataFrame` | `_dataframe` | ★★★ | 数据分析、回测、pandas 集成 |

**性能差异**: tuple 模式跳过 dict 构建，比 dict 快 20-30%。DataFrame 模式内部使用列式内存布局，pandas 可直接利用。

```python
# dict 模式 — 人类可读
bars = client.get_security_bars(4, 1, "600519", 0, 100)
print(bars[0]["open"], bars[0]["close"])

# tuple 模式 — 遍历最快
tuples = client.get_security_bars_tuples(4, 1, "600519", 0, 100)
# tuple: (open, close, high, low, vol, amount, year, month, day, hour, minute, datetime)
for t in tuples:
    print(t[0], t[1])  # 按索引访问

# DataFrame 模式 — 直接分析
df = client.get_security_bars_dataframe(4, 1, "600519", 0, 100)
print(df[["datetime", "open", "close"]].tail())
```

---

## 4. 批量请求优化

### 4.1 用批量接口替代循环

**反模式** ❌:
```python
# 100 只股票 = 100 次请求
for code in stock_list:
    bars = client.get_security_bars(4, 1, code, 0, 100)
```

**正确做法** ✅ (实时行情有批量接口):
```python
# 每次最多 60 只，超出自动截断！
stocks = [(1, code) for code in stock_list[:60]]
quotes = client.get_security_quotes(stocks)
```

**超过 60 只需自行分组**:
```python
def batch_quotes(client, stocks, batch_size=60):
    """分组查询批量行情，每组最多 60 只"""
    results = []
    for i in range(0, len(stocks), batch_size):
        results.extend(client.get_security_quotes(stocks[i:i+batch_size]))
    return results

# 200 只股票 = 4 次请求
all_quotes = batch_quotes(client, [(1, c) for c in stock_list])
```

> **限制说明**:
> - `get_security_quotes` / `get_fund_quotes`: **单次上限 60 只**，TDX 服务端硬限制，超出自动截断，不可修改
> - `get_security_bars` / `get_index_bars`: 不支持批量，每次只能查 1 只股票，每页最多 800 根K线
> - `get_transaction_data`: 每次最多 2000 条逐笔数据

### 4.2 用自动分页替代手动循环

**反模式** ❌:
```python
all_bars = []
for offset in range(0, 5000, 800):
    bars = client.get_security_bars(4, 1, "600519", offset, 800)
    if not bars:
        break
    all_bars.extend(bars)
```

**正确做法** ✅:
```python
# 一行搞定，内部自动翻页
all_bars = client.get_security_bars_all(4, 1, "600519", 5000)
```

### 4.3 用 AsyncTdxHqClient 并发多只股票 K 线

当需要获取多只股票的 K 线时，`AsyncTdxHqClient` 的连接池可并发执行：

```python
from tdxrs import AsyncTdxHqClient
from tdxrs.constants import KLINE_DAILY, MARKET_SH, MARKET_SZ

aclient = AsyncTdxHqClient()
aclient.connect_to_any()

# Rust 侧并发: 4 个连接同时请求
# Python 侧同步等待 (内部 block_on)
codes = ["600519", "000858", "300750", "601318", "000001", "000002"]
results = {}
for code in codes:
    market = MARKET_SH if code.startswith("6") else MARKET_SZ
    results[code] = aclient.get_security_bars(KLINE_DAILY, market, code, 0, 500)
```

> `AsyncTdxHqClient` 内部 4 个连接轮转分发，上述 6 个请求实际在 4 条连接上并发执行。
> 相比 `TdxHqClient` 的连接池 Mutex 串行，吞吐提升约 2-3 倍。

### 4.4 多线程并发 (TdxDirectClient)

对于 CPU 密集型后处理场景，可用 `TdxDirectClient` + `ThreadPoolExecutor`：

```python
from tdxrs import TdxDirectClient
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_bars(code, market):
    dc = TdxDirectClient("180.153.18.170", 7709, timeout=5.0)
    return code, dc.get_security_bars(4, market, code, 0, 500)

# 8 线程并发，每线程独立 TCP 连接
with ThreadPoolExecutor(max_workers=8) as pool:
    futures = [
        pool.submit(fetch_bars, code, MARKET_SH if code.startswith("6") else MARKET_SZ)
        for code in stock_list
    ]
    for f in as_completed(futures):
        code, bars = f.result()
        process(code, bars)
```

> `TdxDirectClient` 无共享状态，天然线程安全。8 线程并发性能约为 `TdxHqClient` 的 4-6 倍。

### 4.5 本地文件优先

如果本地有通达信数据文件，**优先用 Reader 解析本地文件**，零网络开销：

```python
from tdxrs import DailyBarReader

reader = DailyBarReader(coefficient=0.01)
bars = reader.parse_file("E:/tdx/vipdoc/sh/lday/600519.day")  # 瞬间完成

# 高性能 tuple 模式
tuples = reader.parse_file_tuples("E:/tdx/vipdoc/sh/lday/600519.day")
```

| 数据源 | 速度 | 适用 |
|--------|:---:|------|
| 本地 `.day` 文件 | ★★★★★ | 有通达信客户端、历史数据 |
| `TdxHqClient` 网络 | ★★★ | 实时数据、无本地文件 |
| `AsyncTdxHqClient` 网络 | ★★★★ | 批量并发获取 |

### 4.6 批量下载 (Downloader)

`Downloader` 提供多服务器分发 + 自动翻页 + 增量更新。K线下载使用 count+offset 模式，分时/逐笔支持按日下载。

```python
from tdxrs.downloader import Downloader

dl = Downloader(data_dir="./data")

# K线全量下载 (多服务器轮转，自动限流)
dl.run(markets=["sh"], categories=["daily"])

# K线增量更新 (仅 fq=0 支持)
dl.update(markets=["sh"], categories=["daily"])

# 分时按日下载 — codes 必填，协议原生日期查询
dl.download_minute("2026-06-25", codes=["600519", "000858"])

# 逐笔按日下载 — 自动翻页 (2000条/页)
dl.download_ticks(["2026-06-25", "2026-06-24"], codes=["600519"])
```

> **注意**: `download_minute` 和 `download_ticks` 的 `codes` 为必填参数。分时/逐笔为单品种接口（每只股票独立请求），不支持批量查询。

---

## 5. 基金数据获取

`TdxHqFundClient` 封装 `TdxHqClient`，专门处理 ETF/LOF/REITs/分级基金等基金数据。
价格系数、代码分类等细节已内置，无需手动处理。

### 5.1 基本用法

```python
from tdxrs import TdxHqFundClient
from tdxrs.constants import MARKET_SH, MARKET_SZ, KLINE_DAILY

client = TdxHqFundClient()
client.connect_to_any()

# 基金列表 (含类型信息)
funds = client.get_fund_list(MARKET_SH)
# [{'code': '510300', 'fund_type': 'ETF', 'fund_type_zh': '交易型开放式指数基金', ...}, ...]

# 基金K线 — 价格系数自动处理
bars = client.get_fund_bars(KLINE_DAILY, MARKET_SH, "510300", 0, 100)

# 实时行情 — 批量查询
quotes = client.get_fund_quotes([(MARKET_SH, "510300"), (MARKET_SZ, "159915")])

# 自动分页
all_bars = client.get_fund_bars_all(KLINE_DAILY, MARKET_SH, "510300", 2000)
```

### 5.2 基金类型分类

```python
from tdxrs import TdxHqFundClient

# 静态方法，无需连接
TdxHqFundClient.classify_fund(MARKET_SH, "510300")  # → "ETF"
TdxHqFundClient.classify_fund(MARKET_SH, "508000")  # → "REITs"
TdxHqFundClient.classify_fund(MARKET_SZ, "162006")  # → "Structured" (分级)
TdxHqFundClient.classify_fund(MARKET_SZ, "160106")  # → "LOF"
TdxHqFundClient.classify_fund(MARKET_SH, "519003")  # → "OpenEnd" (场外)

# 判断是否为基金 / ETF
TdxHqFundClient.is_fund(MARKET_SH, "510300")  # True
TdxHqFundClient.is_etf(MARKET_SH, "510300")   # True
TdxHqFundClient.is_fund(MARKET_SH, "600519")  # False (股票)
```

**基金类型速查**:

| 类型 | 代码前缀 | 价格系数 | 示例 |
|------|---------|:---:|------|
| ETF | 510/512/513/515/516/159 | 0.001 | 510300 (沪深300ETF) |
| LOF | 501/502/160/161 | 0.001 | 160106 (南方高增) |
| REITs | 508 | 0.001 | 508000 (普洛斯) |
| Structured | 162/163/164 | 0.001 | 162006 (国投瑞利) |
| Bond ETF | 511 | 0.001 | 511010 (国债ETF) |
| OpenEnd | 519 | 0.00001 | 519003 (海富通) |

> **场内基金** (ETF/LOF/REITs/分级/债券) 价格系数 0.001 (3位小数)。
> **场外基金** (传统开放式) 价格系数 0.00001 (5位小数，单位净值)。

### 5.3 批量筛选基金

```python
from tdxrs import TdxHqFundClient
from tdxrs.constants import MARKET_SH

client = TdxHqFundClient()
client.connect_to_any()

# 获取全部基金列表
all_funds = client.get_fund_list(MARKET_SH)

# 筛选 ETF
etfs = [f for f in all_funds if f["fund_type"] == "ETF"]
print(f"沪市 ETF: {len(etfs)} 只")

# 筛选 REITs
reits = [f for f in all_funds if f["fund_type"] == "REITs"]
print(f"沪市 REITs: {len(reits)} 只")

# 获取全部基金的实时行情 (批量接口，算 1 次请求)
codes = [(MARKET_SH, f["code"]) for f in etfs[:50]]  # 前 50 只
quotes = client.get_fund_quotes(codes)
```

### 5.4 基金 vs 股票接口选择

| 场景 | 接口 | 说明 |
|------|------|------|
| 查询基金 | `TdxHqFundClient` | 价格系数自动处理 |
| 查询股票 | `TdxHqClient` | 通用接口 |
| 混合查询 | 分别调用 | 基金用 FundClient，股票用 HqClient |
| 判断类型 | `classify_fund()` | 静态方法，无需连接 |

```python
from tdxrs import TdxHqClient, TdxHqFundClient

hq = TdxHqClient()
fund = TdxHqFundClient()
hq.connect_to_any()
fund.connect_to_any()

stocks = ["600519", "000858", "510300", "159915", "508000"]

for code in stocks:
    market = 1 if code.startswith(("5", "6")) else 0
    if TdxHqFundClient.is_fund(market, code):
        bars = fund.get_fund_bars(4, market, code, 0, 50)
        print(f"[基金] {code}: {len(bars)} 条")
    else:
        bars = hq.get_security_bars(4, market, code, 0, 50)
        print(f"[股票] {code}: {len(bars)} 条")
```

### 5.5 注意事项

**场外基金 (519xxx) 价格是单位净值**，不是交易价格：

```python
bars = client.get_fund_bars(4, MARKET_SH, "519003", 0, 10)
print(bars[0]["close"])  # 3.9050 (单位净值，不是 390.50)
```

**基金没有复权概念**，`fq` 参数对基金无意义：

```python
# 基金K线 fq 参数会被忽略
bars = client.get_fund_bars(4, MARKET_SH, "510300", 0, 100, fq=1)  # fq 无效
```

---

## 6. 配置建议

### 6.1 生产环境推荐配置

```python
from tdxrs import TdxHqClient

client = TdxHqClient()
client.set_connect_timeout(10.0)   # 默认 5s，网络差时调大
client.set_auto_retry(False)       # 生产环境关闭内置重试，自行控制
client.set_cache_ttl(60)           # 缓存 60s (security_count/list)
client.connect_to_any(timeout=5.0)
```

**为什么关闭 auto_retry**:
- 内置重试间隔为 0.1s → 0.5s → 1.0s → 2.0s (共 4 次)
- 批量任务中，单次失败的重试延迟会累积
- 生产环境通常有自己的重试策略 (指数退避、熔断等)

### 6.2 探测最优服务器

```python
client = TdxHqClient()

# 探测全部服务器 (每台 2s 超时，约需 3-5 分钟)
results = client.probe_servers(timeout=2.0)

# 取最快的 5 台设为优先
client.reorder_servers(results[:5])
client.connect_to_any(timeout=3.0)

# 查看结果
for name, ip, port, tcp_ms, hs_ms, api_ms in results[:5]:
    print(f"{name:<20} API: {api_ms:.0f}ms")
```

### 6.3 连接池大小

```python
# TdxHqClient: 默认 5 连接
client = TdxHqClient()

# AsyncTdxHqClient: 默认 4 连接，可调整
from tdxrs import AsyncTdxHqClient
aclient = AsyncTdxHqClient.with_pool_size(8)  # 8 连接池
```

连接池大小与限流的关系：每连接独立限流。4 连接 + 60 req/s = 总吞吐 240 req/s。

---

## 7. 常见反模式

### ❌ 反模式 1: 循环单只查询

```python
# ❌ 每只股票 1 次请求，100 只 = 100 次
for code in codes:
    q = client.get_security_quotes([(market, code)])
```

```python
# ✅ 一次批量查询
q = client.get_security_quotes([(market, code) for code in codes])
```

### ❌ 反模式 2: 不必要的 DataFrame 转换

```python
# ❌ 先 dict 再转 DataFrame (双重构建)
bars = client.get_security_bars(4, 1, "600519", 0, 500)
df = pd.DataFrame(bars)
```

```python
# ✅ 直接用 DataFrame 输出
df = client.get_security_bars_dataframe(4, 1, "600519", 0, 500)
```

### ❌ 反模式 3: 频繁连接/断开

```python
# ❌ 每次查询都重新连接
for code in codes:
    client = TdxHqClient()
    client.connect_to_any()
    bars = client.get_security_bars(4, 1, code, 0, 100)
    client.disconnect()
```

```python
# ✅ 复用连接
client = TdxHqClient()
client.connect_to_any()
for code in codes:
    bars = client.get_security_bars(4, 1, code, 0, 100)
client.disconnect()
```

### ❌ 反模式 4: 用 TdxHqClient 做高并发

```python
# ❌ 多线程共享 TdxHqClient，Mutex 争用严重
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=20) as pool:
    pool.map(lambda c: client.get_security_bars(4, 1, c, 0, 100), codes)
```

```python
# ✅ 用 AsyncTdxHqClient (通道化并发)
aclient = AsyncTdxHqClient()
aclient.connect_to_any()
for code in codes:
    bars = aclient.get_security_bars(4, 1, code, 0, 100)  # 内部并发
```

```python
# ✅ 或用 TdxDirectClient (独立连接)
from concurrent.futures import ThreadPoolExecutor
def fetch(code):
    dc = TdxDirectClient("180.153.18.170", 7709)
    return dc.get_security_bars(4, 1, code, 0, 100)
with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(fetch, codes))
```

### ❌ 反模式 5: 忘记复权参数

```python
# ❌ 不传 fq，默认前复权 — 可能不是你想要的
bars = client.get_security_bars(4, 1, "600519", 0, 100)

# ✅ 显式指定复权类型
bars = client.get_security_bars(4, 1, "600519", 0, 100, fq=0)  # 未复权
bars = client.get_security_bars(4, 1, "600519", 0, 100, fq=1)  # 前复权
bars = client.get_security_bars(4, 1, "600519", 0, 100, fq=2)  # 后复权
```

### ❌ 反模式 6: 用股票接口查基金

```python
# ❌ 价格系数错误 — 场外基金 519003 显示 390.50 (错误)
bars = client.get_security_bars(4, 1, "519003", 0, 100)

# ✅ 用基金接口 — 自动处理价格系数，显示 3.9050 (正确)
from tdxrs import TdxHqFundClient
fund = TdxHqFundClient()
fund.connect_to_any()
bars = fund.get_fund_bars(4, 1, "519003", 0, 100)
```

```python
# ❌ 不区分基金/股票，统一用股票接口
for code in codes:
    bars = client.get_security_bars(4, 1, code, 0, 100)  # 基金价格错误

# ✅ 先判断类型，分别调用
for code in codes:
    market = 1 if code.startswith(("5", "6")) else 0
    if TdxHqFundClient.is_fund(market, code):
        bars = fund.get_fund_bars(4, market, code, 0, 100)
    else:
        bars = client.get_security_bars(4, market, code, 0, 100)
```

---

## 8. 场景速查表

| 场景 | 推荐方案 | 关键代码 |
|------|----------|----------|
| 获取单只股票日K | `TdxHqClient.get_security_bars()` | `client.get_security_bars(4, 1, "600519", 0, 500)` |
| 获取大量历史K线 | `get_security_bars_all()` | `client.get_security_bars_all(4, 1, "600519", 5000)` |
| 批量实时行情 | `get_security_quotes(stocks)` | 一次传入全部股票列表 |
| 多只股票K线 | `AsyncTdxHqClient` | 连接池并发 |
| 多线程批量获取 | `TdxDirectClient` + `ThreadPoolExecutor` | 每线程独立连接 |
| 本地数据分析 | `DailyBarReader.to_dataframe()` | 零网络开销 |
| 回测数据准备 | `_tuples()` 或 `_dataframe()` | 避免 dict 开销 |
| 财务数据对比 | `get_finance_info_dataframe(stocks)` | 多股票一次构建 |
| 探测最快服务器 | `probe_servers()` + `reorder_servers()` | 启动时执行一次 |
| 偶发查询 | `TdxDirectClient` | 无连接池开销 |
| 长期运行服务 | `TdxHqClient` | 心跳 + 自动重连 |
| ETF/基金K线 | `TdxHqFundClient.get_fund_bars()` | 价格系数自动处理 |
| 基金批量行情 | `get_fund_quotes(stocks)` | 批量查询，算 1 次请求 |
| 基金类型判断 | `classify_fund()` / `is_fund()` | 静态方法，无需连接 |
| 场外基金净值 | `get_fund_bars()` + OpenEnd | 价格为单位净值 (5位小数) |
| 批量下载K线 | `Downloader.run()` | 多服务器分发，自动限流 |
| 按日下载分时 | `Downloader.download_minute(dates, codes)` | 协议原生日期查询 |
| 按日下载逐笔 | `Downloader.download_ticks(dates, codes)` | 自动翻页，codes 必填 |
