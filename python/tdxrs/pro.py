"""tdxrs.pro - 扩展模块

包含 ETF 数据等扩展功能。F10 模块需从源码编译启用 (见下方说明)。

## 模块说明

| 模块 | 类 | 连接方式 | 说明 | 获取方式 |
|------|-----|----------|------|----------|
| ETF | TdxHqEtfClient | 共享连接池 | ETF 行情数据 | `pip install tdxrs` |
| F10 | TdxF10Client | 独立连接 | F10 公司资料 | 源码编译 (`--features f10`) |

## 使用方式

```python
from tdxrs.pro import TdxHqEtfClient
```

## ETF 示例

```python
from tdxrs.pro import TdxHqEtfClient
from tdxrs.constants import MARKET_SH

client = TdxHqEtfClient()
client.connect_to_any()

# ETF 列表
sh_etfs = client.get_etf_list(MARKET_SH)

# K线
bars = client.get_etf_bars(4, MARKET_SH, "510300", 0, 100)

# 行情
quotes = client.get_etf_quotes([(MARKET_SH, "510300")])
```

## F10 示例 (需源码编译)

```bash
# 安装 (从源码编译, 启用 f10 feature)
git clone https://github.com/jiangtaovan/tdxrs && cd tdxrs
pip install maturin
maturin develop --release --features f10
```

```python
from tdxrs.pro import TdxF10Client

client = TdxF10Client("180.153.18.170", 7709)

# 获取分类列表
categories = client.get_category(1, "600519")

# 获取公司概况 (推荐: 传入分类字典)
content = client.get_content(1, "600519", categories[1])

# 解析为结构化数据
parsed = TdxF10Client.parse_f10(content)
print(parsed['basic_info'].get('公司名称'))
```
"""

try:
    from tdxrs._internal import TdxHqEtfClient
except ImportError:
    raise ImportError(
        "tdxrs native module not found. Please install with: pip install tdxrs"
    )

__all__ = [
    "TdxHqEtfClient",
]

# F10 模块需从源码编译启用: maturin develop --release --features f10
try:
    from tdxrs._internal import TdxF10Client
    __all__.append("TdxF10Client")
except ImportError:
    pass
