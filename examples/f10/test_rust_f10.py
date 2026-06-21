#!/usr/bin/env python3
"""
测试 Rust F10 模块返回的数据格式
"""

import sys
import json

sys.path.insert(0, r"E:\claudeProjects\tdxrs\python")

from tdxrs.pro import TdxF10Client


def main():
    print("=" * 70)
    print("Rust F10 模块数据格式测试")
    print("=" * 70)
    print()

    # 创建客户端
    client = TdxF10Client("180.153.18.170", 7709)

    # 测试股票
    market = 1  # SH
    code = "601012"

    print(f"股票: {code} ({'SH' if market == 1 else 'SZ'})")
    print()

    # 1. 获取分类列表
    print("=" * 70)
    print("1. get_category() 返回格式")
    print("=" * 70)
    categories = client.get_category(market, code)
    print(f"返回类型: {type(categories)}")
    print(f"元素数量: {len(categories)}")
    print()
    print("第一个分类示例:")
    if categories:
        cat = categories[0]
        print(f"  类型: {type(cat)}")
        print(f"  内容: {cat}")
        print()
        print("  字段说明:")
        print(f"    cat['name']     = {repr(cat['name'])}")
        print(f"    cat['filename'] = {repr(cat['filename'])}")
        print(f"    cat['start']    = {cat['start']} (类型: {type(cat['start'])})")
        print(f"    cat['length']   = {cat['length']} (类型: {type(cat['length'])})")

    print()
    print("=" * 70)
    print("2. get_content() 返回格式")
    print("=" * 70)
    if categories:
        cat = categories[0]
        content = client.get_content(market, code, cat)
        print(f"返回类型: {type(content)}")
        print(f"字符数: {len(content)}")
        print()
        print("内容预览 (前 500 字符):")
        print("-" * 50)
        print(content[:500])
        print("-" * 50)

    print()
    print("=" * 70)
    print("3. get_content_by_name() 返回格式")
    print("=" * 70)
    content = client.get_content_by_name(market, code, "公司概况")
    print(f"返回类型: {type(content)}")
    print(f"字符数: {len(content)}")
    print()
    print("内容预览 (前 500 字符):")
    print("-" * 50)
    print(content[:500])
    print("-" * 50)

    print()
    print("=" * 70)
    print("4. get_all_contents() 返回格式")
    print("=" * 70)
    all_contents = client.get_all_contents(market, code)
    print(f"返回类型: {type(all_contents)}")
    print(f"分类数量: {len(all_contents)}")
    print()
    print("各分类字符数:")
    for name, text in all_contents.items():
        # 只输出 ASCII 安全的部分
        safe_len = len(text)
        print(f"  [{safe_len} chars]")

    print()
    print("=" * 70)
    print("5. 与 Python 原始实现对比")
    print("=" * 70)
    print()
    print("Rust 返回的是原始文本内容，需要解析才能提取结构化数据。")
    print("参考 examples/f10/f10_parser.py 中的解析逻辑。")
    print()
    print("Rust 返回格式 vs Python 原始实现:")
    print("  - get_category()      -> 返回分类列表 (字典数组)")
    print("  - get_content()       -> 返回原始文本字符串")
    print("  - get_content_by_name() -> 返回原始文本字符串")
    print("  - get_all_contents()  -> 返回 {分类名: 文本} 字典")
    print()
    print("如需结构化数据，需在 Python 层使用 F10Parser 解析。")

    print()
    print("=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
