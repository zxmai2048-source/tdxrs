# 变更日志

## v0.5.1 (2026-05-12)

### 修复
- **财务单位修正** — `get_finance_info` 移除所有 `×10000` 自动转换，返回 TDX 原始值。不同字段单位可能不同（万元/千元/元/户），由用户自行判断。旧版本值被错误放大了 10000 倍。

### 新增
- **命名财务指标** — `TdxFinanceClient.get_finance_indicators()` 从 gpcw 数据中提取 45 个核心指标（英文 key，原始值）
- **财务字段映射模块** — `src/protocol/finance_fields.rs`，含 gpcw 索引→(英文名, 中文名) 映射
- **财务演示程序** — `examples/demo_finance.py`，覆盖实时/批量/DataFrame/本地 gpcw/gpcw 下载

### 变更
- `API_REFERENCE.md` 财务部分标注原始值及典型数量级
- `parse_finance_info` 测试断言更新 (100000.0 → 10.0)

---

## v0.5.0 (2026-05-11)

### 新增
- **TdxFinanceClient** — 独立财务客户端，大文件分片下载、gpcw 数据解析
- **轻量日志模块** — `logd!/logi!/logw!/loge!` 宏，`TDXRS_LOG` 环境变量控制级别
- **Net/Utils 公共模块** — 提取三客户端共享逻辑，消除 ~200+ 行重复代码

### 变更
- `client.rs` 精简 ~140 行，移除重复工具方法
- `direct_client.rs` 精简 ~140 行
- `async_client.rs` 精简 ~80 行
- `perform_handshake` 从 `client.rs` 移至 `utils.rs` (API 兼容，内部重构)

### 修复
- 财务 `parse_finance_info` 实现，34 字段解析 (v0.5.1 已修正单位)

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
