# 贡献指南

感谢你对 tdxrs 的关注！欢迎提交 Issue、PR 或参与讨论。

---

## 报告问题

在提交 Issue 之前：
- 确认使用最新版本 (`pip show tdxrs`)
- 描述完整的错误信息、Python 版本、操作系统、Rust 版本
- 网络相关问题提供服务器 IP/端口、请求参数
- 提供最小可复现示例

### 数据准确性反馈

数据准确性是 tdxrs 的核心关注点，但由于 TDX 协议的复杂性和逆向工程的局限性，**部分数据的准确性无法完全保证**。

如果你在使用过程中发现以下问题，请及时反馈：
- 价格解析错误（如涨跌幅异常、价格精度问题）
- 成交量/成交额计算偏差
- 时间映射错误（分时数据时间点不对应）
- 复权计算结果与交易软件不一致
- 逐笔成交数据异常

**反馈格式建议**：
```
问题描述: 简要说明发现的问题
股票代码: 600519
数据类型: 分时/逐笔/K线/行情
预期结果: 交易软件显示的数据
实际结果: tdxrs 返回的数据
复现代码: 最小可复现的代码片段
```

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

环境要求: Rust 1.83+, Python 3.11+。
Windows `x86_64-pc-windows-gnu` 需要安装 MSYS2 dlltool (详见 [INSTALL.md](../INSTALL.md))。

---

## 项目结构

```
src/
├── reader/        # 本地文件解析器 (日线/分钟线/板块/财务)
├── protocol/      # TDX 协议 (parsers/adjuster/types/constants)
├── net/           # 网络客户端 (client/direct_client/async_client)
├── fund/          # 基金模块 (ETF/LOF/REITs)
├── block/         # 板块查询模块
├── profile/       # F10 扩展模块
├── python/        # PyO3 Python 绑定
├── error_codes.rs # 统一错误码体系
├── constants.rs   # 日期/字节解码工具
├── helpers.rs     # TDX 协议辅助 (变长整数)
├── error.rs       # 错误类型
└── lib.rs         # PyO3 模块入口

python/tdxrs/
├── __init__.py    # 入口 (TdxHqClient, Reader 等)
├── constants.py   # 常量子模块
├── downloader.py  # 批量下载器 (多服务器轮转/增量更新)
├── cli.py         # CLI 命令行工具
├── cli_format.py  # CLI 输出格式化 (table/json/csv)
└── __main__.py    # python -m tdxrs 入口
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
| 数据准确性验证 | 建立系统化的数据验证框架，对比主流交易软件数据 | 3-5 天 |

### P2 — 中优先级

| 事项 | 说明 | 预估 |
|------|------|------|
| 磁盘缓存 (K 线) | 历史 K 线 / 证券列表本地缓存，减少重复网络请求 (财务数据缓存已实现) | 2 天 |
| 异步 Python async/await | 当前 `PyAsyncTdxHqClient` 通过 `block_on()` 同步调用，暴露原生 `async/await` API | 1-2 天 |
| 北交所支持 | 完善 market=2 (BJ) 的证券类型识别 | 1 天 |

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
