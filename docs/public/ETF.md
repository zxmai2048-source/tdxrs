# tdxrs ETF 模块

> 版本: v0.6.0 | 更新日期: 2026-06-21

---

## 概述

ETF (交易所交易基金) 模块提供 ETF 数据的专用获取和解析功能。

**模块位置**: `tdxrs.pro` (扩展模块)

**连接方式**: 共享连接池 (与股票行情相同)

| 市场 | 代码前缀 | 示例 | 数量 |
|------|----------|------|:----:|
| 上海 (market=1) | 50xxxx, 51xxxx | 510300 沪深300ETF | ~800 |
| 深圳 (market=0) | 15xxxx, 16xxxx | 159915 创业板ETF | ~1000 |

---

## 快速开始

```python
from tdxrs.pro import TdxHqEtfClient
from tdxrs.constants import MARKET_SH, MARKET_SZ

client = TdxHqEtfClient()
client.connect_to_any()

# 获取 ETF 列表
sh_etfs = client.get_etf_list(MARKET_SH)
print(f"上海 ETF: {len(sh_etfs)} 只")

# 获取 K线
bars = client.get_etf_bars(4, MARKET_SH, "510300", 0, 10)
for bar in bars:
    print(f"{bar['datetime']}: {bar['close']:.3f}")

# 获取实时行情
quotes = client.get_etf_quotes([(MARKET_SH, "510300")])
print(f"510300: {quotes[0]['price']:.3f}")
```

---

## API 参考

### TdxHqEtfClient

ETF 行情客户端，封装 `TdxHqClient`，自动处理 ETF 代码验证。

```python
from tdxrs.pro import TdxHqEtfClient

client = TdxHqEtfClient()
```

#### 连接管理

| 方法 | 返回 | 说明 |
|------|------|------|
| `connect(ip, port, timeout=None)` | `bool` | 连接到指定服务器 |
| `connect_to_any(timeout=None)` | `bool` | 自动探测可用服务器 |
| `disconnect()` | — | 断开连接 |
| `is_connected()` | `bool` | 是否已连接 |

---

#### get_etf_list

```python
get_etf_list(market: int) -> list[dict]
```

从证券列表中筛选出 ETF。

| 参数 | 类型 | 说明 |
|------|------|------|
| `market` | int | 市场代码 (0=深圳, 1=上海) |

返回字段: `market`, `code`, `name`, `vol_unit`, `decimal_point`, `pre_close`

```python
sh_etfs = client.get_etf_list(MARKET_SH)
for etf in sh_etfs[:5]:
    print(f"{etf['code']}: {etf['name']}")
```

---

#### get_etf_bars / get_etf_bars_all

```python
get_etf_bars(category, market, code, start=0, count=800) -> list[dict]
get_etf_bars_all(category, market, code, count=800) -> list[dict]
```

获取 ETF K线数据，支持所有周期。

| 参数 | 类型 | 默认 | 说明 |
|------|------|:--:|------|
| `category` | int | — | K线种类 (0=5分钟, 4=日线, 5=周线 等) |
| `market` | int | — | 市场代码 |
| `code` | str | — | ETF 代码 |
| `start` | int | 0 | 起始偏移 (0=最新) |
| `count` | int | 800 | 数量 (最大 800) |

返回字段: `open`, `close`, `high`, `low`, `vol`, `amount`, `year`, `month`, `day`, `hour`, `minute`, `datetime`

```python
# 日K线
bars = client.get_etf_bars(4, MARKET_SH, "510300", 0, 100)

# 自动分页获取更多
all_bars = client.get_etf_bars_all(4, MARKET_SH, "510300", count=2000)
```

---

#### get_etf_quotes

```python
get_etf_quotes(stocks: list[tuple]) -> list[dict]
```

批量获取 ETF 实时行情，含五档买卖盘。

| 参数 | 类型 | 说明 |
|------|------|------|
| `stocks` | `list[(market, code)]` | ETF 列表 |

返回字段: `market`, `code`, `price`, `last_close`, `open`, `high`, `low`, `vol`, `amount`, `bid1`~`bid5`, `bid_vol1`~`bid_vol5`, `ask1`~`ask5`, `ask_vol1`~`ask_vol5`, `servertime`

```python
quotes = client.get_etf_quotes([
    (MARKET_SH, "510300"),
    (MARKET_SZ, "159915"),
])

for q in quotes:
    pct = (q['price'] / q['last_close'] - 1) * 100
    print(f"{q['code']}: {q['price']:.3f} ({pct:+.2f}%)")
```

---

#### get_etf_minute_time_data

```python
get_etf_minute_time_data(market, code) -> list[dict]
get_etf_history_minute_time_data(market, code, date) -> list[dict]
```

获取分时数据。返回字段: `price`, `vol`

---

#### get_etf_transaction_data

```python
get_etf_transaction_data(market, code, start=0, count=2000) -> list[dict]
get_etf_history_transaction_data(market, code, start, count, date) -> list[dict]
```

获取逐笔成交。返回字段: `time`, `price`, `vol`, `num`, `buyorsell`

---

#### get_etf_xdxr_info

```python
get_etf_xdxr_info(market, code) -> list[dict]
```

获取除权除息信息。ETF 通常只有分红记录 (category=1)。

返回字段: `year`, `month`, `day`, `category`, `fenhong`, `peigujia`, `songzhuangu`, `peigu`, `suogu`

---

#### get_etf_finance_info

```python
get_etf_finance_info(market, code) -> dict
```

获取财务信息 (ETF 仅含部分字段)。

返回字段: `market`, `code`, `zongguben`, `liutongguben`, `meigujingzichan`, `zongzichan`, `jingzichan`

---

#### 静态方法

```python
TdxHqEtfClient.is_etf(market, code) -> bool      # 判断是否为 ETF
TdxHqEtfClient.auto_market_code(code) -> int      # 自动判断市场
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

## 性能参考

> 测试环境: 180.153.18.170:7709, 2026-06-21

| 接口 | 平均耗时 | 说明 |
|------|----------|------|
| connect_to_any | ~300ms | 首次连接含握手 |
| get_etf_list(SH) | ~2.5s | 811 只 ETF, 多页获取 |
| get_etf_bars(5分钟,10) | ~70ms | — |
| get_etf_quotes(1只) | ~70ms | — |
| get_etf_quotes(2只) | ~70ms | 批量几乎无额外开销 |
| get_etf_minute_time_data | ~65ms | 240 条 |
| get_etf_transaction_data(100) | ~65ms | — |
| get_etf_xdxr_info | ~70ms | 15 条 |
| get_etf_finance_info | ~65ms | 7 项 |

---

## 模块结构

```
src/etf/
├── mod.rs              # 模块入口
├── constants.rs        # ETF 常量 (代码前缀, 市场代码复用 protocol::constants)
├── types.rs            # ETF 数据类型 (EtfInfo, EtfBar, EtfQuote 等)
├── client.rs           # ETF 客户端封装 (TdxHqEtfClient)
└── utils.rs            # 工具函数 (ETF 代码验证)
```

---

## 常见问题

### Q: ETF 代码如何判断市场？

A: 根据代码前缀自动判断：
- 沪市: 50xxxx, 51xxxx → `market=1`
- 深市: 15xxxx, 16xxxx → `market=0`

或使用 `TdxHqEtfClient.auto_market_code(code)` 自动判断。

### Q: ETF 是否支持复权？

A: 支持。ETF 复权只处理现金分红，公式简化为 `P_ex = P_close - D`。

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [F10 模块](F10.md) | F10 公司资料 |
| [API 参考](API_REFERENCE.md) | 完整 Python API |
| [复权算法](../ADJUSTER_ALGORITHM.md) | 复权公式详解 |
