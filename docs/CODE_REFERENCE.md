# 代码引用与关联关系

> 目的: 版本迭代时避免错误覆盖——改一处，知全貌。
> 最后更新: 2026-05-12 | v0.5.0

---

## 1. 模块依赖图

```
                    lib.rs (PyO3 入口)
                   /    |    |    \
           python/   net/  protocol/  reader/  logging  constants  helpers  error
          /|||||\\      ...........     ||||
        client reader const df direct  adjuster parsers types constants
```

依赖方向: **上层 → 下层**。`protocol` 不感知 `net`，`reader` 不感知 `python`。

### 详细引用关系

```
error.rs          ← 被所有模块引用 (Result, TdxError)
constants.rs      ← reader/, protocol/parsers.rs, protocol/adjuster.rs, net/pool.rs
helpers.rs        ← protocol/parsers.rs (get_price, get_volume)
logging.rs        ← 独立 (通过宏引用，无编译期依赖)

protocol/
  types.rs        ← protocol/parsers.rs, protocol/adjuster.rs, net/client.rs,
                    net/direct_client.rs, net/async_client.rs, net/utils.rs,
                    net/finance_client.rs, python/py_client.rs,
                    python/py_direct_client.rs, python/py_dataframe.rs
  parsers.rs      ← net/client.rs, net/direct_client.rs, net/async_client.rs,
                    net/utils.rs, net/finance_client.rs
  adjuster.rs     ← net/client.rs, net/direct_client.rs, net/async_client.rs
                    (通过 use crate::protocol::adjuster)
  constants.rs    ← net/client.rs, net/utils.rs, net/pool.rs, python/py_constants.rs

net/
  connection.rs   ← net/pool.rs, net/client.rs, net/direct_client.rs,
                    net/finance_client.rs, net/utils.rs
  packet.rs       ← net/client.rs, net/utils.rs, net/direct_client.rs,
                    net/async_client.rs, net/finance_client.rs
  pool.rs         ← net/client.rs
  utils.rs        ← net/client.rs, net/direct_client.rs, net/async_client.rs,
                    net/finance_client.rs
  client.rs       ← python/py_client.rs (TdxHqClient)
  direct_client.rs← python/py_direct_client.rs (TdxDirectClient)
  finance_client.rs ← 暂无 Python 绑定
  async_client.rs   ← 暂无 Python 绑定

python/
  py_client.rs    ← lib.rs (注册 TdxHqClient)
  py_direct_client.rs ← lib.rs (注册 TdxDirectClient)
  py_reader.rs    ← lib.rs (注册 5 个 Reader)
  py_dataframe.rs ← py_client.rs, py_reader.rs
  py_constants.rs ← lib.rs (register_constants)

reader/
  daily_bar.rs    ← python/py_reader.rs
  min_bar.rs      ← python/py_reader.rs
  block.rs        ← python/py_reader.rs, net/client.rs, net/direct_client.rs
  financial.rs    ← python/py_reader.rs, net/finance_client.rs
```

---

## 2. 关键类型流

### types.rs 中定义的结构体 — 被广泛消费

| 类型 | 定义于 | 被消费于 |
|------|:-----:|---------|
| `SecurityBar` | `protocol/types.rs` | `parsers`, `adjuster`, `client`, `direct_client`, `async_client`, `utils`, `py_client`, `py_direct_client`, `py_dataframe` |
| `IndexBar` | `protocol/types.rs` | `parsers`, `adjuster`, `client`, `direct_client`, `async_client`, `py_client`, `py_direct_client`, `py_dataframe` |
| `SecurityQuote` | `protocol/types.rs` | `parsers`, `client`, `direct_client`, `async_client`, `py_client`, `py_direct_client`, `py_dataframe` |
| `FinanceInfo` | `protocol/types.rs` | `parsers`, `client`, `direct_client`, `async_client`, `finance_client`, `py_client`, `py_direct_client`, `py_dataframe` |
| `XdXrInfo` | `protocol/types.rs` | `parsers`, `adjuster`, `client`, `direct_client`, `async_client`, `finance_client`, `utils`, `py_client`, `py_direct_client` |
| `SecurityInfo` | `protocol/types.rs` | `parsers`, `client`, `direct_client`, `async_client`, `py_client`, `py_direct_client` |
| `TickData` | `protocol/types.rs` | `parsers`, `client`, `direct_client`, `async_client`, `py_client`, `py_direct_client` |
| `MinuteTimePrice` | `protocol/types.rs` | `parsers`, `client`, `direct_client`, `async_client`, `py_client`, `py_direct_client` |
| `BlockInfoMeta` | `protocol/types.rs` | `parsers`, `client`, `direct_client` |

### parsers.rs 中的解析函数

| 解析器 | 被调用方 |
|------|---------|
| `parse_security_bars` | `client`, `direct_client`, `async_client`, `utils` |
| `parse_index_bars` | `client`, `direct_client`, `async_client` |
| `parse_security_quotes` | `client`, `direct_client`, `async_client` |
| `parse_finance_info` | `client`, `direct_client`, `async_client`, `finance_client` |
| `parse_xdxr_info` | `client`, `direct_client`, `async_client`, `finance_client` |
| `parse_security_count` | `client`, `direct_client`, `async_client` |
| `parse_security_list` | `client`, `direct_client`, `async_client` |
| `parse_minute_time_data` | `client`, `direct_client`, `async_client` |
| `parse_history_minute_time_data` | `client`, `direct_client`, `async_client` |
| `parse_transaction_data` | `client`, `direct_client`, `async_client` |
| `parse_history_transaction_data` | `client`, `direct_client`, `async_client` |
| `parse_block_info_meta` | `client`, `direct_client` |
| `parse_block_info` | `client`, `direct_client` |

### utils.rs 的工具函数

| 函数 | 被调用方 |
|------|---------|
| `code_bytes` | `client`, `direct_client`, `async_client`, `utils` (自身) |
| `build_security_bars_packet` | `client`, `direct_client`, `async_client`, `utils` |
| `build_index_bars_packet` | `client` |
| `perform_handshake` | `client`, `direct_client`, `finance_client` |
| `decompress_zlib` | `direct_client`, `utils` (自身) |
| `fetch_context_bars_for_adjust` | `client`, `direct_client` |

---

## 3. 变更影响矩阵

改哪个文件时，必须同步检查以下文件:

| 修改内容 | 影响范围 | 必须检查的文件 |
|---------|---------|-------------|
| **types.rs 增/删/改字段** | 全网 | `parsers.rs` → `adjuster.rs` → `py_client.rs` → `py_direct_client.rs` → `py_dataframe.rs` → `API_REFERENCE.md` |
| **parsers.rs 解析逻辑** | 全网 | 所有 `net/` 客户端 → `py_client.rs` → `py_direct_client.rs` |
| **adjuster.rs 签名/算法** | K 线链路 | `client.rs` → `direct_client.rs` → `async_client.rs` |
| **utils.rs 公共函数** | 四客户端 | `client.rs` + `direct_client.rs` + `async_client.rs` + `finance_client.rs` |
| **client.rs 新增 API** | 三客户端 + Python | ① `direct_client.rs` ② `async_client.rs` ③ `py_client.rs` ④ `py_direct_client.rs` (如适用) |
| **protocol/constants.rs** | 全网 | `py_constants.rs` → `python/tdxrs/constants.py` → `API_REFERENCE.md` |
| **error.rs 新增变体** | 上层调用 | 所有 `match` / `?` 涉及的调用链 |
| **connection.rs** | 网络层 | `pool.rs`, `client.rs`, `direct_client.rs`, `finance_client.rs`, `utils.rs` |
| **packet.rs** | 网络层 | 同 connection.rs |

---

## 4. Python ↔ Rust 映射

### TdxHqClient (Rust: `net/client.rs` → Python: `py_client.rs`)

| Rust 方法 | Python 暴露 |
|----------|:--:|
| `connect` / `connect_to_any` / `disconnect` / `is_connected` | ✅ |
| `set_auto_retry` / `set_cache_ttl` / `set_connect_timeout` | ✅ |
| `set_servers` / `add_server` / `reorder_servers` / `probe_servers` | ✅ |
| `pool_stats` | ✅ |
| `get_security_bars` / `get_security_bars_all` | ✅ + `_tuples` + `_dataframe` |
| `get_index_bars` / `get_index_bars_all` | ✅ + `_tuples` + `_dataframe` |
| `get_security_quotes` | ✅ + `_tuples` + `_dataframe` |
| `get_security_list` / `get_security_count` | ✅ |
| `get_minute_time_data` / `get_history_minute_time_data` | ✅ |
| `get_transaction_data` / `get_history_transaction_data` | ✅ |
| `get_finance_info` | ✅ + `_dataframe` |
| `get_xdxr_info` / `get_and_parse_block_info` | ✅ |
| `get_block_info` / `get_block_info_meta` | Rust only |

### TdxDirectClient (Rust: `direct_client.rs` → Python: `py_direct_client.rs`)

所有 13 个数据 API 已暴露。**不暴露**: 自动分页 (`_all`)、tuple/DataFrame 模式、连接管理 API。

### Reader (Rust: `reader/*.rs` → Python: `py_reader.rs`)

| Rust 解析器 | Python 类 |
|-----------|----------|
| `parse_daily_bar` / `read_daily_bar_file` | `DailyBarReader` |
| `parse_min_bar` / `read_min_bar_file` | `MinBarReader` |
| `parse_lc_min_bar` / `read_lc_min_bar_file` | `LcMinBarReader` |
| `parse_block` / `read_block_file` | `BlockReader` |
| `parse_financial` / `read_financial_file` | `FinancialReader` |

### DataFrame 辅助 (`py_dataframe.rs`)

| 函数 | 用于 |
|------|------|
| `security_bars_to_df` | `get_security_bars_dataframe` |
| `index_bars_to_df` | `get_index_bars_dataframe` |
| `quotes_to_df` | `get_security_quotes_dataframe` |
| `finance_to_df` | `get_finance_info_dataframe` |
| `daily_records_to_df` | `DailyBarReader.to_dataframe` |
| `min_records_to_df` | `MinBarReader.to_dataframe` |

---

## 5. 一致性约定

### 新增 API 时的必改清单

```
1.  Rust 实现       → net/client.rs (TdxHqClient)
2.  裸连接复刻       → net/direct_client.rs
3.  异步复刻 (如适用) → net/async_client.rs
4.  Python dict 绑定 → python/py_client.rs (或 py_direct_client.rs)
5.  tuple 模式 (如适用) → python/py_client.rs
6.  DataFrame (如适用) → python/py_dataframe.rs
7.  API 文档         → docs/public/API_REFERENCE.md
```

### 不改的三处同步

| 内容 | 位置 | 同步要求 |
|------|------|:--:|
| `code_bytes` | `utils.rs` | 永远从 utils import，禁止本地定义 |
| `build_*_packet` | `utils.rs` | 同上 |
| `perform_handshake` | `utils.rs` | 同上 |
| `fetch_context_bars_for_adjust` | `utils.rs` | 同上 |

### 字段编号常量

`protocol/constants.rs` 中的 K 线种类 (KLINE_*)、复权类型 (fq_type)、市场代码等 → 同时注册到 `python/py_constants.rs` → 导出到 `python/tdxrs/constants.py`。

---

## 6. 跨层引用速查

```
如果你想改 X                         → 必须同时检查 Y
─────────────────────────────────────────────────────────
SecurityBar 加字段                    → parsers(解析) → adjuster(复权不调整新字段)
                                        → py_client(序列化) → py_dataframe(列)
                                        → py_direct_client(序列化)
                                        → API_REFERENCE.md

XdXrInfo 加字段                       → parsers(category-based 解析)
                                        → adjuster(只用 fenhong/songzhuangu/peigu/peigujia)
                                        → py_client/py_direct_client(序列化)

parsers.rs 中修正解析偏移              → 对比 tdxpy 原版, 运行 compare_tdxpy_tdxrs.py

adjust_security_bars 签名变更          → client/direct_client/async_client 三处调用点
                                        → ADJUSTER_ALGORITHM.md

TcpConnection 方法变更                 → pool(连接管理) → client(池借还)
                                        → direct_client(独立用) → finance_client(独立用)
                                        → utils(handshake)

protocol/constants 命令码/端口/限制     → 全网使用这些常量的地方
                                        → py_constants → constants.py

新增大文件下载协议 (如 gpcw)           → finance_client(独立连接+超时) → 不放入client(pool)
```

---

## 7. 文件清单 (按层)

| 层 | 文件 | 行数(约) | 职责 |
|----|------|:--:|------|
| 入口 | `lib.rs` | 30 | PyO3 模块注册 |
| 基础 | `error.rs` | 40 | TdxError + Result |
| | `constants.rs` | 80 | 日期/字节 解码工具 |
| | `helpers.rs` | 200 | get_price / get_volume |
| | `logging.rs` | 120 | 日志宏 |
| 协议 | `protocol/types.rs` | 260 | 全部数据结构 |
| | `protocol/parsers.rs` | 1200 | 13 个解析器 |
| | `protocol/adjuster.rs` | 320 | 复权算法 |
| | `protocol/constants.rs` | 180 | 命令码/市场/K线/服务器 |
| 网络 | `net/connection.rs` | 60 | 同步 TCP |
| | `net/async_connection.rs` | 80 | 异步 TCP |
| | `net/packet.rs` | 40 | 响应头 |
| | `net/pool.rs` | 260 | 连接池 |
| | `net/utils.rs` | 210 | 公共工具 |
| | `net/client.rs` | 870 | TdxHqClient |
| | `net/direct_client.rs` | 310 | TdxDirectClient |
| | `net/finance_client.rs` | 250 | TdxFinanceClient |
| | `net/async_client.rs` | 490 | AsyncTdxHqClient |
| 读取 | `reader/daily_bar.rs` | 110 | 日线 |
| | `reader/min_bar.rs` | 200 | 分钟线 |
| | `reader/block.rs` | 160 | 板块 |
| | `reader/financial.rs` | 160 | gpcw 财务 |
| Python | `python/py_client.rs` | 750 | TdxHqClient 绑定 |
| | `python/py_direct_client.rs` | 400 | TdxDirectClient 绑定 |
| | `python/py_reader.rs` | 500 | 5 Reader 绑定 |
| | `python/py_dataframe.rs` | 260 | DataFrame 构建 |
| | `python/py_constants.rs` | 50 | 常量注册 |
