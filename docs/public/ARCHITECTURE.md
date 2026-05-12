# tdxrs 架构说明

## 模块分层

```
┌─────────────────────────────────────────────┐
│               Python 层                      │
│  TdxHqClient / TdxDirectClient / Reader     │
│  → list[dict] / list[tuple] / DataFrame     │
├─────────────────────────────────────────────┤
│               PyO3 绑定层                    │
│  py_client.rs / py_reader.rs /              │
│  py_direct_client.rs / py_dataframe.rs      │
├──────────────┬──────────────────────────────┤
│  net/        │         reader/              │
│  client.rs   │  daily_bar.rs  (日线)        │
│  pool.rs     │  min_bar.rs    (分钟线)      │
│  direct_*.rs │  block.rs      (板块)        │
│  async_*.rs  │  financial.rs  (财务)        │
├──────────────┴────────────┬─────────────────┤
│       protocol/           │   constants.rs  │
│  parsers.rs   (11 解析器)  │   helpers.rs    │
│  types.rs     (数据结构)   │   error.rs      │
│  constants.rs (协议常量)   │                 │
├───────────────────────────┴─────────────────┤
│            connection.rs (TCP)              │
└─────────────────────────────────────────────┘
```

## 核心模块

### Reader — 本地文件解析

解析通达信客户端本地存储的二进制数据文件：

| Reader | 文件格式 | 记录长度 | 说明 |
|--------|----------|:---:|------|
| `DailyBarReader` | `.day` | 32B | 日线 (OHLCV + 日期) |
| `MinBarReader` | `.lc5` | 32B | 5分钟线 (整数价格) |
| `LcMinBarReader` | `.lc5` | 32B | LC 分钟线 (浮点价格) |
| `BlockReader` | `.dat` | 变长 | 板块/行业分类 |
| `FinancialReader` | `.dat` | 变长 | 财务报表数据 |

数据流：`二进制文件 → Reader::parse → Vec<Record> → Python dict/tuple/DataFrame`

### Protocol — 网络协议

实现 TDX 行情服务器 TCP 协议的请求构建与响应解析，覆盖 11 种数据类型：

| 解析器 | 对应数据 |
|--------|----------|
| `parse_security_bars` | 个股 K 线 (差分编码) |
| `parse_index_bars` | 指数 K 线 |
| `parse_security_quotes` | 实时行情 (五档买卖) |
| `parse_security_list` | 证券列表 |
| `parse_security_count` | 证券数量 |
| `parse_minute_time_data` | 分时数据 |
| `parse_transaction_data` | 逐笔成交 |
| `parse_finance_info` | 财务信息 (34 字段, TDX 原始值, 不转换单位) |
| `finance_fields` | gpcw 数据 → 45 个核心指标英文名映射 |
| `parse_xdxr_info` | 除权除息 |
| `parse_block_info_meta` | 板块元数据 |
| `parse_block_info` | 板块原始数据 |

数据流：`API 调用 → 构建请求包 → TCP 发送 → 接收响应 → zlib 解压 → 解析器 → 结构化数据`

### Net/Utils — 公共工具

`src/net/utils.rs` 提取三客户端共享逻辑，消除重复：
- `code_bytes` / `build_security_bars_packet` / `build_index_bars_packet` — 请求包构建
- `perform_handshake` — TDX 三步握手
- `decompress_zlib` — 响应解压
- `fetch_context_bars_for_adjust` — 复权上下文拉取 (泛型闭包适配不同连接模型)

### Logging — 轻量日志

`src/logging.rs` 提供 `logd!/logi!/logw!/loge!` 宏，按 `TDXRS_LOG` 环境变量控制级别 (off/error/warn/info/debug)。debug 编译默认 `debug`，release 默认 `warn`。

### Net — 连接管理

三种客户端覆盖不同使用场景：

| 客户端 | 连接策略 | 特性 |
|--------|----------|------|
| `TdxHqClient` | 连接池 (默认 5) | 连接复用、自动心跳、断线重连、智能重试、数据缓存 |
| `TdxDirectClient` | 每次请求新建连接 | 无状态、高并发友好 (无 Mutex 争用) |
| `AsyncTdxHqClient` | tokio 异步单连接 | 事件驱动、适合 tokio 生态集成 |
| `TdxFinanceClient` | 每次请求新建连接 (独立超时) | 大文件分片下载、gpcw 数据解析 |

连接池机制：
```
borrow(server) → 空闲队列取 → 无空闲且未达上限 → 新建连接+握手 → 返回 guard
                                                                    ↓
return_connection ← 请求完成、guard 析构 ← 自动归还
```

## 数据输出格式

支持三种输出格式，按需选择：

| 格式 | Python 方法 | 适用场景 |
|------|------------|----------|
| `list[dict]` | `get_security_bars()` | 调试打印、少量数据、API 返回 |
| `list[tuple]` | `get_security_bars_tuples()` | 遍历、中等数据量 |
| `DataFrame` | `get_security_bars_dataframe()` | 数据分析、回测、批量处理 |

DataFrame 采用 dict-of-lists → `pd.DataFrame()` 构建，数据按列组织，pandas 可直接利用列式内存布局。

## 复权处理

- 网络 API 默认返回**前复权**数据（历史价格向后调整，保持现价不变）
- 支持 `fq=0`(未复权) / `fq=1`(前复权) / `fq=2`(后复权) 参数选择
- 本地 `.day` 文件始终为未复权原始数据
- 复权算法位于 `src/protocol/adjuster.rs`，采用 A 股标准除权除息公式：
  ```
  P_ex = (P_close - D + P_rights × R_rights) / (1 + R_bonus + R_rights)
  factor = P_ex / P_close  (QFQ, 前复权因子)
  ```
- **context_bars**: 当除权事件早于 K 线数据范围时，客户端自动向后翻页获取更早的 K 线作为前收盘价计算上下文。最多获取 6400 根历史 K 线。解决了早期除权事件被静默丢弃的问题。
- 详细算法文档见 [复权算法说明](ADJUSTER_ALGORITHM.md)

## 扩展点

- **新增数据源**: 实现 `Reader` trait pattern，注册到 `reader/` 模块
- **新增客户端策略**: 参考 `direct_client.rs` 模式，实现自定义连接管理
- **自定义输出格式**: 扩展 `py_dataframe.rs`，添加新的列式输出函数
