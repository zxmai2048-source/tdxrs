# tdxrs CLI 使用指南

> 版本: v0.6.5 | 更新日期: 2026-07-01

tdxrs 提供命令行工具，无需编写代码即可快速查询股票行情数据、测试服务器连通性、批量下载数据。

---

## 安装

CLI 随 tdxrs 包一起安装，无需额外依赖：

```bash
pip install tdxrs

# 或从源码安装
git clone <repo-url> && cd tdxrs
maturin develop --release
```

## 快速开始

```bash
# 查看贵州茅台实时行情
tdxrs quote 600519

# 获取最近 30 天日K线
tdxrs bars 600519 --count 30

# 获取前复权周K线
tdxrs bars 600519 --category week --fq 1

# JSON 输出（可被 jq 等工具处理）
tdxrs quote 600519,000858 --format json

# 测试服务器连通性
tdxrs servers

# 查看版本
tdxrs version
```

也可通过 `python -m tdxrs` 调用：

```bash
python -m tdxrs quote 600519
```

---

## 命令一览

| 命令 | 说明 | 示例 |
|------|------|------|
| `quote` | 实时行情 | `tdxrs quote 600519,000858` |
| `bars` | K线数据 | `tdxrs bars 600519 --count 100` |
| `minutes` | 分时数据 | `tdxrs minutes 600519` |
| `trades` | 逐笔成交 | `tdxrs trades 600519 --count 50` |
| `stocks` | 股票列表 | `tdxrs stocks --market sh` |
| `index` | 指数成分 | `tdxrs index 000300` |
| `xdxr` | 除权除息信息 | `tdxrs xdxr 600519` |
| `download` | 批量下载 | `tdxrs download --market sh` |
| `update` | 增量更新 | `tdxrs update` |
| `download-xdxr` | 下载除权除息数据 | `tdxrs download-xdxr --market sh` |
| `parse` | 本地文件解析 | `tdxrs parse sh600519.day` |
| `servers` | 服务器测试 | `tdxrs servers` |
| `version` | 版本信息 | `tdxrs version` |

---

## 网络查询命令

### `tdxrs quote` — 实时行情

查询股票实时行情（最新价、涨跌幅、五档等）。

```bash
tdxrs quote 600519                          # 单只
tdxrs quote 600519,000858,300750            # 多只（逗号分隔，最多 20 只）
tdxrs quote 600519 --format json            # JSON 输出
```

| 参数 | 默认 | 上限 | 说明 |
|------|------|------|------|
| `codes` | 必填 | 20 | 股票代码，逗号分隔 |
| `--timeout` | 5.0 | — | 超时秒数 |
| `--format` | table | — | table / json / csv |

### `tdxrs bars` — K线数据

获取股票K线数据（日线、周线、分钟线等）。

```bash
tdxrs bars 600519                               # 最近 10 天日线（默认）
tdxrs bars 600519 --count 30                    # 最近 30 天
tdxrs bars 600519 --category 5min               # 5 分钟线
tdxrs bars 600519 --category week --count 50    # 周K线 50 条
tdxrs bars 600519 --fq 1 --count 200            # 前复权 200 条
tdxrs bars 600519 --fq 2                        # 后复权
tdxrs bars 600519 --format csv                  # CSV 输出
```

| 参数 | 默认 | 上限 | 说明 |
|------|------|------|------|
| `code` | 必填 | — | 股票代码 |
| `--category` | day | — | 5min/15min/30min/60min/day/week/month/season/year |
| `--count` | 10 | 800 | 返回条数 |
| `--fq` | 0 | — | 0=原始(支持增量) 1=前复权(全量覆盖) 2=后复权(全量覆盖) |

| `--timeout` | 5.0 | — | 超时秒数 |
| `--format` | table | — | table / json / csv |

### `tdxrs minutes` — 分时数据

获取当日分时数据（240 个数据点）。

```bash
tdxrs minutes 600519                    # 默认 20 条
tdxrs minutes 600519 --count 50         # 50 条
tdxrs minutes 600519 --format json
```

| 参数 | 默认 | 上限 | 说明 |
|------|------|------|------|
| `code` | 必填 | — | 股票代码 |
| `--count` | 20 | 240 | 返回条数 |
| `--timeout` | 5.0 | — | 超时秒数 |
| `--format` | table | — | table / json / csv |

**输出字段**: 时间、价格、涨跌幅%、均价、成交量（手）

**时间范围**:
- 上午: 09:31 ~ 11:30 (120 点)
- 下午: 13:01 ~ 15:00 (120 点)
- 上下午开盘集合竞价 (09:30、13:00) 不包含在内

> 注意: 成交量单位为**手**（1手=100股），非股数。

### `tdxrs trades` — 逐笔成交

获取当日逐笔成交记录。

```bash
tdxrs trades 600519                 # 最近 10 笔（默认）
tdxrs trades 600519 --count 200     # 最近 200 笔
tdxrs trades 600519 --format csv    # CSV 输出
```

| 参数 | 默认 | 上限 | 说明 |
|------|------|------|------|
| `code` | 必填 | — | 股票代码 |
| `--count` | 10 | 500 | 返回条数 |
| `--timeout` | 5.0 | — | 超时秒数 |
| `--format` | table | — | table / json / csv |

**输出字段**: 时间、价格、成交量（手）、笔数、买/卖

> 注意: 成交量单位为**手**（1手=100股），非股数。

### `tdxrs stocks` — 股票列表

获取市场股票列表。

```bash
tdxrs stocks --market sh                # 沪市前 10 只（默认）
tdxrs stocks --market sz --count 100    # 深市 100 只
tdxrs stocks --market sh --offset 50    # 从第 51 只开始
```

| 参数 | 默认 | 上限 | 说明 |
|------|------|------|------|
| `--market` | sh | — | sh / sz |
| `--offset` | 0 | — | 起始偏移 |
| `--count` | 10 | 200 | 返回数量 |

| `--timeout` | 5.0 | — | 超时秒数 |
| `--format` | table | — | table / json |

### `tdxrs index` — 指数成分

获取指数成分股列表。

```bash
tdxrs index 000300                   # 沪深 300 前 10 只（默认）
tdxrs index 000300 --count 100       # 沪深 300 前 100 只
tdxrs index 000016 --format json     # 上证 50 JSON 输出
```

| 参数 | 默认 | 上限 | 说明 |
|------|------|------|------|
| `code` | 必填 | — | 指数代码（如 000300） |
| `--offset` | 0 | — | 起始偏移 |
| `--count` | 10 | 100 | 返回数量 |

| `--timeout` | 5.0 | — | 超时秒数 |
| `--format` | table | — | table / json |

### `tdxrs xdxr` — 除权除息信息

获取股票除权除息历史记录。

```bash
tdxrs xdxr 600519                      # 最新 10 条（默认）
tdxrs xdxr 600519 --count 50           # 最新 50 条
tdxrs xdxr 600519 --format json        # JSON 输出
```

| 参数 | 默认 | 上限 | 说明 |
|------|------|------|------|
| `code` | 必填 | — | 股票代码 |
| `--count` | 10 | 100 | 返回数量 |

| `--timeout` | 5.0 | — | 超时秒数 |
| `--format` | table | — | table / json / csv |

返回字段: `日期`, `类型`(分红/送股/配股/缩股), `分红(元)`, `送股`, `配股`, `配股价`, `缩股`

---

## 数据下载命令

### `tdxrs download` — 下载股票数据

下载指定股票的K线数据，支持多服务器分发和限流。

```bash
tdxrs download 600519                            # 下载单只股票日线
tdxrs download 600519,000858                     # 下载多只股票 (逗号分隔，最多20只)
tdxrs download 600519 --category week            # 周线
tdxrs download 600519 --format csv               # CSV 格式
tdxrs download 600519 --output ~/stock_data      # 自定义输出目录
tdxrs download 600519 --fq 1                     # 前复权数据
tdxrs download 600519 --start 2024-01-01         # 从指定日期开始下载
tdxrs download 600519 --start 2024-01-01 --end 2024-12-31  # 指定日期范围
```

| 参数 | 默认 | 上限 | 说明 |
|------|------|------|------|
| `code` | 必填 | 20 只 | 股票代码，逗号分隔 |
| `--category` | day | — | K线类型 (day/week/month/5min/15min/30min/60min) |
| `--format` | tdx | — | tdx / csv / parquet |
| `--output` | ./data | — | 输出目录 |
| `--fq` | 0 | — | 0=原始(支持增量) 1=前复权(全量覆盖) 2=后复权(全量覆盖) |
| `--start` | — | — | 起始日期 YYYY-MM-DD |
| `--end` | — | — | 结束日期 YYYY-MM-DD |
| `--servers` | 内置 | — | 服务器列表，逗号分隔 |
| `--rate-limit` | 15 | 50 | 每秒请求数 |

> **复权说明**: fq=0 下载原始数据，支持增量更新；fq=1/2 下载复权数据，不支持增量更新，需全量覆盖。

> **批量下载**: 如需下载全市场数据，请使用 Python API `Downloader.run()`。

**默认保存位置**: `./data/`（当前目录下的 data 文件夹）

**文件结构**:
```
data/
├── sh/
│   ├── daily/          # 日线
│   │   ├── 600519.day
│   │   └── ...
│   ├── weekly/         # 周线
│   ├── monthly/        # 月线
│   └── min5/           # 5分钟线
├── sz/
│   ├── daily/
│   │   ├── 000858.day
│   │   └── ...
│   └── ...
└── xdxr/               # 除权除息数据
    ├── sh/
    │   └── 600519.csv
    └── sz/
        └── 000858.csv
```

### `tdxrs update` — 增量更新

仅下载新增数据，基于上次同步记录自动判断起始位置。仅支持 fq=0 (原始数据)。

```bash
tdxrs update                              # 增量更新已下载的股票
tdxrs update --code 600519                # 增量更新指定股票
tdxrs update --code 600519,000858         # 增量更新多只股票
tdxrs update --market sh                  # 仅沪市已下载的股票
tdxrs update --category weekly            # 仅周线
tdxrs update --start 2024-01-01           # 从指定日期开始增量更新
tdxrs update --start 2024-01-01 --end 2024-12-31  # 指定日期范围
```

| 参数 | 默认 | 上限 | 说明 |
|------|------|------|------|
| `--code` | — | 20 只 | 股票代码，逗号分隔 (默认更新已下载的股票) |
| `--market` | all | — | sh / sz / all |
| `--category` | day | — | K线类型 |
| `--format` | tdx | — | tdx / csv / parquet |
| `--output` | ./data | — | 数据目录 |
| `--start` | — | — | 起始日期 YYYY-MM-DD |
| `--end` | — | — | 结束日期 YYYY-MM-DD |
| `--servers` | 内置 | — | 服务器列表 |
| `--rate-limit` | 15 | 50 | 每秒请求数 |

> **注意**: `update` 命令默认只更新已下载的股票，不会下载新股票。如需下载新股票，请使用 `download` 命令。

### `tdxrs download-xdxr` — 下载除权除息数据

下载指定股票的除权除息数据，保存为 CSV 文件。

```bash
tdxrs download-xdxr 600519                        # 单只股票
tdxrs download-xdxr 600519,000858                 # 多只股票 (逗号分隔，最多20只)
tdxrs download-xdxr 600519 --output ~/data        # 自定义目录
```

输出目录结构:
```
{output}/xdxr/
├── sh/
│   ├── 600519.csv
│   └── ...
└── sz/
    ├── 000858.csv
    └── ...
```

CSV 字段: `date`, `category`, `fenhong`, `peigujia`, `songzhuangu`, `peigu`, `suogu`

| 参数 | 默认 | 说明 |
|------|------|------|
| `code` | 必填 | 股票代码，逗号分隔 (最多20只) |
| `--output` | ./data | 输出目录 |
| `--servers` | 内置 | 服务器列表 |
| `--rate-limit` | 15 | 每秒请求数 |

> **批量下载**: 如需下载全市场 XDXR 数据，请使用 Python API `Downloader.run_xdxr()`。

---

## 本地解析命令

### `tdxrs parse` — 本地文件解析

解析 TDX 二进制数据文件（`.day`、分钟线、板块文件等）。

```bash
tdxrs parse sh600519.day                      # 解析日线文件
tdxrs parse sh600519.day --count 10           # 只显示 10 条
tdxrs parse sh600519.day --format json        # JSON 输出
tdxrs parse sh600519.day --format csv         # CSV 输出
tdxrs parse block_zs.dat --type block         # 解析板块文件
```

| 参数 | 默认 | 说明 |
|------|------|------|
| `file` | 必填 | 文件路径 |
| `--type` | auto | auto / daily / min / block |
| `--count` | all | 显示条数 |
| `--format` | table | table / json / csv |

**自动类型检测**:
- `.day` 文件 → 日线
- `.5` / `.15` / `.30` / `.60` 文件 → 分钟线
- `block_*.dat` 文件 → 板块数据

---

## 工具命令

### `tdxrs servers` — 服务器测试

测试所有内置服务器的连通性和延迟。

```bash
tdxrs servers                 # 默认 3 秒超时
tdxrs servers --timeout 5     # 5 秒超时
```

输出示例：

```
测试服务器连通性...

可用服务器: 10/10
平均延迟: 183ms
延迟范围: 111ms ~ 253ms
```

### `tdxrs version` — 版本信息

```bash
tdxrs version
# tdxrs 0.6.5
# Python 3.13.5
# platform win32
```

---

## 通用选项

所有网络命令支持以下通用选项：

| 选项 | 说明 | 默认 |
|------|------|------|
| `--timeout SECONDS` | 超时时间 | 5.0 秒 |
| `--format {table,json,csv}` | 输出格式 | table |

### 输出格式

**table** — 人类可读表格（默认）

```
┌──────────┬────────┬────────┬────────┐
│ 代码     │ 最新   │ 涨跌%  │ 成交量 │
├──────────┼────────┼────────┼────────┤
│ 600519   │ 1580.0 │ +1.20  │ 12,345 │
└──────────┴────────┴────────┴────────┘
```

**json** — 结构化数据，可被 `jq` 等工具处理

```json
[
  {
    "代码": "600519",
    "最新": "1580.00",
    "涨跌%": "+1.20"
  }
]
```

**csv** — 标准 CSV 格式，可导入 Excel

```csv
代码,最新,涨跌%,成交量
600519,1580.00,+1.20,"12,345"
```

---

## 参数限制

CLI 定位为轻量调试工具，参数上限远低于 Python API：

| 命令 | 限制参数 | CLI 默认 | CLI 上限 | API 默认 |
|------|---------|---------|---------|---------|
| quote | codes 数量 | — | **20** | 80 |
| bars | count | 100 | **800** | 无限制 |
| trades | count | 50 | **500** | 无限制 |
| stocks | count | 50 | **200** | 1000 |
| index | count | 30 | **100** | 1000 |
| download | rate-limit | 15 | **50** | 200 |
| download | count/股 | 250 | **1000** | 无限制 |

超限时 CLI 会立即报错，不发起网络请求：

```
$ tdxrs bars 600519 --count 2000
error: K线条数 最大 800，当前 2000。如需更多数据请使用 tdxrs Python API。
```

---

## 使用场景示例

### 快速查看多只股票行情

```bash
tdxrs quote 600519,000858,300750,601318
```

### 导出K线数据到 CSV

```bash
tdxrs bars 600519 --count 500 --format csv > 600519_daily.csv
```

### 批量下载后用 Python 分析

```bash
# 下载
tdxrs download --market sh --category daily --output ./data

# Python 分析
python -c "
from tdxrs import DailyBarReader
reader = DailyBarReader()
data = reader.parse_file('./data/sh/daily/600519.day')
print(f'Total bars: {len(data)}')
"
```

### 测试哪个服务器最快

```bash
tdxrs servers --timeout 3
# 选择延迟最低的服务器用于 API 调用
```

### JSON 输出配合 jq

```bash
# 获取最新价
tdxrs quote 600519 --format json | jq '.[0]["最新"]'

# 获取涨跌%
tdxrs quote 600519,000858 --format json | jq '.[] | {代码: .["代码"], 涨跌: .["涨跌%"]}'
```

---

## 常见问题

### Q: 中文显示乱码？

Windows 控制台默认使用 GBK 编码，tdxrs CLI 的中文输出可能显示为乱码。功能不受影响，JSON/CSV 输出可被程序正常解析。

解决方案：
- 使用 Windows Terminal（默认 UTF-8）
- 或设置 `chcp 65001` 切换到 UTF-8 编码

### Q: 如何获取超过 800 条K线？

CLI 单次上限 800 条。如需更多数据，请使用 Python API：

```python
from tdxrs import TdxHqClient
client = TdxHqClient()
client.connect_to_any()
all_bars = client.get_security_bars_all(KLINE_DAILY, MARKET_SH, "600519", count=5000)
```

### Q: 下载数据存放在哪里？

默认存放在当前目录下的 `./data/` 文件夹。可通过 `--output` 参数自定义：

```bash
tdxrs download --output ~/stock_data
```

### Q: 如何使用自定义服务器？

CLI 命令自动选择可用服务器，无需手动指定。如需批量下载时指定服务器列表，可使用 `--servers` 参数：

```bash
tdxrs download 600519 --servers "119.29.19.242:7709,180.153.18.170:7709"
```
