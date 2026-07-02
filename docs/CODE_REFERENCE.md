# 代码引用与关联关系

> 目的: 版本迭代时避免错误覆盖——改一处，知全貌。
> 最后更新: 2026-07-02 | v0.6.5

---

## 1. 模块依赖图

```
                    lib.rs (PyO3 入口)
                   /    |    \    \    \    \
           python/   net/  protocol/  reader/  fund/  block/  profile/
                      |       |                   |      |       |
                   (5 客户端) (parsers/adjuster) (基金) (板块)  (F10)
```

新增模块 (v0.6.2+):
- `fund/` — 基金数据模块 (ETF/LOF/REITs/分级基金)
- `block/` — 板块数据模块 (概念/行业/地域)
- `profile/` — F10 公司资料模块 (需 --features f10)
- `error_codes.rs` — 错误码枚举 (ErrorCode → TdxError)
- `python/py_fund.rs` — 基金 Python 绑定
- `python/py_async_client.rs` — 异步客户端 Python 绑定
- `python/tdxrs/cli.py` — CLI 命令行工具
- `python/tdxrs/downloader.py` — 批量下载/增量更新
- `python/tdxrs/cli_format.py` — CLI 输出格式化

依赖方向: **上层 → 下层**。`protocol` 不感知 `net`，`reader` 不感知 `python`。

### 详细引用关系

```
error.rs          ← 被所有模块引用 (Result, TdxError)
error_codes.rs    ← error.rs (ErrorCode 枚举 → TdxError 转换)
constants.rs      ← reader/, protocol/, net/, fund/, block/, profile/
helpers.rs        ← protocol/parsers.rs (get_price, get_volume)
logging.rs        ← 独立 (通过宏引用，无编译期依赖)

protocol/
  types.rs        ← protocol/parsers.rs, protocol/adjuster.rs, net/client.rs,
                    net/direct_client.rs, net/async_client.rs, net/utils.rs,
                    net/finance_client.rs, fund/client.rs, block/query.rs,
                    python/py_client.rs, python/py_direct_client.rs,
                    python/py_dataframe.rs, python/py_fund.rs
  parsers.rs      ← net/client.rs, net/direct_client.rs, net/async_client.rs,
                    net/utils.rs, net/finance_client.rs, fund/client.rs,
                    block/query.rs
  adjuster.rs     ← net/client.rs, net/direct_client.rs, net/async_client.rs
  constants.rs    ← net/client.rs, net/utils.rs, net/pool.rs, fund/constants.rs,
                    python/py_constants.rs

net/
  connection.rs   ← net/pool.rs, net/client.rs, net/direct_client.rs,
                    net/finance_client.rs, net/utils.rs, fund/client.rs,
                    block/client.rs, profile/client.rs
  packet.rs       ← net/client.rs, net/utils.rs, net/direct_client.rs,
                    net/async_client.rs, net/finance_client.rs, fund/client.rs,
                    block/client.rs, profile/client.rs
  pool.rs         ← net/client.rs
  utils.rs        ← net/client.rs, net/direct_client.rs, net/async_client.rs,
                    net/finance_client.rs, fund/client.rs, block/query.rs
  client.rs       ← python/py_client.rs (TdxHqClient)
  direct_client.rs← python/py_direct_client.rs (TdxDirectClient)
  finance_client.rs ← python/py_client.rs (TdxFinanceClient 绑定)
  async_client.rs   ← python/py_async_client.rs (AsyncTdxHqClient 绑定)

fund/  (独立模块，不依赖 net/client.rs)
  client.rs       ← python/py_fund.rs (TdxHqFundClient)
  constants.rs    ← fund/client.rs, fund/types.rs
  types.rs        ← fund/client.rs
  utils.rs        ← fund/client.rs

block/  (独立模块，不依赖 net/client.rs)
  client.rs       ← python/py_fund.rs (TdxBlockClient 绑定在此文件)
  query.rs        ← block/client.rs
  types.rs        ← block/client.rs, block/query.rs

profile/  (独立模块，需 --features f10)
  client.rs       ← lib.rs (条件编译)
  parser.rs       ← profile/client.rs
  parser_f10.rs   ← profile/client.rs
  types.rs        ← profile/client.rs, profile/parser.rs, profile/parser_f10.rs
  constants.rs    ← profile/client.rs, profile/parser.rs

python/
  py_client.rs    ← lib.rs (注册 TdxHqClient)
  py_direct_client.rs ← lib.rs (注册 TdxDirectClient)
  py_async_client.rs  ← lib.rs (注册 AsyncTdxHqClient)
  py_fund.rs      ← lib.rs (注册 TdxHqFundClient, TdxBlockClient)
  py_reader.rs    ← lib.rs (注册 5 个 Reader)
  py_dataframe.rs ← py_client.rs, py_reader.rs
  py_constants.rs ← lib.rs (register_constants)

reader/
  daily_bar.rs    ← python/py_reader.rs
  min_bar.rs      ← python/py_reader.rs
  block.rs        ← python/py_reader.rs, net/client.rs, net/direct_client.rs
  financial.rs    ← python/py_reader.rs, net/finance_client.rs

python/tdxrs/  (Python 包)
  cli.py          ← __main__.py (CLI 入口)
  cli_format.py   ← cli.py (输出格式化)
  downloader.py   ← cli.py (批量下载/增量更新)
  constants.py    ← _internal (常量子模块)
  pro.py          ← _internal (旧入口，已 deprecate)
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

### fund/types.rs 中定义的结构体

| 类型 | 定义于 | 被消费于 |
|------|:-----:|---------|
| `FundType` | `fund/constants.rs` | `fund/client.rs`, `fund/utils.rs`, `python/py_fund.rs` |
| `FundInfo` | `fund/types.rs` | `fund/client.rs`, `python/py_fund.rs` |
| `FundBar` | `fund/types.rs` | `fund/client.rs`, `python/py_fund.rs` |
| `FundQuote` | `fund/types.rs` | `fund/client.rs`, `python/py_fund.rs` |
| `FundNav` | `fund/types.rs` | `fund/client.rs`, `python/py_fund.rs` |
| `FundPcf` | `fund/types.rs` | `fund/client.rs`, `python/py_fund.rs` |

### block/types.rs 中定义的结构体

| 类型 | 定义于 | 被消费于 |
|------|:-----:|---------|
| `BlockInfo` | `block/types.rs` | `block/client.rs`, `block/query.rs`, `python/py_fund.rs` |

### profile/types.rs 中定义的结构体

| 类型 | 定义于 | 被消费于 |
|------|:-----:|---------|
| `CompanyInfoCategory` | `profile/types.rs` | `profile/client.rs`, `profile/parser.rs` |
| `CompanyInfoContent` | `profile/types.rs` | `profile/client.rs`, `profile/parser.rs` |
| `ProfileField` | `profile/types.rs` | `profile/client.rs`, `profile/parser_f10.rs` |

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
| `parse_transaction_data_with_coefficient` | `client`, `direct_client`, `async_client` (基金价格精度) |
| `parse_history_transaction_data` | `client`, `direct_client`, `async_client` |
| `parse_history_transaction_data_with_coefficient` | `client`, `direct_client`, `async_client` |
| `parse_block_info_meta` | `client`, `direct_client`, `block/query` |
| `parse_block_info` | `client`, `direct_client`, `block/query` |

### profile/parser.rs 中的解析函数

| 解析器 | 被调用方 |
|------|---------|
| `parse_company_info_category` | `profile/client.rs` |
| `parse_company_info_content` | `profile/client.rs` |

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
| **protocol/types.rs 增/删/改字段** | 全网 | `parsers.rs` → `adjuster.rs` → `py_client.rs` → `py_direct_client.rs` → `py_dataframe.rs` → `API_REFERENCE.md` |
| **parsers.rs 解析逻辑** | 全网 | 所有 `net/` 客户端 → `fund/client.rs` → `block/query.rs` → `py_client.rs` → `py_direct_client.rs` |
| **parsers.rs 新增 _with_coefficient** | 基金链路 | `client.rs` + `direct_client.rs` + `async_client.rs` (传入 coefficient) |
| **adjuster.rs 签名/算法** | K 线链路 | `client.rs` → `direct_client.rs` → `async_client.rs` |
| **utils.rs 公共函数** | 六客户端 | `client.rs` + `direct_client.rs` + `async_client.rs` + `finance_client.rs` + `fund/client.rs` + `block/query.rs` |
| **client.rs 新增 API** | 三客户端 + Python | ① `direct_client.rs` ② `async_client.rs` ③ `py_client.rs` ④ `py_direct_client.rs` (如适用) |
| **protocol/constants.rs** | 全网 | `py_constants.rs` → `python/tdxrs/constants.py` → `API_REFERENCE.md` |
| **error.rs 新增变体** | 上层调用 | 所有 `match` / `?` 涉及的调用链 |
| **error_codes.rs 新增错误码** | 全网 | `error.rs` (ErrorCode → TdxError 转换) |
| **connection.rs** | 网络层 | `pool.rs`, `client.rs`, `direct_client.rs`, `finance_client.rs`, `fund/client.rs`, `block/client.rs`, `profile/client.rs` |
| **packet.rs** | 网络层 | 同 connection.rs |
| **fund/types.rs 修改** | 基金链路 | `fund/client.rs` → `py_fund.rs` → `FUND.md` |
| **fund/constants.rs 修改** | 基金链路 | `fund/client.rs`, `fund/utils.rs`, `py_fund.rs` |
| **block/types.rs 修改** | 板块链路 | `block/client.rs` → `block/query.rs` → `py_fund.rs` |
| **profile/types.rs 修改** | F10 链路 | `profile/parser.rs` → `profile/parser_f10.rs` → `profile/client.rs` |
| **get_security_coefficient** | 基金精度 | `protocol/types.rs` → 所有客户端交易数据解析 |

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

### AsyncTdxHqClient (Rust: `async_client.rs` → Python: `py_async_client.rs`)

v0.6.3 新增。API 与 TdxHqClient 一致，通过 `block_on()` 同步调用。内部使用 Channel 连接池，无锁争用。

| Rust 方法 | Python 暴露 |
|----------|:--:|
| `connect` / `connect_to_any` / `disconnect` / `is_connected` | ✅ |
| `set_auto_retry` / `set_cache_ttl` / `set_connect_timeout` | ✅ |
| `set_servers` / `add_server` / `reorder_servers` / `probe_servers` | ✅ |
| `pool_stats` | ✅ |
| `get_security_bars` / `get_security_bars_all` | ✅ + `_dataframe` |
| `get_index_bars` / `get_index_bars_all` | ✅ + `_dataframe` |
| `get_security_quotes` | ✅ + `_dataframe` |
| `get_security_list` / `get_security_count` | ✅ |
| `get_minute_time_data` / `get_history_minute_time_data` | ✅ |
| `get_transaction_data` / `get_history_transaction_data` | ✅ |
| `get_finance_info` | ✅ |
| `get_xdxr_info` / `get_and_parse_block_info` | ✅ |

### TdxHqFundClient (Rust: `fund/client.rs` → Python: `py_fund.rs`)

v0.6.2 新增。基金专用客户端，独立连接管理。

| Rust 方法 | Python 暴露 |
|----------|:--:|
| `connect` / `connect_to_any` / `disconnect` | ✅ |
| `get_fund_bars` | ✅ + `_dataframe` |
| `get_fund_quotes` | ✅ |
| `get_fund_nav` | ✅ |
| `get_fund_purchase_redemption` | ✅ |
| `classify_fund` (静态) | ✅ |

### TdxBlockClient (Rust: `block/client.rs` → Python: `py_fund.rs`)

v0.6.2 新增，v0.6.5 扩展。板块专用客户端，独立连接管理。Python 绑定在 `py_fund.rs` 中。

| Rust 方法 | Python 暴露 | 说明 |
|----------|:--:|------|
| `new` / `with_default` | ✅ | 构造函数 |
| `set_server` / `set_timeout` | ✅ | 配置 |
| `get_block_bars` / `get_block_bars_default` | ✅ | 板块K线 (带级别限制) |
| `get_block_quotes` | ✅ | 板块实时行情 (88xxxx) |
| `get_block_list` | ✅ | 下载并解析指定 `.dat` 板块文件 |
| `get_industry_blocks` | ✅ | 行业/筛选板块 (block_fg.dat) |
| `get_concept_blocks` | ✅ | 概念板块 (block_gn.dat) |
| `get_index_blocks` | ✅ | 指数成分 (block_zs.dat) |

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
通用 API (行情/K线/逐笔等):
1.  Rust 实现       → net/client.rs (TdxHqClient)
2.  裸连接复刻       → net/direct_client.rs
3.  异步复刻 (如适用) → net/async_client.rs
4.  Python dict 绑定 → python/py_client.rs (或 py_direct_client.rs)
5.  tuple 模式 (如适用) → python/py_client.rs
6.  DataFrame (如适用) → python/py_dataframe.rs
7.  API 文档         → docs/public/API_REFERENCE.md

基金 API (净值/行情/申赎等):
1.  Rust 实现       → fund/client.rs (TdxHqFundClient)
2.  类型定义         → fund/types.rs
3.  常量/系数         → fund/constants.rs
4.  Python 绑定      → python/py_fund.rs
5.  API 文档         → docs/public/FUND.md + API_REFERENCE.md

板块 API (列表/成分股等):
1.  Rust 实现       → block/client.rs (TdxBlockClient)
2.  查询逻辑         → block/query.rs
3.  类型定义         → block/types.rs
4.  Python 绑定      → python/py_fund.rs (与 FundClient 同文件)
5.  API 文档         → docs/public/API_REFERENCE.md

F10 API (公司资料):
1.  Rust 实现       → profile/client.rs (TdxF10Client)
2.  解析器           → profile/parser.rs + profile/parser_f10.rs
3.  类型定义         → profile/types.rs
4.  条件编译         → lib.rs (#[cfg(feature = "f10")])
5.  API 文档         → docs/public/F10.md
```

### 不改的三处同步

| 内容 | 位置 | 同步要求 |
|------|------|:--:|
| `code_bytes` | `utils.rs` | 永远从 utils import，禁止本地定义 |
| `build_*_packet` | `utils.rs` | 同上 |
| `perform_handshake` | `utils.rs` | 同上 |
| `fetch_context_bars_for_adjust` | `utils.rs` | 同上 |
| `get_security_coefficient` | `protocol/types.rs` | 基金精度核心，所有客户端共用 |
| `_DEFAULT_SERVERS` | `downloader.py` | Rust PRIMARY_SERVERS 为唯一源头，Python 从 Rust 同步 |

### 独立模块 (不共享连接池)

| 模块 | 连接方式 | 说明 |
|------|---------|------|
| `TdxHqClient` | 共享连接池 (Mutex) | 默认 5 连接，自动重试 |
| `TdxDirectClient` | 每次独立 TCP | 无池/无重试/无心跳 |
| `TdxFinanceClient` | 独立连接 | 超时 15s，分片下载 |
| `AsyncTdxHqClient` | Channel 连接池 | tokio 异步，无锁 |
| `TdxHqFundClient` | 独立连接 | 基金专用，不共享 |
| `TdxBlockClient` | 独立连接 | 板块专用，不共享 |
| `TdxF10Client` | 独立连接 | F10 专用，需 f10 feature |

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
                                        → fund/client.rs(独立用) → block/client.rs(独立用)
                                        → profile/client.rs(独立用)
                                        → utils(handshake)

protocol/constants 命令码/端口/限制     → 全网使用这些常量的地方
                                        → py_constants → constants.py

新增大文件下载协议 (如 gpcw)           → finance_client(独立连接+超时) → 不放入client(pool)

基金类型/系数变更                      → fund/constants.rs → fund/client.rs → py_fund.rs
                                        → protocol/types.rs (get_security_coefficient)
                                        → FUND.md

基金代码前缀变更                       → fund/constants.rs → fund/utils.rs → py_fund.rs
                                        → protocol/types.rs (get_security_coefficient)

板块查询逻辑变更                       → block/query.rs → block/client.rs → py_fund.rs
                                        → parsers.rs (复用 parse_block_info*)

F10 解析器变更                         → profile/parser.rs + profile/parser_f10.rs
                                        → profile/client.rs → lib.rs (条件编译)

CLI 命令变更                           → python/tdxrs/cli.py → cli_format.py
                                        → downloader.py (download/update 命令)
                                        → CLI.md
```

---

## 7. 文件清单 (按层)

| 层 | 文件 | 行数(约) | 职责 |
|----|------|:--:|------|
| 入口 | `lib.rs` | ~30 | PyO3 模块注册 (含 f10 条件编译) |
| 基础 | `error.rs` | ~40 | TdxError + Result |
| | `error_codes.rs` | 446 | ErrorCode 枚举 (错误码 → TdxError) |
| | `constants.rs` | ~80 | 日期/字节 解码工具 |
| | `helpers.rs` | ~200 | get_price / get_volume |
| | `logging.rs` | ~120 | 日志宏 |
| 协议 | `protocol/types.rs` | ~260 | 全部数据结构 + get_security_coefficient |
| | `protocol/parsers.rs` | ~1200 | 13 个解析器 + _with_coefficient 变体 |
| | `protocol/adjuster.rs` | ~320 | 复权算法 |
| | `protocol/constants.rs` | ~180 | 命令码/市场/K线/服务器 |
| 网络 | `net/connection.rs` | ~60 | 同步 TCP |
| | `net/packet.rs` | ~40 | 响应头 |
| | `net/pool.rs` | ~260 | 连接池 |
| | `net/utils.rs` | ~210 | 公共工具 (handshake/zlib/packet) |
| | `net/client.rs` | ~870 | TdxHqClient (连接池+重试+缓存) |
| | `net/direct_client.rs` | ~310 | TdxDirectClient (裸连接) |
| | `net/finance_client.rs` | ~250 | TdxFinanceClient (财务独立连接) |
| | `net/async_client.rs` | ~490 | AsyncTdxHqClient (tokio+Channel池) |
| 基金 | `fund/client.rs` | 321 | TdxHqFundClient (净值/行情/申赎) |
| | `fund/constants.rs` | 268 | FundType 枚举 + 代码前缀 + 价格系数 |
| | `fund/types.rs` | 344 | FundInfo/FundBar/FundQuote/FundNav/FundPcf |
| | `fund/utils.rs` | 81 | 基金代码验证/分类 |
| | `fund/mod.rs` | 66 | 模块入口 |
| 板块 | `block/client.rs` | 270 | TdxBlockClient (K线/行情/列表) |
| | `block/query.rs` | 289 | 板块查询逻辑 (复用 parsers) |
| | `block/types.rs` | 54 | BlockInfo |
| | `block/mod.rs` | 48 | 模块入口 |
| F10 | `profile/client.rs` | 278 | TdxF10Client (公司资料, 需 f10 feature) |
| | `profile/parser.rs` | 262 | 通用解析器 |
| | `profile/parser_f10.rs` | 265 | F10 专用解析器 |
| | `profile/types.rs` | 267 | CompanyInfoCategory/Content/ProfileField |
| | `profile/constants.rs` | 98 | F10 常量 |
| | `profile/mod.rs` | 37 | 模块入口 |
| 读取 | `reader/daily_bar.rs` | ~110 | 日线 |
| | `reader/min_bar.rs` | ~200 | 分钟线 |
| | `reader/block.rs` | ~220 | 板块 |
| | `reader/financial.rs` | ~160 | gpcw 财务 |
| Python | `python/py_client.rs` | ~750 | TdxHqClient 绑定 |
| | `python/py_direct_client.rs` | ~400 | TdxDirectClient 绑定 |
| | `python/py_async_client.rs` | 797 | AsyncTdxHqClient 绑定 |
| | `python/py_fund.rs` | 603 | TdxHqFundClient + TdxBlockClient 绑定 |
| | `python/py_reader.rs` | ~500 | 5 Reader 绑定 |
| | `python/py_dataframe.rs` | ~260 | DataFrame 构建 |
| | `python/py_constants.rs` | ~50 | 常量注册 |
| Python包 | `python/tdxrs/cli.py` | 852 | CLI 命令行 (quote/bars/trades/download 等) |
| | `python/tdxrs/cli_format.py` | 111 | CLI 输出格式化 (table/json/csv) |
| | `python/tdxrs/downloader.py` | 942 | 批量下载/增量更新 |
| | `python/tdxrs/constants.py` | ~30 | 常量子模块 |
| | `python/tdxrs/pro.py` | ~30 | 旧入口 (已 deprecate) |
