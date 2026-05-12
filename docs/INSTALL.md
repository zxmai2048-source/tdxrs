# tdxrs 安装和使用说明

> 版本: v0.5.1 | 更新: 2026-05-12

## 环境要求

| 组件 | 最低版本 | 说明 |
|------|----------|------|
| Python | 3.8+ | 运行 Python 绑定 |
| Rust | 1.83+ | 从源码构建时需要 (pyo3 0.28 要求) |
| maturin | 1.5+ | 构建 Python 扩展模块 |

## 安装

### 方式一: pip 安装 (推荐)

```bash
pip install tdxrs
```

### 方式二: 从源码构建

```bash
git clone <repo-url>
cd tdxrs

# 安装 maturin
pip install maturin

# 开发构建 (安装到当前 Python 环境)
maturin develop --release

# 发布构建 (生成 wheel)
maturin build --release
```

> Windows `x86_64-pc-windows-gnu` 工具链需额外安装 MSYS2 dlltool (详见下文 FAQ)。

### 方式三: 仅使用 Rust 库

```toml
[dependencies]
tdxrs = { path = "path/to/tdxrs" }
```

### 验证安装

```python
import tdxrs
print(tdxrs.__version__)  # 0.5.1
```

---

## 功能概览

- **本地文件解析** — 日线 (.day) / 分钟线 (.lc5/.lc1) / 板块 (.dat) / 财务 (gpcw*.dat)
- **网络行情客户端** — 4 种客户端方案覆盖不同场景
- **复权计算** — 客户端侧前复权/后复权，支持分红+送股+配股联动

---

## 本地文件解析

### 日线数据 (DailyBarReader)

```python
from tdxrs import DailyBarReader

reader = DailyBarReader(coefficient=0.01)

# 从文件读取
bars = reader.parse_file("C:/tdx/v600/day/600519.day")
for bar in bars[:3]:
    print(f"{bar['date']}: O={bar['open']:.2f} C={bar['close']:.2f}")

# 从 bytes 解析
with open("600519.day", "rb") as f:
    bars = reader.parse_data(f.read())

# Tuple 模式 (高性能)
tuples = reader.parse_data_tuples(data)
# → (date, open, high, low, close, amount, volume, year, month, day)

# DataFrame 模式
df = reader.to_dataframe(open("600519.day", "rb").read())
```

**coefficient 参数:**

| 品种 | coefficient |
|------|:--:|
| A 股 | 0.01 |
| B 股 | 0.001 |
| 指数 | 0.01 |
| 基金 | 0.001 |
| 债券 | 0.0001 |

### 分钟线数据 (MinBarReader / LcMinBarReader)

```python
from tdxrs import MinBarReader, LcMinBarReader

# 整数格式 (.lc5 / .lc1)
reader = MinBarReader()
bars = reader.parse_file("600519.lc5")

# 浮点格式 (LC 数据)
reader = LcMinBarReader()
bars = reader.parse_file("600519.lc1")
```

### 板块数据 (BlockReader)

```python
from tdxrs import BlockReader

reader = BlockReader()

# 扁平模式: 每只股票一行
records = reader.parse_file("blocknew.dat")

# 分组模式: 每个板块一行
groups = reader.parse_data_group(open("blocknew.dat", "rb").read())
```

### 财务数据 (FinancialReader)

```python
from tdxrs import FinancialReader

reader = FinancialReader()
records = reader.parse_file("gpcw20260331.dat")
for r in records[:3]:
    print(f"{r['code']}: report_date={r['report_date']}, {len(r['fields'])} fields")
# → f32 财务指标数组 (部分字段含未验证数据)
```

---

## 网络行情客户端

### 基本连接

```python
from tdxrs import TdxHqClient

client = TdxHqClient()

# 推荐: 自动选择可用服务器
client.connect_to_any(timeout=5.0)

# 或指定服务器
client.connect("119.147.212.81", 7709, timeout=5.0)

# 检查连接状态
print(client.is_connected())  # True
```

### K 线数据 (核心)

```python
from tdxrs.constants import (
    MARKET_SH, MARKET_SZ,           # 市场: 1=上海, 0=深圳, 2=北京
    KLINE_DAILY, KLINE_WEEKLY,      # K线种类
    FQ_QFQ, FQ_HFQ, FQ_NONE,        # 复权: 1=前复权, 2=后复权, 0=未复权
)

# 个股日K — 前复权 (默认)
bars = client.get_security_bars(KLINE_DAILY, MARKET_SH, "600519", 0, 100)
# fq 参数可省略，默认=1 (前复权)

# 个股日K — 未复权
bars = client.get_security_bars(KLINE_DAILY, MARKET_SH, "600519", 0, 100, fq=0)

# 个股日K — 后复权
bars = client.get_security_bars(KLINE_DAILY, MARKET_SH, "600519", 0, 100, fq=2)

# 自动分页 (count > 800)
bars = client.get_security_bars_all(KLINE_DAILY, MARKET_SH, "600519", count=3000)

# 指数K线 (fq 被忽略, 指数不复权)
bars = client.get_index_bars(KLINE_DAILY, MARKET_SH, "000001", 0, 100)
for b in bars[:3]:
    print(f"{b['datetime']}: O={b['open']:.2f} ↑{b['up_count']} ↓{b['down_count']}")

# DataFrame 直出
df = client.get_security_bars_dataframe(KLINE_DAILY, MARKET_SH, "600519", 0, 500)

# Tuple 高性能模式
tuples = client.get_security_bars_tuples(KLINE_DAILY, MARKET_SH, "600519", 0, 100)
# → (open, close, high, low, vol, amount, year, month, day, hour, minute, datetime)
```

### 复权类型 (fq)

| 值 | 常量 | 说明 |
|:--:|------|------|
| 0 | `FQ_NONE` | 未复权 — 交易所原始价格。仅 `category=4` (KLINE_DAILY) 支持。 |
| 1 | `FQ_QFQ` | **前复权** (默认) — 历史价格按后续除权因子向下调整，现价不变。 |
| 2 | `FQ_HFQ` | 后复权 — 近期价格按历史除权因子向上调整，首日价不变。 |

> fq>0 时客户端自动拉取除权信息并计算。指数 K 线不支持复权，fq 参数被忽略。

### 实时行情

```python
# 批量获取
quotes = client.get_security_quotes([
    (MARKET_SH, "600519"),
    (MARKET_SZ, "000858"),
    (MARKET_SZ, "300750"),
])
for q in quotes:
    print(f"{q['code']}: {q['price']:.2f} (昨收 {q['last_close']:.2f})")
```

### 分时和逐笔

```python
# 当日分时
ticks = client.get_minute_time_data(market=1, code="000001")

# 历史分时 (date: YYYYMMDD)
ticks = client.get_history_minute_time_data(market=1, code="000001", date=20260429)

# 逐笔成交
ticks = client.get_transaction_data(market=1, code="600519", start=0, count=100)

# 历史逐笔
ticks = client.get_history_transaction_data(market=1, code="600519", start=0, count=100, date=20260429)
```

### 财务数据

```python
# 实时财务 — 34 字段, TDX 原始值 (单位不固定)
info = client.get_finance_info(market=1, code="600519")
# 原始值: 股本类 ~10⁵ 量级 (万元), 资产类 ~10⁸, 每股指标 ~10¹
print(f"流通股本(raw): {info['liutongguben']:.2f}")     # e.g. 125227
print(f"总资产(raw):   {info['zongzichan']:.0f}")      # e.g. 319918848
print(f"每股净资产:     {info['meigujingzichan']:.2f}")  # e.g. 216.32
print(f"股东人数:       {info['gudongrenshu']:.0f}")     # e.g. 243159
print(f"更新日期:       {info['updated_date']}")         # e.g. 20260425

# 多股票财务 DataFrame
df = client.get_finance_info_dataframe([
    (MARKET_SH, "600519"), (MARKET_SZ, "000858"), (MARKET_SZ, "300750")
])
print(df[["code", "jingzichan", "jinglirun"]])
```

> **v0.5.1 起**: 所有财务字段返回 TDX 原始值，不自动做 ×10000 转换。不同字段单位不同（万元/千元/元/户），由用户自行判断。历史上 v0.5.0 及更早版本会 ×10000 放大。

> 45 个命名英文指标请使用 `TdxFinanceClient` (Rust API)。

### 除权除息

```python
xdxr = client.get_xdxr_info(market=1, code="600519")
for item in xdxr:
    if item['category'] == 1:
        print(f"{item['year']}-{item['month']:02d}-{item['day']:02d} "
              f"分红={item['fenhong']} 送转={item['songzhuangu']}")
```

### 证券列表

```python
# 证券数量 (带缓存, TTL 30s)
count = client.get_security_count(market=1)  # 上海

# 证券列表 (start=0 时启用缓存)
stocks = client.get_security_list(market=1, start=0)
for s in stocks[:5]:
    print(f"{s['code']} {s['name']} 昨收={s['pre_close']:.2f}")
```

### 板块数据

```python
blocks = client.get_and_parse_block_info("block_zs.dat")
```

---

## 高级配置

```python
client.set_auto_retry(False)       # 关闭内置重试 (生产环境推荐)
client.set_cache_ttl(120)           # 缓存 120 秒 (默认 30s)
client.set_connect_timeout(10.0)   # 连接超时 (默认 5s)

# 连接池状态
stats = client.pool_stats()
print(f"idle={stats['idle']} active={stats['active']} max={stats['max_size']}")

# 服务器管理
client.set_servers([("海通", "58.63.254.191", 7709)])
client.probe_servers(timeout=3.0)  # 探测延迟
```

---

## 市场代码

| 值 | 常量 | 市场 |
|:--:|------|------|
| 0 | `MARKET_SZ` | 深圳 |
| 1 | `MARKET_SH` | 上海 |
| 2 | `MARKET_BJ` | 北京 |

## K 线类型 (category)

| 值 | 常量 | 类型 | 支持 fq=0 |
|:--:|------|------|:--:|
| 0 | `KLINE_5MIN` | 5 分钟 | ✅ |
| 1 | `KLINE_15MIN` | 15 分钟 | ✅ |
| 2 | `KLINE_30MIN` | 30 分钟 | ✅ |
| 3 | `KLINE_1HOUR` | 1 小时 | ✅ |
| 4 | `KLINE_DAILY` | 日线 (推荐) | ✅ |
| 5 | `KLINE_WEEKLY` | 周线 | ✅ |
| 6 | `KLINE_MONTHLY` | 月线 | ✅ |
| 7 | `KLINE_EXHQ_1MIN` | 扩展 1 分钟 | ✅ |
| 8 | `KLINE_1MIN` | 1 分钟 | ✅ |
| 9 | `KLINE_RI_K` | 日线精简 | ❌ |
| 10 | `KLINE_3MONTH` | 季线 | ✅ |
| 11 | `KLINE_YEARLY` | 年线 | ✅ |

---

## Rust 使用

### 示例

```rust
use tdxrs::net::client::TdxHqClient;

fn main() {
    let client = TdxHqClient::new();
    client.connect_to_any(Some(5.0)).unwrap();

    // 日K — fq=1 前复权
    let bars = client.get_security_bars(4, 1, "600519", 0, 5, 1).unwrap();
    for bar in &bars {
        println!("{}: O={:.2} C={:.2}", bar.datetime, bar.open, bar.close);
    }

    // 实时行情
    let quotes = client.get_security_quotes(&[(1, "600519")]).unwrap();
    for q in &quotes {
        println!("{}: {:.2}", q.code, q.price);
    }

    client.disconnect();
}
```

### Rust API 速查

```rust
// 连接
client.connect(ip, port, timeout) -> Result<bool>
client.connect_to_any(timeout) -> Result<bool>
client.disconnect()
client.is_connected() -> bool

// 个股K线 (fq: 0=未复权 1=前复权 2=后复权)
client.get_security_bars(cat, mkt, code, start, count, fq) -> Result<Vec<SecurityBar>>
client.get_security_bars_all(cat, mkt, code, count, fq) -> Result<Vec<SecurityBar>>
// 指数K线 (fq 被忽略)
client.get_index_bars(cat, mkt, code, start, count, fq) -> Result<Vec<IndexBar>>
client.get_index_bars_all(cat, mkt, code, count, fq) -> Result<Vec<IndexBar>>

// 行情
client.get_security_quotes(&[(market, code)]) -> Result<Vec<SecurityQuote>>

// 列表
client.get_security_count(market) -> Result<u16>
client.get_security_list(market, start) -> Result<Vec<SecurityInfo>>

// 分时/逐笔
client.get_minute_time_data(market, code) -> Result<Vec<MinuteTimePrice>>
client.get_history_minute_time_data(market, code, date) -> Result<Vec<MinuteTimePrice>>
client.get_transaction_data(market, code, start, count) -> Result<Vec<TickData>>
client.get_history_transaction_data(market, code, start, count, date) -> Result<Vec<TickData>>

// 财务 — TDX 原始值, 不转换单位
client.get_finance_info(market, code) -> Result<FinanceInfo>
client.get_xdxr_info(market, code) -> Result<Vec<XdXrInfo>>

// 配置
client.set_auto_retry(bool)
client.set_cache_ttl(secs)
client.set_connect_timeout(secs)
client.pool_stats() -> PoolStats
```

---

## 常见问题

### Q: 连接超时

- 检查网络: `telnet 119.147.212.81 7709`
- 增加超时: `client.set_connect_timeout(10.0)`
- 尝试多服务器: `client.connect_to_any()`

### Q: K 线数据为空

- 确认市场代码正确 (0=深圳, 1=上海, 2=北京)
- 确认股票代码正确 (6 位数字)
- `category=9` 不支持 `fq=0`, 请用 `category=4`
- 非交易时间无实时数据

### Q: 财务数据怎么解读单位？

v0.5.1 起返回 TDX 原始值。经验规则:
- 股本类 (zongguben 等) → 万元 (÷10000 = 亿股)
- 资产/收入/利润类 → 万元 (÷10000 = 亿元)
- 每股指标 (meigujingzichan) → 元
- 股东人数 → 户

> 但不同服务器/版本返回单位可能不同，建议用已知数据 (如 600519 茅台) 交叉校验。

### Q: pip install 失败

- `rustc --version` ≥ 1.83
- `maturin --version` ≥ 1.5
- Windows GNU 工具链需 MSYS2 dlltool

### Q: Windows dlltool 错误

```powershell
# 安装 MSYS2
winget install MSYS2.MSYS2
# 在 MSYS2 UCRT64 终端:
pacman -S mingw-w64-ucrt-x86_64-binutils
# 加入 PATH (管理员 PowerShell, ⚠️ 勿用 setx):
[Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";C:\msys64\ucrt64\bin", "User")
```

### Q: maturin develop 未生效

Windows 上 `.pyd` 可能被 Python 进程锁定，手动复制:
```powershell
cp target/release/tdxrs.dll $env:VIRTUAL_ENV/Lib/site-packages/tdxrs/_internal.*.pyd
```
