"""tdxrs - 通达信行情数据解析库 (Rust 实现)

标准模块包含核心功能：
- Reader: 日线、分钟线、板块、财务数据解析
- Client: 行情客户端 (TdxHqClient, TdxDirectClient)

扩展模块请使用 `from tdxrs.pro import ...`:
- TdxHqEtfClient: ETF 数据客户端
- TdxF10Client: F10 公司资料客户端
"""

try:
    from tdxrs._internal import (
        DailyBarReader, MinBarReader, LcMinBarReader, BlockReader, FinancialReader,
        TdxHqClient, TdxDirectClient,
    )
except ImportError:
    raise ImportError(
        "tdxrs native module not found. Please install with: pip install tdxrs"
    )

__version__ = "0.5.0"
__all__ = [
    "DailyBarReader", "MinBarReader", "LcMinBarReader", "BlockReader", "FinancialReader",
    "TdxHqClient", "TdxDirectClient",
]
