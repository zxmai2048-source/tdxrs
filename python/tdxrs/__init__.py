"""tdxrs - 通达信行情数据解析库 (Rust 实现)"""

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
