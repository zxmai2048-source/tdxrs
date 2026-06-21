#!/usr/bin/env python3
"""
Rust F10 解析器最终测试
"""

import sys
import os

sys.path.insert(0, r"E:\claudeProjects\tdxrs\python")

from tdxrs.pro import TdxF10Client


def main():
    print("=" * 70)
    print("Rust F10 解析器 - 最终测试")
    print("=" * 70)
    print()

    # 创建客户端
    client = TdxF10Client("180.153.18.170", 7709)

    # 测试股票
    market = 1  # SH
    code = "600519"

    print(f"股票: {code} ({'SH' if market == 1 else 'SZ'})")
    print()

    # 1. 获取公司概况
    print("=" * 70)
    print("1. 获取并解析公司概况")
    print("=" * 70)
    content = client.get_content_by_name(market, code, "公司概况")
    print(f"原始文本长度: {len(content)} 字符")
    print()

    # 2. 使用 Rust 解析器
    print("=" * 70)
    print("2. Rust 解析器结果")
    print("=" * 70)
    parsed = TdxF10Client.parse_f10(content)

    # 基本资料
    basic_info = parsed.get('basic_info', {})
    print(f"\n基本资料: {len(basic_info)} 个字段")
    for k, v in basic_info.items():
        print(f"  {k}: {v[:60]}{'...' if len(v) > 60 else ''}")

    # 发行上市信息
    listing_info = parsed.get('listing_info', {})
    print(f"\n发行上市信息: {len(listing_info)} 个字段")
    for k, v in listing_info.items():
        print(f"  {k}: {v[:60]}{'...' if len(v) > 60 else ''}")

    # 章节列表
    sections = parsed.get('sections', {})
    print(f"\n章节列表: {len(sections)} 个章节")
    for title in sections.keys():
        print(f"  - {title}")

    print()
    print("=" * 70)
    print("总结")
    print("=" * 70)
    print()
    print("Rust F10 解析器功能:")
    print("  1. 获取分类列表: get_category()")
    print("  2. 获取原始文本: get_content() / get_content_by_name()")
    print("  3. 解析结构化数据: parse_f10()")
    print("  4. 提取基本资料: extract_basic_info()")
    print()
    print("数据格式:")
    print("  - basic_info: 基本资料 (公司名称、证券代码等)")
    print("  - listing_info: 发行上市信息 (发行日期、发行价等)")
    print("  - sections: 所有章节内容")
    print()
    print("优势:")
    print("  - 无需外部 Python 解析器")
    print("  - 解析速度快")
    print("  - 支持所有 F10 分类")


if __name__ == "__main__":
    main()
