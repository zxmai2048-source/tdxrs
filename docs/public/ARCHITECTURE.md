# tdxrs 架构说明

## 模块分层

```
┌─────────────────────────────────────────────────────┐
│                    Python 层                         │
│  tdxrs (核心): TdxHqClient / TdxDirectClient / Reader│
│  tdxrs._internal (扩展): TdxHqFundClient / Block... │
│  → list[dict] / list[tuple] / DataFrame             │
├─────────────────────────────────────────────────────┤
│                    PyO3 绑定层                       │
│  py_client / py_direct_client / py_reader /         │
│  py_fund / py_block / py_profile / py_constants     │
├─────────────┬──────────────┬────────────────────────┤
│  net/       │  reader/     │  fund/  /  profile/    │
│  client.rs  │  daily_bar   │  client    client      │
│  pool.rs    │  min_bar     │  constants constants   │
│  direct_*.rs│  block       │  types     parser      │
│  async_*.rs │  financial   │  utils     parser_f10  │
│  f10_client │              │  block/                │
│  finance_*  │              │  query/types/client    │
├─────────────┴──────────────┴────────────────────────┤
│              protocol/  +  constants / helpers       │
│  parsers.rs (11) / adjuster.rs / types.rs           │
│  constants.rs / finance_fields.rs                   │
├─────────────────────────────────────────────────────┤
│              connection.rs (TCP)                     │
└─────────────────────────────────────────────────────┘
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
- `RateLimiter` — 请求速率限制器 (分级限流，上限 200 req/s)
- `auto_market` / `encode_gbk` / `encode_gbk_padded` — F10/Profile 共享工具

### Logging — 轻量日志

`src/logging.rs` 提供 `logd!/logi!/logw!/loge!` 宏，按 `TDXRS_LOG` 环境变量控制级别 (off/error/warn/info/debug)。debug 编译默认 `debug`，release 默认 `warn`。

所有网络模块已接入日志 (v0.6.1)：

| 模块 | 前缀 | 关键日志点 |
|------|------|-----------|
| `client.rs` | `hq` | 连接/断开/重试/重连/心跳失败 |
| `pool.rs` | `pool` | 连接池耗尽 |
| `direct_client.rs` | `direct` | 连接失败 |
| `f10_client.rs` | `f10` | 连接失败/分类获取失败 |
| `finance_client.rs` | `finance` | 缓存命中/股票未找到 |
| `profile/client.rs` | `profile` | 分类获取失败 |

### Net — 连接管理

四种客户端覆盖不同使用场景：

| 客户端 | 连接策略 | 特性 |
|--------|----------|------|
| `TdxHqClient` | 连接池 (默认 5) | 连接复用、自动心跳、断线重连、智能重试、数据缓存 |
| `AsyncTdxHqClient` | 通道化连接池 (默认 4) | tokio async、通道分发、真正并发、自动心跳 |
| `TdxDirectClient` | 每次请求新建连接 | 无状态、高并发友好 (无 Mutex 争用) |
| `TdxFinanceClient` | 每次请求新建连接 (独立超时) | 大文件分片下载、gpcw 数据解析 |

**TdxHqClient 连接池机制** (同步):
```
borrow(server) → 空闲队列取 → 无空闲且未达上限 → 新建连接+握手 → 返回 guard
                                                                    ↓
return_connection ← 请求完成、guard 析构 ← 自动归还
```

**AsyncTdxHqClient 通道化连接池** (异步):
```
connect() → 创建 N 个 ConnectionTask → 每个 task 独立 tokio::spawn
         → 每个 task 持有 mpsc::Receiver<Request>
         → 每个 task 串行处理请求 (send_and_recv)

try_send() → 轮转选择连接 → mpsc::Sender::try_send(Request)
           → 通道满 → 尝试下一个连接
           → Request 包含 oneshot::Sender 回复通道

ConnectionTask::run():
  while let Some(req) = rx.recv().await {
      result = send_and_recv(req.data)
      req.reply.send(result)   ← 通过 oneshot 返回结果
  }
```

优势: 连接间真正并发 (无全局 Mutex)，请求通过通道分发到各连接 task 内串行执行。
Python 绑定通过内部 `tokio::runtime::Runtime::block_on()` 同步调用，API 与 sync 版一致。

### Fund — 基金模块 (`TdxHqFundClient`)

基金模块封装 `TdxHqClient`，覆盖 ETF/LOF/REITs/分级基金等全部基金类型。通过 `FundType` 枚举自动分类。

- **连接方式**: 共享连接池 (与股票行情相同)
- **模块位置**: `src/fund/` (constants, types, client, utils)
- **Python 绑定**: `src/python/py_fund.rs` → `TdxHqFundClient`

数据流: `Python 调用 → FundType 分类 → TdxHqClient API → FundInfo 转换 → dict`

### Block — 板块查询 (`TdxBlockClient`)

板块模块提供指数/行业/概念板块的成分股查询和K线数据。使用独立客户端，内置K线级别限制。

- **连接方式**: 独立连接 (TdxDirectClient 封装)
- **模块位置**: `src/block/` (types, query, client)
- **Python 绑定**: `src/python/py_block.rs` → `TdxBlockClient`
- **限制**: 1分钟K线禁用，分钟级默认50根上限

### Profile / F10 — 源码编译模块 (`--features f10`)

F10 模块获取通达信公司基本面资料 (16 分类)，使用独立连接避免影响行情。因数据合规考虑，未包含在 pip 包中，需从源码编译启用。

- **连接方式**: 独立 TCP 连接 (每次请求新建+握手+关闭)
- **模块位置**: `src/profile/` (constants, types, parser, parser_f10, client) + `src/net/f10_client.rs`
- **Python 绑定**: `src/python/py_profile.rs` → `TdxF10Client`

数据流: `Python 调用 → 独立 TCP 连接 → 分类/内容 API → GBK 解码 → 文本解析 → 结构化数据`

共享工具 (`net/utils.rs`): `auto_market`, `encode_gbk`, `encode_gbk_padded` 供 F10 和 Profile 共用。

### Downloader — 批量下载 (Python)

`tdxrs.downloader` 模块提供全市场历史数据批量下载，纯 Python 实现，调用现有 Rust API。

- **多服务器轮转**: 创建多个 `TdxDirectClient` 实例，轮转分发请求
- **每服务器限流**: 日K 15 req/s，分时 10 req/s
- **自动翻页**: Python 层循环调用 `get_security_bars`，每页 800 条
- **默认 `.day` 格式**: 与通达信格式兼容，`DailyBarReader` 可直接读取
- **增量更新**: 记录每只股票最后日期，仅追加新数据
- **断点续传**: 每 50 只股票保存进度到 `.tdxrs_meta/checkpoint.json`

数据流:
```
Downloader.run()
  → ServerPool 轮转选择服务器
  → get_security_count → get_security_list → 全市场股票列表
  → 遍历: get_security_bars (循环翻页) → 写入 .day/.csv/.parquet
  → 更新 last_sync.json
```

### CLI — 命令行工具 (Python)

`tdxrs.cli` 模块提供命令行快速查询工具，纯 Python argparse 实现，零额外依赖。

- **13 个子命令**: quote / bars / minutes / trades / stocks / index / xdxr / download / update / download-xdxr / parse / servers / version
- **参数锁上限**: CLI 上限远低于库 API (quote 20 只, bars 800 条, download 50 req/s)
- **三种输出格式**: table (默认) / json / csv
- **复用现有模块**: `TdxDirectClient` (网络) + `Downloader` (下载) + `Reader` (解析)

数据流:
```
tdxrs quote 600519
  → argparse 解析参数 + 校验上限
  → pick_server() 随机选取服务器
  → TdxDirectClient(ip, port).get_security_quotes()
  → format_output(table/json/csv)
```

安装后直接使用:
```bash
tdxrs quote 600519              # 实时行情
tdxrs bars 600519 --count 30    # K线
tdxrs download --market sh      # 批量下载
tdxrs servers                   # 测试服务器
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
