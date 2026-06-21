# 贡献指南

感谢你对 tdxrs 的关注！欢迎提交 Issue、PR 或参与讨论。

---

## 报告问题

在提交 Issue 之前：
- 确认使用最新版本 (`pip show tdxrs`)
- 描述完整的错误信息、Python 版本、操作系统、Rust 版本
- 网络相关问题提供服务器 IP/端口、请求参数
- 提供最小可复现示例

---

## 开发环境

```bash
git clone <repo-url> && cd tdxrs

# 安装 maturin
pip install maturin

# 开发构建 (编辑模式，代码改动自动生效)
maturin develop --release

# 仅编译检查
cargo check

# 运行 Rust 单元测试
cargo test --lib

# Python 集成验证
python tests/compare_tdxpy_tdxrs.py --mode reader
```

环境要求: Rust 1.83+, Python 3.8+。
Windows `x86_64-pc-windows-gnu` 需要安装 MSYS2 dlltool (详见 [INSTALL.md](../INSTALL.md))。

---

## 项目结构

```
src/
├── reader/        # 本地文件解析器 (日线/分钟线/板块/财务)
│   └── financial.rs   # gpcw 格式 + 命名字段
├── protocol/      # TDX 协议
│   ├── parsers.rs     # 11 个响应解析器
│   ├── adjuster.rs    # 复权调整算法
│   ├── types.rs       # 数据结构定义
│   ├── constants.rs   # 协议常量 (命令码/市场代码等)
│   └── finance_fields.rs # gpcw 字段映射
├── net/           # 网络客户端
│   ├── client.rs         # TdxHqClient (连接池+心跳+重试)
│   ├── direct_client.rs  # TdxDirectClient (裸连接)
│   ├── finance_client.rs # TdxFinanceClient (独立财务)
│   ├── f10_client.rs     # TdxF10Client (独立连接)
│   ├── async_client.rs   # AsyncTdxHqClient (tokio)
│   ├── utils.rs          # 公共工具 (握手/解压/auto_market/encode_gbk)
│   ├── pool.rs           # 连接池
│   ├── connection.rs     # 同步 TCP
│   ├── async_connection.rs # 异步 TCP
│   └── packet.rs         # 响应头解析
├── etf/           # ETF 扩展模块
│   ├── client.rs         # TdxHqEtfClient (封装 TdxHqClient)
│   ├── constants.rs      # ETF 常量 (代码前缀, 复用 protocol 市场代码)
│   ├── types.rs          # ETF 数据类型
│   └── utils.rs          # ETF 代码验证
├── profile/       # F10 扩展模块 (需 --features f10)
│   ├── client.rs         # ProfileClient (共享连接池变体)
│   ├── constants.rs      # 协议常量、分类名称
│   ├── types.rs          # F10 数据类型
│   ├── parser.rs         # 二进制响应解析器
│   └── parser_f10.rs     # F10 文本解析器 (结构化提取)
├── python/        # PyO3 Python 绑定
│   ├── py_client.rs      # TdxHqClient 绑定
│   ├── py_direct_client.rs # TdxDirectClient 绑定
│   ├── py_reader.rs      # Reader 绑定
│   ├── py_etf.rs         # TdxHqEtfClient 绑定
│   ├── py_profile.rs     # TdxF10Client 绑定
│   ├── py_dataframe.rs   # DataFrame 构建
│   └── py_constants.rs   # 常量注册
├── logging.rs     # 轻量日志 (TDXRS_LOG 控制)
├── helpers.rs     # TDX 协议辅助 (变长整数)
├── constants.rs   # 日期/字节解码工具
├── error.rs       # 错误类型
└── lib.rs         # PyO3 模块入口
```

---

## 代码约定

- **Rust**: `cargo fmt` + `cargo clippy`。避免使用 `unwrap()` 在可能失败的地方，优先 `?`。
- **日志**: 关键模块使用 `logd!/logi!/logw!/loge!` 宏 (`use crate::logd;`)。环境变量 `TDXRS_LOG=debug` 启用详细输出。
- **测试**: 新功能必须包含 Rust 单元测试 (`#[cfg(test)] mod tests`)。
- **提交信息**: `type: description` 格式 (如 `feat: add DataFrame output`, `fix: adjuster context_bars`)。

---

## 新增功能流程

### 新增 Reader
1. 在 `src/reader/` 创建解析模块
2. 实现 `parse_xxx(data: &[u8]) -> Result<Vec<Record>>`
3. 注册到 `src/reader/mod.rs`
4. 在 `src/python/py_reader.rs` 添加 Python 绑定
5. 在 `src/lib.rs` 注册类
6. 添加单元测试

### 新增客户端 API
1. 在 `src/net/client.rs` 添加方法
2. 同步到 `src/net/direct_client.rs` 和 `src/net/async_client.rs`
3. 如需公共逻辑，提取到 `src/net/utils.rs`
4. 在 `src/python/py_client.rs` 添加 Python 绑定
5. 添加测试

### 新增解析器
1. 在 `src/protocol/parsers.rs` 添加 `pub fn parse_xxx()`
2. 在 `src/protocol/types.rs` 定义数据结构
3. 添加边界条件测试

---

## 测试验证

```bash
# Rust 单元测试
cargo test --lib

# 预存已知失败 (与构建环境无关):
#   test_get_volume_zero      — 浮点精度差异
#   test_parse_lc_min_bar     — 浮点精度差异

# Python 对比验证 (需要 tdxpy 参考)
python tests/compare_tdxpy_tdxrs.py --mode reader
python tests/compare_tdxpy_tdxrs.py --mode network
```

---

## 发布流程

1. 更新 `docs/public/CHANGELOG.md`
2. 更新版本号 (`Cargo.toml`, `pyproject.toml`)
3. `maturin build --release`
4. 上传 wheel 到 PyPI

---

## 可贡献方向

按优先级排列的待实现功能，欢迎贡献：

### P1 — 高优先级

| 事项 | 说明 | 预估 |
|------|------|------|
| 异步连接池 | `AsyncTdxHqClient` 当前单连接，高并发退化严重。需 tokio 异步连接池，性能对标 `TdxDirectClient` | 2-3 天 |
| 连接池优化 | 减少 `borrow()` 持锁时间：新建连接时先释放锁再做 I/O，或使用无锁结构 | 1 天 |
| CI/CD | GitHub Actions: `cargo check` + `cargo test` + `maturin build` + wheel 发布 | 1 天 |
| 多平台 wheel | Linux (manylinux) / macOS / Windows wheel 自动构建 | 1 天 |

### P2 — 中优先级

| 事项 | 说明 | 预估 |
|------|------|------|
| 磁盘缓存 | 历史 K 线 / 证券列表本地缓存，减少重复网络请求 | 2 天 |
| 异步 Python 绑定 | `pyo3-asyncio` 暴露为 Python `async/await` API | 1-2 天 |
| Data export | CSV / Parquet 导出，支持 pandas 直读 | 1-2 天 |

### P3 — 低优先级

| 事项 | 说明 |
|------|------|
| 技术指标 | MA / MACD / RSI / KDJ / BOLL |
| 零拷贝解析 | 直接在原始字节上构建视图，避免中间 Vec 分配 |
| SIMD 加速 | 价格差分解码并行处理 |
| WebSocket 推送 | 代理 TDX TCP，提供 WebSocket 接口 |
| 多市场扩展 | 期货 / 港股 / 美股 |
| Fuzzing | 解析器模糊测试 |

### 技术债

| 事项 | 说明 |
|------|------|
| `parse_block_info_meta` hash 校验 | 当前仅读取元数据，未校验完整性 |
| `test_get_volume_zero` | 浮点精度 `5.877e-39` ≠ `0.0` |
| `test_parse_lc_min_bar` | 浮点精度 `high` ≠ `10.80` |
| `test_min_bar_600519` | 测试数据日期需更新 |

---

## 许可证

MIT License — 详见 [LICENSE](../../LICENSE)
