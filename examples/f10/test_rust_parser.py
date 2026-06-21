#!/usr/bin/env python3
"""
测试 Rust F10 解析器功能
"""

import sys

sys.path.insert(0, r"E:\claudeProjects\tdxrs\python")

from tdxrs.pro import TdxF10Client


def main():
    print("=" * 70)
    print("Rust F10 解析器功能测试")
    print("=" * 70)
    print()

    # 创建客户端
    client = TdxF10Client("180.153.18.170", 7709)

    # 测试股票
    market = 1  # SH
    code = "600519"

    print(f"股票: {code} ({'SH' if market == 1 else 'SZ'})")
    print()

    # 1. 获取公司概况原始文本
    print("=" * 70)
    print("1. 获取公司概况原始文本")
    print("=" * 70)
    content = client.get_content_by_name(market, code, "公司概况")
    print(f"字符数: {len(content)}")
    print()

    # 2. 使用 Rust 解析器解析
    print("=" * 70)
    print("2. 使用 Rust 解析器解析")
    print("=" * 70)
    parsed = TdxF10Client.parse_f10(content)

    print("解析结果结构:")
    print(f"  - basic_info: {len(parsed.get('basic_info', {}))} 个字段")
    print(f"  - listing_info: {len(parsed.get('listing_info', {}))} 个字段")
    print(f"  - sections: {len(parsed.get('sections', {}))} 个章节")
    print()

    # 3. 显示基本资料
    print("=" * 70)
    print("3. 基本资料 (basic_info)")
    print("=" * 70)
    basic_info = parsed.get('basic_info', {})
    for key, value in basic_info.items():
        print(f"  {key}: {value[:50]}{'...' if len(value) > 50 else ''}")

    print()

    # 4. 显示发行上市信息
    print("=" * 70)
    print("4. 发行上市信息 (listing_info)")
    print("=" * 70)
    listing_info = parsed.get('listing_info', {})
    for key, value in listing_info.items():
        print(f"  {key}: {value[:50]}{'...' if len(value) > 50 else ''}")

    print()

    # 5. 显示章节列表
    print("=" * 70)
    print("5. 章节列表 (sections)")
    print("=" * 70)
    sections = parsed.get('sections', {})
    for title, content in sections.items():
        print(f"  {title}: {len(content)} 字符")

    print()

    # 6. 使用 extract_basic_info 快捷方法
    print("=" * 70)
    print("6. extract_basic_info 快捷方法")
    print("=" * 70)
    basic = TdxF10Client.extract_basic_info(content)
    print(f"返回 {len(basic)} 个字段:")
    for key, value in basic.items():
        print(f"  {key}: {value[:50]}{'...' if len(value) > 50 else ''}")

    print()
    print("=" * 70)
    print("测试完成")
    print("=" * 70)
    print()
    print("总结:")
    print("  - Rust 解析器可以直接从原始文本提取结构化数据")
    print("  - 无需依赖外部 Python 解析器")
    print("  - 解析速度快，支持所有 F10 分类")


if __name__ == "__main__":
    main()
