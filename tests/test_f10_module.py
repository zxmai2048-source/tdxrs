#!/usr/bin/env python3
"""
F10 模块 Python 集成测试

测试 TdxF10Client 的基本功能 (独立连接模式)。
需要网络连接到通达信服务器。
"""

import sys
import time

# 添加路径以导入本地 tdxrs
sys.path.insert(0, r"E:\claudeProjects\tdxrs\python")

from tdxrs.pro import TdxF10Client


def test_import():
    """测试导入"""
    print("[1/7] 测试导入...")
    assert TdxF10Client is not None
    print("  OK - 导入成功")


def test_static_methods():
    """测试静态方法"""
    print("[2/7] 测试静态方法...")

    # 测试 is_valid_code
    assert TdxF10Client.is_valid_code("600519") == True
    assert TdxF10Client.is_valid_code("000858") == True
    assert TdxF10Client.is_valid_code("abc") == False
    assert TdxF10Client.is_valid_code("12345") == False
    print("  OK - is_valid_code 正确")

    # 测试 auto_market_code
    assert TdxF10Client.auto_market_code("600519") == 1  # SH
    assert TdxF10Client.auto_market_code("000858") == 0  # SZ
    assert TdxF10Client.auto_market_code("300750") == 0  # SZ
    print("  OK - auto_market_code 正确")


def test_client_creation():
    """测试客户端创建"""
    print("[3/7] 测试客户端创建 (独立连接)...")
    client = TdxF10Client("180.153.18.170", 7709)
    assert client is not None
    print("  OK - 客户端创建成功")
    return client


def test_get_category():
    """测试获取分类列表"""
    print("[4/7] 测试获取分类列表...")
    client = TdxF10Client("180.153.18.170", 7709)

    # 获取 600519 (贵州茅台) 的分类
    categories = client.get_category(1, "600519")

    assert categories is not None
    assert len(categories) > 0
    print(f"  OK - 获取到 {len(categories)} 个分类")

    return client


def test_get_content():
    """测试获取内容"""
    print("[5/7] 测试获取内容...")
    client = TdxF10Client("180.153.18.170", 7709)

    # 获取分类列表
    categories = client.get_category(1, "600519")
    assert len(categories) > 0

    # 获取第一个分类的内容
    first_cat = categories[0]
    content = client.get_content(1, "600519", first_cat)

    assert content is not None
    assert len(content) > 0
    print(f"  OK - 获取 '{first_cat['name']}' 成功 ({len(content)} 字符)")

    return client


def test_get_all_contents():
    """测试获取所有内容"""
    print("[6/7] 测试获取所有内容...")
    client = TdxF10Client("180.153.18.170", 7709)

    # 获取所有内容
    all_contents = client.get_all_contents(1, "600519")

    assert all_contents is not None
    assert len(all_contents) > 0
    print(f"  OK - 获取所有内容成功 ({len(all_contents)} 个分类)")

    return client


def test_parse_f10():
    """测试解析功能"""
    print("[7/7] 测试解析功能...")
    client = TdxF10Client("180.153.18.170", 7709)

    # 获取公司概况
    content = client.get_content_by_name(1, "600519", "公司概况")
    assert content is not None
    assert len(content) > 0

    # 解析
    parsed = TdxF10Client.parse_f10(content)
    assert parsed is not None

    basic_info = parsed.get('basic_info', {})
    listing_info = parsed.get('listing_info', {})
    sections = parsed.get('sections', {})

    print(f"  OK - 解析成功: basic_info={len(basic_info)}, listing_info={len(listing_info)}, sections={len(sections)}")

    return client


def main():
    """主测试函数"""
    print("=" * 60)
    print("F10 模块 Python 集成测试 (独立连接)")
    print("=" * 60)
    print()

    start_time = time.time()

    try:
        # 基本测试
        test_import()
        test_static_methods()
        client = test_client_creation()

        # 功能测试
        test_get_category()
        test_get_content()
        test_get_all_contents()
        test_parse_f10()

        elapsed = time.time() - start_time
        print()
        print("=" * 60)
        print(f"所有测试通过! ({elapsed:.2f}s)")
        print("=" * 60)

        return 0

    except Exception as e:
        elapsed = time.time() - start_time
        print()
        print("=" * 60)
        print(f"测试失败: {e} ({elapsed:.2f}s)")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
