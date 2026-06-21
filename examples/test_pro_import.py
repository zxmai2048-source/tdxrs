#!/usr/bin/env python3
"""
测试模块分层导入
"""

import sys

sys.path.insert(0, r"E:\claudeProjects\tdxrs\python")


def test_standard_import():
    """测试标准模块导入"""
    print("=" * 60)
    print("1. 标准模块导入 (from tdxrs import ...)")
    print("=" * 60)

    from tdxrs import (
        DailyBarReader, MinBarReader, LcMinBarReader, BlockReader, FinancialReader,
        TdxHqClient, TdxDirectClient,
    )

    print("  [OK] DailyBarReader")
    print("  [OK] MinBarReader")
    print("  [OK] LcMinBarReader")
    print("  [OK] BlockReader")
    print("  [OK] FinancialReader")
    print("  [OK] TdxHqClient")
    print("  [OK] TdxDirectClient")
    print()


def test_pro_import():
    """测试扩展模块导入"""
    print("=" * 60)
    print("2. 扩展模块导入 (from tdxrs.pro import ...)")
    print("=" * 60)

    from tdxrs.pro import TdxHqEtfClient
    print("  [OK] TdxHqEtfClient")

    try:
        from tdxrs.pro import TdxF10Client
        print("  [OK] TdxF10Client (f10 feature enabled)")
    except ImportError:
        print("  [SKIP] TdxF10Client (需要 --features f10 源码编译)")
    print()


def test_version():
    """测试版本信息"""
    print("=" * 60)
    print("3. 版本信息")
    print("=" * 60)

    import tdxrs

    print(f"  版本: {tdxrs.__version__}")
    print(f"  标准模块: {len(tdxrs.__all__)} 个")
    print(f"  标准模块列表: {', '.join(tdxrs.__all__)}")

    import tdxrs.pro

    print(f"  扩展模块: {len(tdxrs.pro.__all__)} 个")
    print(f"  扩展模块列表: {', '.join(tdxrs.pro.__all__)}")
    print()


def main():
    print("=" * 60)
    print("tdxrs 模块分层导入测试")
    print("=" * 60)
    print()

    test_standard_import()
    test_pro_import()
    test_version()

    print("=" * 60)
    print("总结")
    print("=" * 60)
    print()
    print("标准模块 (核心功能):")
    print("  from tdxrs import TdxHqClient, DailyBarReader, ...")
    print()
    print("扩展模块 (ETF):")
    print("  from tdxrs.pro import TdxHqEtfClient")
    print()
    print("F10 模块 (需源码编译):")
    print("  maturin develop --release --features f10")
    print("  from tdxrs.pro import TdxF10Client")


if __name__ == "__main__":
    main()
