"""tdxrs.pro - 扩展模块 (已弃用)

.. deprecated::
    v0.6.3 起，ETF 功能已合并至标准模块 ``tdxrs.TdxHqFundClient``。

    旧用法::

        from tdxrs.pro import TdxHqEtfClient  # 不再可用

    新用法::

        from tdxrs import TdxHqFundClient

    F10 模块需从源码编译启用::

        maturin develop --release --features f10
        from tdxrs._internal import TdxF10Client
"""


def __getattr__(name):
    if name == "TdxHqEtfClient":
        raise AttributeError(
            "TdxHqEtfClient 已移除，请使用 tdxrs.TdxHqFundClient 替代。"
        )
    if name == "TdxF10Client":
        raise AttributeError(
            "TdxF10Client 需从源码编译启用: maturin develop --release --features f10"
        )
    raise AttributeError(f"module 'tdxrs.pro' has no attribute {name!r}")
