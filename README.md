# tdxrs — 通达信行情数据解析库 (Rust + Python)

[![Rust](https://img.shields.io/badge/Rust-1.83%2B-orange)](https://www.rust-lang.org/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/tdxrs?color=blue&label=PyPI)](https://pypi.org/project/tdxrs/)
[![PyPI downloads](https://img.shields.io/pypi/dm/tdxrs?color=blue&label=Downloads)](https://pypi.org/project/tdxrs/)
[![GitHub stars](https://img.shields.io/github/stars/jiangtaovan/tdxrs?color=yellow&label=Stars)](https://github.com/jiangtaovan/tdxrs)
[![GitHub forks](https://img.shields.io/github/forks/jiangtaovan/tdxrs?label=Forks)](https://github.com/jiangtaovan/tdxrs)
[![GitHub last commit](https://img.shields.io/github/last-commit/jiangtaovan/tdxrs?label=Updated)](https://github.com/jiangtaovan/tdxrs/commits)

**tdxrs** 是通达信 (TDX) 行情数据解析库的 Rust 高性能实现。通过 PyO3/maturin 提供 Python 调用接口，保持与 Python [tdxpy](https://github.com/rainx/tdxpy) 的 API 兼容，本地解析性能提升 **9-11 倍**。

```python
from tdxrs import TdxHqClient
from tdxrs.constants import MARKET_SH, KLINE_DAILY, FQ_QFQ

client = TdxHqClient()
client.connect_to_any()

# 贵州茅台日K → DataFrame
df = client.get_security_bars_dataframe(KLINE_DAILY, MARKET_SH, "600519", 0, 500)
df["ma20"] = df["close"].rolling(20).mean()

# 批量实时行情
quotes = client.get_security_quotes([
    (MARKET_SH, "600519"), (0, "000858"), (0, "300750")
])
```

---

## 性能

| 场景 | tdxrs (Rust) | tdxpy (Python) | 提升 |
|------|------------:|--------------:|:---:|
| 日线解析 1000 条 | 0.3ms | 2.8ms | **9×** |
| 分钟线解析 1000 条 | 0.5ms | 5.1ms | **10×** |
| 板块解析 500 条 | 1.2ms | 12.0ms | **10×** |
| 网络 K 线 100 条 | 73ms | 110ms | **1.5×** |
| 网络行情 3 只 | 75ms | 95ms | **1.3×** |
| 60 线程并发 K 线 | **344ms** | — | 零退化 |

> 吞吐量 ~260 万条/秒。全市场 5000 只股票日线解析约 2 秒。详见 [性能基准](docs/public/BENCHMARKS.md)。

---

## 功能

### 网络行情 (13 类数据)

| 数据 | 覆盖 |
|------|------|
| **K 线** | 个股 + 指数，12 种周期 (1分钟 ~ 年线) |
| **实时行情** | 五档盘口，含成交额/总量 |
| **分时数据** | 当日 + 历史 |
| **逐笔成交** | 当日 + 历史，含买卖方向 |
| **证券信息** | 全市场列表 + 数量 (带缓存) |
| **财务数据** | 实时 34 项 + 45 个英文命名财务指标 |
| **除权除息** | 分红/送股/配股/缩股历史 |
| **板块数据** | 行业/概念/地域分类 |

### 扩展模块 (`tdxrs.pro`)

| 模块 | 类 | 说明 | 获取方式 |
|------|-----|------|----------|
| **ETF** | `TdxHqEtfClient` | ETF 专用行情 (K线/行情/分时/逐笔/除权/财务) | `pip install tdxrs` |
| **F10** | `TdxF10Client` | F10 公司资料 (16 分类, 内置文本解析器) | 源码编译 (`--features f10`) |

```python
from tdxrs.pro import TdxHqEtfClient
from tdxrs.constants import MARKET_SH

# ETF 行情
etf = TdxHqEtfClient()
etf.connect_to_any()
bars = etf.get_etf_bars(4, MARKET_SH, "510300", 0, 100)
```

### 客户端侧复权计算

TDX 服务端返回未复权原始数据。tdxrs 在客户端自行计算前复权/后复权：
- 中国 A 股标准除权除息公式：`P_ex = (P_close - D + P_rights × R_rights) / (1 + R_bonus + R_rights)`
- 支持分红+送股+配股联动
- 自动补全早期除权事件 (context_bars 机制)
- `fq=0` 路径零额外开销

### 四种客户端方案

| 客户端 | 策略 | 场景 |
|-------|------|------|
| `TdxHqClient` | 连接池(5) + 心跳 + 重试 + 缓存 | 主力，顺序请求 |
| `TdxDirectClient` | 每请求独立 TCP | 高并发 (60线程零退化) |
| `TdxFinanceClient` | 独立超时(15s) + 磁盘缓存 | gpcw 大文件下载 |
| `AsyncTdxHqClient` | tokio 异步 | 异步生态集成 |

### 本地文件解析

| 格式 | Reader | 输出 |
|------|--------|------|
| `.day` 日线 | `DailyBarReader` | dict / tuple / DataFrame |
| `.lc5` `.lc1` 分钟线 | `MinBarReader` `LcMinBarReader` | 同上 |
| `.dat` 板块 | `BlockReader` | flat / group 两种模式 |
| `gpcw*.dat` 财务 | `FinancialReader` | f32 字段数组 |

---

## 安装

```bash
pip install tdxrs
```

或从源码构建：

```bash
git clone https://github.com/jiangtaovan/tdxrs && cd tdxrs
pip install maturin
maturin develop --release
```

Windows `x86_64-pc-windows-gnu` 需额外安装 [MSYS2 dlltool](docs/INSTALL.md)。详见 [安装说明](docs/INSTALL.md)。

---

## 快速示例

### K 线 — 完整复权演示

```python
from tdxrs import TdxHqClient
from tdxrs.constants import MARKET_SH, MARKET_SZ, KLINE_DAILY, KLINE_WEEKLY, FQ_QFQ, FQ_HFQ, FQ_NONE

client = TdxHqClient()
client.connect_to_any()

# 前复权 (默认)
bars = client.get_security_bars(KLINE_DAILY, MARKET_SH, "600519", 0, 100)

# 未复权原始数据
raw = client.get_security_bars(KLINE_DAILY, MARKET_SH, "600519", 0, 100, fq=FQ_NONE)

# 后复权
hfq = client.get_security_bars(KLINE_DAILY, MARKET_SH, "600519", 0, 100, fq=FQ_HFQ)

# 周K + 自动分页 (3000条)
all_bars = client.get_security_bars_all(KLINE_WEEKLY, MARKET_SH, "600519", count=3000)

# Tuple 高性能模式 (快 40-60%)
tuples = client.get_security_bars_tuples(KLINE_DAILY, MARKET_SH, "600519", 0, 500)
# → (open, close, high, low, vol, amount, year, month, day, hour, minute, datetime)

client.disconnect()
```

### 多股票批量财务

```python
# 实时财务 (TDX 原始值, 不自动转换单位)
info = client.get_finance_info(market=1, code="600519")
# 经验规则: 股本类 ≈万元, 资产类 ≈万元, 每股指标 ≈元
print(f"净资产: {info['jingzichan']:.0f}")   # e.g. 270894048 → 2709亿元
print(f"每股净资产: {info['meigujingzichan']:.2f}")  # 216.32元

# 多股票对比 DataFrame
df = client.get_finance_info_dataframe([
    (MARKET_SH, "600519"), (MARKET_SZ, "000858"), (MARKET_SZ, "300750")
])
print(df[["code", "jingzichan", "jinglirun", "meigujingzichan"]])
```

### 本地文件解析

```python
from tdxrs import DailyBarReader

reader = DailyBarReader(coefficient=0.01)
df = reader.to_dataframe(open("600519.day", "rb").read())
# df.columns: date, open, high, low, close, amount, volume, year, month, day
```

---

## 工程亮点

```
语言:    Rust 2021 edition, 0 行 unsafe
测试:    128 个单元/集成测试
依赖:    6 个核心 crate (pyo3, flate2, tokio, serde, thiserror, encoding_rs)
文档:    12 篇维护文档 (6 public + 6 internal)
```

---

## 架构

```
Python API ─── dict / tuple / DataFrame
    │
Net 层 ─── Pool / Direct / Finance / Async / F10 五个客户端
    │         └── utils.rs 公共工具 (packet / handshake / decompress / auto_market)
    │
Protocol 层 ─── 13 个解析器 + 复权算法 + gpcw 字段映射
    │
Reader 层 ─── 日线 / 分钟线 / 板块 / 财务
    │
Profile 层 ─── F10 文本解析器 + 结构化提取
    │
ETF 层 ─── ETF 代码验证 + 客户端封装
    │
基础设施 ─── error / logging / helpers / constants
```

详见 [架构说明](docs/public/ARCHITECTURE.md) 和 [代码引用](docs/CODE_REFERENCE.md)。

---

## 文档

| 文档 | 说明 |
|------|------|
| [API 参考](docs/public/API_REFERENCE.md) | 完整 Python API + 最佳实践 |
| [架构说明](docs/public/ARCHITECTURE.md) | 模块设计、数据流、客户端策略 |
| [性能基准](docs/public/BENCHMARKS.md) | 顺序/并发性能 + 场景选择指南 |
| [ETF 模块](docs/public/ETF.md) | ETF 数据获取与解析 |
| [F10 模块](docs/public/F10.md) | F10 公司资料 (源码编译, `--features f10`) |
| [复权算法](docs/ADJUSTER_ALGORITHM.md) | 公式推导、版本迭代、验证方法 |
| [变更日志](docs/public/CHANGELOG.md) | 版本历史 |
| [贡献指南](docs/public/CONTRIBUTING.md) | 参与开发 + 可贡献方向 |
| [安装说明](docs/INSTALL.md) | 环境配置 + FAQ |

---

## 要求

- **Rust** 1.83+ | **Python** 3.8+ | **maturin** 1.5+
- pandas (可选, DataFrame 输出)

---

## 免责声明

- 本项目仅供**学习和研究**用途，不构成任何投资建议
- 本项目不保证数据的准确性、完整性和时效性
- 通达信行情数据的版权归相关数据提供商所有
- F10 公司资料模块涉及第三方数据内容，**未包含在 pip 包中**，需从源码编译启用
- 用户使用本项目获取的数据用于商业用途时，需自行解决数据授权合规问题
- 本项目按 [MIT License](LICENSE) 发布，作者不对因使用本项目产生的任何损失承担责任

---

## 许可证

MIT License — 详见 [LICENSE](LICENSE)

---

## Star History

<a href="https://www.star-history.com/?repos=jiangtaovan%2Ftdxrs&type=Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=jiangtaovan/tdxrs&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=jiangtaovan/tdxrs&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=jiangtaovan/tdxrs&type=Date" />
 </picture>
</a>
