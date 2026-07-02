# tdxrs 基金模块

> 版本: v0.6.5 | 更新日期: 2026-07-02

---

## 概述

基金模块提供 ETF、LOF、REITs、分级基金等全部基金类型的数据获取和解析。

**客户端**: `TdxHqFundClient`

**连接方式**: 共享连接池 (与股票行情相同)

| 类型 | 前缀 | 市场 | 示例 | 交易方式 |
|------|------|------|------|----------|
| ETF | 510/512/513/515/516, 159 | 沪/深 | 510300 沪深300ETF | 场内实时交易 |
| LOF | 501/502, 160/161 | 沪/深 | 160105 南方积配 | 场内实时交易 |
| REITs | 508 | 沪 | 508000 普洛斯 | 场内实时交易 |
| 分级基金 | 162/163/164 | 深 | 162006 银华锐进 | 场内实时交易 |
| 债券基金 | 511 | 沪 | 511010 国债ETF | 场内实时交易 |
| 传统开放式 | 519 | 沪 | 519001 华夏成长 | 场外申购/赎回 |

---

## 场内基金 vs 场外基金

### 重要区别

| 特性 | 场内基金 | 场外基金 |
|------|----------|----------|
| **代码前缀** | 50x/51x (沪), 15x/16x (深) | 519xxx (沪) |
| **交易方式** | 交易所实时买卖 | 申购/赎回 |
| **价格类型** | 实时交易价格 | 单位净值 (每日更新) |
| **价格精度** | 0.001 元 | 0.00001 元 |
| **数据来源** | TDX 实时行情 | TDX 净值数据 |

### 价格说明

**场内基金** (ETF/LOF/REITs):
- 返回实时交易价格
- 精度: 0.001 元 (3位小数)
- 示例: `510050 (50ETF) = 3.024 元`

**场外基金** (传统开放式基金):
- 返回**单位净值**，不是累积净值
- 精度: 0.00001 元 (5位小数)
- 示例: `519003 (华夏优势增长) = 3.9050 元`

> **注意**: TDX 协议返回的是单位净值，累积净值需要从其他数据源获取。

---

## 快速开始

```python
from tdxrs import TdxHqFundClient
from tdxrs.constants import MARKET_SH, MARKET_SZ

client = TdxHqFundClient()
client.connect_to_any()

# 获取基金列表 (含 FundType 分类)
funds = client.get_fund_list(MARKET_SH)
for f in funds[:5]:
    print(f"{f['code']}: {f['name']} [{f['fund_type_zh']}]")

# 获取 K线
bars = client.get_fund_bars(4, MARKET_SH, "510300", 0, 10)
for bar in bars:
    print(f"{bar['datetime']}: {bar['close']:.3f}")

# 获取实时行情 (五档)
quotes = client.get_fund_quotes([(MARKET_SH, "510300")])
print(f"510300: {quotes[0]['price']:.3f}")
```

---

## FundType 枚举

```python
from tdxrs import TdxHqFundClient

# 静态方法
TdxHqFundClient.is_fund(MARKET_SH, "510300")       # True
TdxHqFundClient.is_etf(MARKET_SH, "510300")        # True
TdxHqFundClient.classify_fund(MARKET_SH, "510300")  # "ETF"
```

| 类型 | 英文 | 说明 |
|------|------|------|
| ETF | Etf | 交易型开放式指数基金 |
| LOF | Lof | 上市型开放式基金 |
| REITs | Reits | 不动产投资信托基金 |
| 分级基金 | Structured | 结构化基金 |
| 开放式基金 | OpenEnd | 传统开放式基金 |
| 债券基金 | Bond | 债券型基金 |
| 货币基金 | Money | 货币市场基金 |
| 其他 | Other | 未分类 |

---

## API 参考

### TdxHqFundClient

基金行情客户端，封装 `TdxHqClient`，自动处理基金代码验证和 FundType 分类。

```python
from tdxrs import TdxHqFundClient

client = TdxHqFundClient()
```

#### 连接管理

| 方法 | 返回 | 说明 |
|------|------|------|
| `connect(ip, port, timeout=None)` | `bool` | 连接到指定服务器 |
| `connect_to_any(timeout=None)` | `bool` | 自动探测可用服务器 |
| `disconnect()` | — | 断开连接 |
| `is_connected()` | `bool` | 是否已连接 |

---

#### get_fund_list

```python
get_fund_list(market: int) -> list[dict]
```

从证券列表中筛选出全部基金。

| 参数 | 类型 | 说明 |
|------|------|------|
| `market` | int | 市场代码 (0=深圳, 1=上海) |

返回字段: `market`, `code`, `name`, `fund_type`, `fund_type_zh`, `vol_unit`, `decimal_point`, `pre_close`

```python
funds = client.get_fund_list(MARKET_SH)
for f in funds[:5]:
    print(f"{f['code']}: {f['name']} [{f['fund_type_zh']}]")
```

---

#### get_fund_bars / get_fund_bars_all

```python
get_fund_bars(category, market, code, start=0, count=800) -> list[dict]
get_fund_bars_all(category, market, code, count=800) -> list[dict]
```

获取基金 K线数据，支持所有周期。

| 参数 | 类型 | 默认 | 说明 |
|------|------|:--:|------|
| `category` | int | — | K线种类 (0=5分钟, 4=日线, 5=周线 等) |
| `market` | int | — | 市场代码 |
| `code` | str | — | 基金代码 |
| `start` | int | 0 | 起始偏移 (0=最新) |
| `count` | int | 800 | 数量 (最大 800) |

返回字段: `open`, `close`, `high`, `low`, `vol`, `amount`, `year`, `month`, `day`, `hour`, `minute`, `datetime`

```python
# 日K线
bars = client.get_fund_bars(4, MARKET_SH, "510300", 0, 100)

# 自动分页获取更多
all_bars = client.get_fund_bars_all(4, MARKET_SH, "510300", count=2000)
```

---

#### get_fund_quotes

```python
get_fund_quotes(stocks: list[tuple]) -> list[dict]
```

批量获取基金实时行情，含五档买卖盘。**单次上限 60 只**，超出自动截断。

| 参数 | 类型 | 说明 |
|------|------|------|
| `stocks` | `list[(market, code)]` | 基金列表，**单次上限 60 只**，超出自动截断 |

返回字段: `market`, `code`, `price`, `last_close`, `open`, `high`, `low`, `vol`, `amount`, `bid1`~`bid5`, `bid_vol1`~`bid_vol5`, `ask1`~`ask5`, `ask_vol1`~`ask_vol5`, `servertime`

```python
# 单次查询 (≤60 只)
quotes = client.get_fund_quotes([
    (MARKET_SH, "510300"),
    (MARKET_SZ, "159915"),
])

# 超过 60 只需分组
def batch_fund_quotes(client, stocks, batch_size=60):
    results = []
    for i in range(0, len(stocks), batch_size):
        results.extend(client.get_fund_quotes(stocks[i:i+batch_size]))
    return results

for q in quotes:
    pct = (q['price'] / q['last_close'] - 1) * 100
    print(f"{q['code']}: {q['price']:.3f} ({pct:+.2f}%)")
```

---

#### get_fund_minute_time_data

```python
get_fund_minute_time_data(market, code) -> list[dict]
get_fund_history_minute_time_data(market, code, date) -> list[dict]
```

获取分时数据。返回字段: `price`, `vol`

---

#### get_fund_transaction_data

```python
get_fund_transaction_data(market, code, start=0, count=2000) -> list[dict]
get_fund_history_transaction_data(market, code, start, count, date) -> list[dict]
```

获取逐笔成交。返回字段: `time`, `price`, `vol`, `num`, `buyorsell`

---

#### get_fund_xdxr_info

```python
get_fund_xdxr_info(market, code) -> list[dict]
```

获取除权除息信息。基金通常只有分红记录 (category=1)。

返回字段: `year`, `month`, `day`, `category`, `fenhong`, `peigujia`, `songzhuangu`, `peigu`, `suogu`

---

#### get_fund_finance_info

```python
get_fund_finance_info(market, code) -> dict
```

获取财务信息 (基金仅含部分字段)。

返回字段: `market`, `code`, `zongguben`, `liutongguben`, `meigujingzichan`, `zongzichan`, `jingzichan`

---

#### 静态方法

```python
TdxHqFundClient.is_fund(market, code) -> bool        # 判断是否为基金
TdxHqFundClient.is_etf(market, code) -> bool         # 判断是否为 ETF
TdxHqFundClient.classify_fund(market, code) -> str    # 返回基金类型名称
TdxHqFundClient.auto_market_code(code) -> int         # 自动判断市场
```

---

## K线种类 (category)

| 值 | 含义 | 值 | 含义 |
|:--:|------|:--:|------|
| 0 | 5 分钟线 | 5 | 周 K 线 |
| 1 | 15 分钟线 | 6 | 月 K 线 |
| 2 | 30 分钟线 | 7 | 扩展 1 分钟线 |
| 3 | 60 分钟线 | 8 | 1 分钟线 |
| **4** | **日 K 线** | 9 | 日 K 线 (精简) |
| 10 | 季 K 线 | 11 | 年 K 线 |

---

## 模块结构

```
src/fund/
├── mod.rs              # 模块入口
├── constants.rs        # FundType 枚举, 代码前缀, 价格系数
├── types.rs            # 数据类型 (FundInfo, FundBar, FundQuote)
├── client.rs           # 客户端封装 (TdxHqFundClient)
└── utils.rs            # 工具函数 (基金代码验证)
```

---

## 数据核对与注意事项

### 基金接口 vs 股票接口

同一基金可通过 `TdxHqClient` (股票接口) 或 `TdxHqFundClient` (基金接口) 查询。
两者返回值**通常一致**，但在特定场景下存在差异:

| 接口 | 场内基金 (ETF/LOF/REITs) | 场外基金 (519xxx) | 债券ETF (511xxx) |
|------|:---:|:---:|:---:|
| `get_security_bars` (股票K线) | 市场价 | **100x 偏高** ⚠️ | 市场收盘价 |
| `get_fund_bars` (基金K线) | 市场价 | **100x 偏高** ⚠️ | 基金净值 (NAV) |
| `get_security_quotes` (股票行情) | 市场价 | 单位净值 ✅ | 市场价 |
| `get_fund_quotes` (基金行情) | 市场价 | 单位净值 ✅ | 基金净值 (NAV) |

> **结论**: 对于场内基金，两个接口返回值一致，可互换使用。
> 基金接口的优势在于自动代码验证和 FundType 分类。

### 场外基金 (519xxx) K 线数据异常 ⚠️

场外基金 (传统开放式基金，代码 519xxx) 的 **K 线数据存在 100x 偏差**:

| 基金 | K 线收盘价 | 实时行情价格 | 说明 |
|------|:---------:|:----------:|------|
| 519003 海富通收益增长 | 390.500 | **3.905** | K 线 100x |
| 519688 交银精选混合 | 162.730 | **1.627** | K 线 100x |

- **实时行情** (`get_fund_quotes` / `get_security_quotes`) 返回正确的单位净值
- **K 线** (`get_fund_bars` / `get_security_bars`) 返回值是正确值的 ~100 倍
- 两个接口返回值一致，问题在 TDX 协议解析层，不在基金模块
- **影响范围**: 仅 519xxx 场外基金的 K 线数据

**临时解决方案**: 获取场外基金 K 线后手动除以 100:

```python
bars = client.get_fund_bars(4, MARKET_SH, "519003", 0, 100)
for bar in bars:
    bar["open"] /= 100
    bar["close"] /= 100
    bar["high"] /= 100
    bar["low"] /= 100
```

> 此问题将在后续版本中修复。

### 债券 ETF 市场价 vs 净值

债券 ETF (511xxx) 在两个接口返回不同含义的价格:

| 接口 | 返回值 | 含义 |
|------|--------|------|
| `get_security_bars` / `get_security_quotes` | 市场收盘价 | 二级市场交易价格 |
| `get_fund_bars` / `get_fund_quotes` | 基金净值 (NAV) | 基金公司计算的资产净值 |

两者差异 (折溢价) 是正常的套利空间，通常在 ±1% 以内:

```python
# 对比债券 ETF 的市场价与净值
stock_q = hq_client.get_security_quotes([(MARKET_SH, "511010")])
fund_q = fund_client.get_fund_quotes([(MARKET_SH, "511010")])

market_price = stock_q[0]["price"]  # 市场价
nav_price = fund_q[0]["price"]      # 净值
premium = (market_price / nav_price - 1) * 100
print(f"折溢价: {premium:+.2f}%")
```

> 场内基金 (ETF/LOF/REITs) 通常没有折溢价差异 (两个接口返回值一致)。
> 差异主要出现在债券 ETF 和流动性较低的基金上。

### 科创板 ETF (58xxxx) 价格修正

> **v0.6.5 修复**: 科创板 ETF (588xxx，如 588000/588200) 的价格系数已修正为 0.001。
> 修复前使用 A 股默认系数 0.01 导致价格偏高 10 倍。逐笔成交数据的价格精度同步修正。

### 如何自行核对数据

**步骤 1: 确认基金类型**

```python
from tdxrs import TdxHqFundClient
from tdxrs.constants import MARKET_SH

fund_type = TdxHqFundClient.classify_fund(MARKET_SH, "510300")
print(fund_type)  # "ETF"
```

**步骤 2: 对比两个接口**

```python
from tdxrs import TdxHqClient, TdxHqFundClient
from tdxrs.constants import MARKET_SH, KLINE_DAILY

hq = TdxHqClient()
fund = TdxHqFundClient()
hq.connect_to_any()
fund.connect_to_any()

code = "510300"
stock_bars = hq.get_security_bars(KLINE_DAILY, MARKET_SH, code, 0, 5)
fund_bars = fund.get_fund_bars(KLINE_DAILY, MARKET_SH, code, 0, 5)

for sb, fb in zip(stock_bars, fund_bars):
    ratio = sb["close"] / fb["close"] if fb["close"] else 0
    print(f"{sb['year']}-{sb['month']:02d}-{sb['day']:02d}: "
          f"stock={sb['close']:.4f} fund={fb['close']:.4f} ratio={ratio:.3f}")
```

**步骤 3: 验证价格合理性**

| 基金类型 | 典型价格范围 | 说明 |
|---------|:----------:|------|
| ETF | 0.5 - 20 元 | 跟踪指数，价格适中 |
| LOF | 0.5 - 10 元 | 与 ETF 类似 |
| REITs | 1 - 15 元 | 不动产信托 |
| 分级基金 | 0.3 - 5 元 | B 端波动较大 |
| 债券 ETF | 90 - 120 元 | 跟踪债券指数 |
| 场外基金 | 0.3 - 10 元 | **注意: K 线需 ÷100** |

如果价格明显偏离预期范围，建议:
1. 对比实时行情 (`get_fund_quotes`) 验证
2. 在其他平台 (同花顺、东方财富) 核实
3. 确认基金类型是否正确分类

---

## 常见问题

### Q: 如何判断基金代码的市场？

A: 根据代码前缀自动判断：
- 沪市: 50xxxx, 51xxxx → `market=1`
- 深市: 15xxxx, 16xxxx → `market=0`

或使用 `TdxHqFundClient.auto_market_code(code)` 自动判断。

### Q: 基金是否支持复权？

A: 支持。基金复权只处理现金分红，公式简化为 `P_ex = P_close - D`。

### Q: FundType 如何获取？

A: `get_fund_list()` 返回的每个 dict 包含 `fund_type` (英文) 和 `fund_type_zh` (中文) 字段。也可用 `classify_fund(market, code)` 静态方法。

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [API 参考](API_REFERENCE.md) | 完整 Python API |
| [Python 最佳实践](PYTHON_BEST_PRACTICES.md) | 限流、优化、反模式 |
| [板块查询](API_REFERENCE.md#tdxblockclient) | 板块/概念/行业查询 |
| [复权算法](../ADJUSTER_ALGORITHM.md) | 复权公式详解 |
