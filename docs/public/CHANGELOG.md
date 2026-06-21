# 变更日志

## v0.6.0 (2026-06-21) — 扩展模块: ETF + F10

### 新增
- **ETF 模块** (`tdxrs.pro.TdxHqEtfClient`) — ETF 专用行情客户端
  - K线 (12 周期)、实时行情 (五档)、分时、逐笔、除权除息、财务
  - ETF 列表自动筛选 (沪市 50/51, 深市 15/16)
  - ETF 代码验证 + 市场自动识别
  - 共享连接池，与股票行情相同性能
- **F10 模块** (`tdxrs.pro.TdxF10Client`) — F10 公司资料客户端 (源码编译, `--features f10`)
  - 16 分类数据获取 (公司概况/财务分析/股东研究等)
  - 独立 TCP 连接，不影响行情数据
  - Rust 内置 F10 文本解析器 (267K 字符 4.6ms)
  - 结构化提取: basic_info (15 字段) + listing_info (8 字段)
  - GBK 原始字节保留，避免编码损耗
  - ⚠️ 因数据合规考虑，未包含在 pip 包中，需从源码编译启用
- **模块分层** — `tdxrs` (核心) + `tdxrs.pro` (扩展)
- **共享工具** — `net/utils.rs` 新增 `auto_market`, `encode_gbk`, `encode_gbk_padded`
- **性能测试** — `tests/bench_etf_f10.py`

### 变更
- `profile/constants.rs` 移除重复的 `MARKET_SZ`/`MARKET_SH` (复用 `protocol::constants`)
- `etf/constants.rs` 移除重复常量，`is_sh_etf`/`is_sz_etf` 改为私有
- `etf/utils.rs` 移除死代码 (未使用的 `EtfError` 变体和工具函数)
- `profile/parser_f10.rs` 移除调试输出 (`eprintln!`)、`F10Parsed.raw` 字段、重复键
- `profile/types.rs` `F10Category` 新增 `filename_raw` 字段

### 文档
- 新增 [ETF 模块文档](ETF.md)
- 新增 [F10 模块文档](F10.md)
- 更新 README: 新增 PyPI/Stars 徽章、Star History、扩展模块介绍

---

## v0.5.0 (2026-05-13) — 首次 PyPI 发布

### 新增
- **TdxFinanceClient** — 独立财务客户端，分片下载 + 磁盘缓存 (24h TTL)
- **命名财务指标** — `get_finance_indicators()` 从 gpcw 提取 45 个核心指标（英文 key，原始值）
- **财务字段映射** — `src/protocol/finance_fields.rs`
- **轻量日志** — `logd!/logi!/logw!/loge!` 宏，`TDXRS_LOG` 环境变量控制级别
- **Net/Utils** — 提取三客户端共享逻辑，消除 ~360 行重复代码
- **连接池磁盘缓存** — TdxFinanceClient 24h 本地缓存 gpcw 文件
- **CI/CD** — GitHub Actions 多平台构建 (Linux/macOS/Windows) → PyPI 自动发布
- **文档** — 12 篇维护文档 + 3 个 demo 程序

### 变更
- `client.rs` / `direct_client.rs` / `async_client.rs` 精简去重
- `perform_handshake` 移至 `utils.rs`

### 修复
- **财务单位** — `get_finance_info` 移除所有 `×10000` 自动转换，返回 TDX 原始值
- **指数 K 线 fq** — 客户端强制 `fq=0`，不再透传用户值到服务端
- **自动分页排序** — `get_xxx_all` 改为 prepend，修复跨页乱序
- **quotes 边界检查** — `parse_security_quotes` 增加 `pos + 30` 保护
- 测试断言更新 (93 passed)

---

## v0.4.0 (2026-05-05)

### 新增
- **TdxDirectClient** Python 绑定 — 裸连接客户端 (无池/无重试)
- **DataFrame 输出** — Reader 和 Client 均支持 `to_dataframe()` / `*_dataframe()` 方法
- **协议常量子模块** (`tdxrs.constants`) — 市场代码、K线种类、复权类型等 26 个常量
- **复权参数** — K线 API 新增 `fq` 参数 (0=未复权, 1=前复权, 2=后复权)
- **context_bars 支持** — 除权日在 K 线范围之外时自动拉取历史数据补全因子计算
- 服务器列表扩展至 18 台 (优先组) + 101 台 (完整列表)
- 连接池服务管理 API: `set_servers` / `add_server` / `probe_servers` / `reorder_servers`
- 连接池大小默认提升至 5

### 变更
- pyo3 0.23 → 0.28 API 迁移
- Python 返回类型统一为 `list[dict]`
- 异步模块 (tokio) 启用编译
- 复权算法增加 context_bars 参数 (`adjust_security_bars` 签名变更)

### 修复
- Windows GNU 工具链 dlltool 编译支持
- `#[pymodule]` 命名与 maturin 配置对齐
- 早期除权事件 (早于 K 线数据范围) 静默丢弃

---

## v0.3.0 (2026-05-02)

### 新增
- 连接池 (`ConnectionPool` + RAII guard)
- 内置心跳线程 (10s keepalive)
- 断线自动重连 + 智能重试 (0.1~2.0s)
- 数据缓存 (security_count / security_list, TTL 30s)
- K线自动分页 (`get_security_bars_all` / `get_index_bars_all`)
- Tuple 高性能模式 (3 个 `*_tuples` 方法)

---

## v0.2.0 (2026-05-01)

### 新增
- 网络协议客户端: TCP 连接 + 13 个 API + 11 个响应解析器
- Python 绑定 (`PyTdxHqClient`)

---

## v0.1.0 (2026-05-01)

### 新增
- 本地文件解析: 日线 / 分钟线 / 板块 / 财务 (4 个 Reader)
- Python 绑定 (5 个 Reader 类)
- 单元测试 + 性能基准
