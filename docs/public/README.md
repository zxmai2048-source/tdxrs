# tdxrs — 通达信行情数据解析库

[![Rust](https://img.shields.io/badge/Rust-1.83%2B-orange)](https://www.rust-lang.org/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![pyo3](https://img.shields.io/badge/pyo3-0.28-green)](https://pyo3.rs/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen)](../../LICENSE)

**tdxrs** 是通达信 (TDX) 行情数据解析库的 Rust 实现。通过 PyO3/maturin 提供 Python 调用接口，保持与 Python [tdxpy](https://github.com/rainx/tdxpy) 项目的功能兼容，利用 Rust 的内存安全和零成本抽象特性显著提升解析性能。

---

## 核心特性

### 本地文件解析
日线 (.day)、分钟线 (.lc5)、板块 (.dat)、财务 (gpcw*.dat) 二进制文件 → Python dict / tuple / DataFrame

### 网络行情客户端 (13 类数据)
| 数据类别 | 说明 |
|---------|------|
| K 线 | 个股 / 指数，支持 1min/5min/15min/30min/60min/日/周/月/季/年 |
| 实时行情 | 五档买卖盘口，含成交额、总量、现量 |
| 分时数据 | 当日 + 历史 |
| 逐笔成交 | 当日 + 历史，含买卖方向 |
| 证券信息 | 列表、数量 (含缓存) |
| 财务数据 | 实时 34 项 + 45 个英文命名指标 |
| 除权除息 | 分红 / 送股 / 配股 / 缩股历史 |
| 板块数据 | 行业/概念/地域分类 |

### 五种客户端方案
| 客户端 | 策略 | 场景 |
|-------|------|------|
| `TdxHqClient` | 连接池 (默认 5) + 心跳 + 重试 + 缓存 | 主力，顺序请求 |
| `TdxDirectClient` | 每次独立 TCP 连接 | 偶发请求、高并发 |
| `TdxFinanceClient` | 独立连接 + 超长超时 (15s) + 分片下载 | 大文件 gpcw 数据 |
| `AsyncTdxHqClient` | tokio 异步 + Channel 连接池 | 异步生态集成 |
| `TdxHqFundClient` | 基金专用 (净值/行情/申赎清单) | ETF/LOF/REITs |
| `TdxBlockClient` | 板块专用 (列表/成分股) | 概念/行业/地域板块 |

### 复权处理
客户端侧前复权/后复权，支持分红+送股+配股联动，自动补全早期除权事件上下文。详见 [复权算法](../ADJUSTER_ALGORITHM.md)。

### Python 生态
- 返回 `list[dict]` / `list[tuple]` / `pd.DataFrame` 三种格式
- `tdxrs.constants` 子模块暴露 26 个常用常量
- 协议常量与 Python tdxpy 对齐

---

## 快速开始

### 安装

```bash
pip install maturin
git clone <repo-url> && cd tdxrs
maturin develop --release
```

详细安装见 [INSTALL.md](../INSTALL.md)。

### CLI 命令行

无需编写代码，直接查询行情：

```bash
tdxrs quote 600519              # 实时行情
tdxrs bars 600519 --count 30    # K线数据
tdxrs trades 600519             # 逐笔成交
tdxrs servers                   # 测试服务器连通性
tdxrs download --market sh      # 批量下载
```

详见 [CLI 使用指南](CLI.md)。

### 网络行情

```python
from tdxrs import TdxHqClient
from tdxrs.constants import MARKET_SH, KLINE_DAILY, FQ_QFQ

client = TdxHqClient()
client.connect_to_any()

# 贵州茅台前复权日K线
bars = client.get_security_bars(KLINE_DAILY, MARKET_SH, "600519", 0, 100)

# 直出 DataFrame
df = client.get_security_bars_dataframe(KLINE_DAILY, MARKET_SH, "600519", 0, 500)

# 多股票实时行情
quotes = client.get_security_quotes([
    (MARKET_SH, "600519"), (0, "000858"), (0, "300750")
])

client.disconnect()
```

### 本地文件

```python
from tdxrs import DailyBarReader

reader = DailyBarReader(coefficient=0.01)
df = reader.to_dataframe(open("600519.day", "rb").read())
```

---

## 架构概览

```
tdxrs/
├── src/reader/         # 本地二进制文件解析 (日线/分钟线/板块/财务)
├── src/protocol/       # TDX 协议编解码 + 复权算法
├── src/net/            # TCP 连接管理 (5 种客户端 + 公共工具)
├── src/fund/           # 基金数据 (净值/行情/申赎清单)
├── src/block/          # 板块数据 (列表/成分股)
├── src/profile/        # F10 公司资料
├── src/python/         # PyO3 绑定 (Reader / Client / DataFrame / Constants)
├── src/logging.rs      # 轻量日志 (TDXRS_LOG 环境变量控制)
├── src/error_codes.rs  # 错误码定义
├── docs/               # 项目文档
├── tests/              # 测试脚本 + 二进制测试数据
├── examples/           # 示例代码
├── python/tdxrs/       # Python 包入口 + CLI
└── benches/            # Benchmark
```

---

## 环境要求

- **Rust** 1.83+
- **Python** 3.11+
- **maturin** (`pip install maturin`)
- Windows `x86_64-pc-windows-gnu` 额外需要 `dlltool.exe`（详见 [INSTALL.md](../INSTALL.md)）

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [API 参考](API_REFERENCE.md) | 完整 Python API 签名与参数说明 |
| [CLI 使用指南](CLI.md) | 命令行工具用法 (quote/bars/trades/download) |
| [基金模块](FUND.md) | ETF/LOF/REITs 数据接口 |
| [F10 公司资料](F10.md) | 公司基本面数据 (需源码编译) |
| [架构说明](ARCHITECTURE.md) | 模块设计、数据流、客户端策略 |
| [性能基准](BENCHMARKS.md) | 顺序/并发性能 + 方案选择指南 |
| [复权算法](../ADJUSTER_ALGORITHM.md) | 公式推导、版本迭代、验证方法 |
| [变更日志](CHANGELOG.md) | 版本历史 |
| [贡献指南](CONTRIBUTING.md) | 参与开发 |

---

## 许可证

MIT License — 详见 [LICENSE](../../LICENSE)
