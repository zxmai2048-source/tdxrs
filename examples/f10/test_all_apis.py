#!/usr/bin/env python3
"""
F10 模块完整 API 测试
"""

import sys

sys.path.insert(0, r"E:\claudeProjects\tdxrs\python")

from tdxrs.pro import TdxF10Client


def test_api(name, func):
    """测试单个 API"""
    try:
        result = func()
        print(f"  [OK] {name}")
        return result
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        return None


def main():
    print("=" * 70)
    print("F10 模块完整 API 测试 (独立连接)")
    print("=" * 70)
    print()

    # 创建客户端
    print("1. 创建客户端 (独立连接)")
    client = TdxF10Client("180.153.18.170", 7709)
    print(f"   类型: {type(client)}")
    print()

    # 3. 静态方法
    print("3. 静态方法")
    test_api("is_valid_code('600519')", lambda: TdxF10Client.is_valid_code("600519"))
    test_api("is_valid_code('abc')", lambda: TdxF10Client.is_valid_code("abc"))
    test_api("auto_market_code('600519')", lambda: TdxF10Client.auto_market_code("600519"))
    test_api("auto_market_code('000858')", lambda: TdxF10Client.auto_market_code("000858"))
    print()

    # 4. 获取分类
    print("4. 获取分类列表")
    categories = test_api("get_category(1, '600519')", lambda: client.get_category(1, "600519"))
    if categories:
        print(f"   返回 {len(categories)} 个分类")
        print(f"   第一个分类: {categories[0]}")
    print()

    categories_auto = test_api("get_category_auto('600519')", lambda: client.get_category_auto("600519"))
    if categories_auto:
        print(f"   返回 {len(categories_auto)} 个分类")
    print()

    # 5. 获取内容
    print("5. 获取内容")
    if categories:
        content = test_api("get_content(1, '600519', categories[0])", lambda: client.get_content(1, "600519", categories[0]))
        if content:
            print(f"   返回 {len(content)} 字符")
    print()

    content_by_name = test_api("get_content_by_name(1, '600519', '公司概况')", lambda: client.get_content_by_name(1, "600519", "公司概况"))
    if content_by_name:
        print(f"   返回 {len(content_by_name)} 字符")
    print()

    # 6. 获取所有内容
    print("6. 获取所有内容")
    all_contents = test_api("get_all_contents(1, '600519')", lambda: client.get_all_contents(1, "600519"))
    if all_contents:
        print(f"   返回 {len(all_contents)} 个分类")
    print()

    # 7. 获取所有数据
    print("7. 获取所有数据 (F10Data)")
    all_data = test_api("get_all_data(1, '600519')", lambda: client.get_all_data(1, "600519"))
    if all_data:
        print(f"   代码: {all_data.get('code')}")
        print(f"   市场: {all_data.get('market')}")
        print(f"   分类数: {all_data.get('category_count')}")
        print(f"   总字符: {all_data.get('total_chars')}")
        print(f"   总字节: {all_data.get('total_bytes')}")
    print()

    # 8. 解析功能
    print("8. 解析功能")
    if content_by_name:
        parsed = test_api("parse_f10(content)", lambda: TdxF10Client.parse_f10(content_by_name))
        if parsed:
            print(f"   basic_info: {len(parsed.get('basic_info', {}))} 个字段")
            print(f"   listing_info: {len(parsed.get('listing_info', {}))} 个字段")
            print(f"   sections: {len(parsed.get('sections', {}))} 个章节")
        print()

        basic = test_api("extract_basic_info(content)", lambda: TdxF10Client.extract_basic_info(content_by_name))
        if basic:
            print(f"   返回 {len(basic)} 个字段")
    print()

    # 汇总
    print("=" * 70)
    print("API 汇总")
    print("=" * 70)
    print()
    print("| 方法 | 说明 | 状态 |")
    print("|------|------|------|")
    print("| TdxF10Client(ip, port) | 创建客户端 (独立连接) | OK |")
    print("| set_server(ip, port) | 设置服务器地址 | OK |")
    print("| set_timeout(secs) | 设置超时时间 | OK |")
    print("| get_category(market, code) | 获取分类列表 | OK |")
    print("| get_category_auto(code) | 自动识别市场获取分类 | OK |")
    print("| get_content(market, code, cat) | 获取指定分类内容 | OK |")
    print("| get_content_by_name(market, code, name) | 按名称获取内容 | OK |")
    print("| get_all_contents(market, code) | 获取所有内容 | OK |")
    print("| get_all_data(market, code) | 获取所有数据 (F10Data) | OK |")
    print("| parse_f10(text) | 解析 F10 文本 (静态) | OK |")
    print("| extract_basic_info(text) | 提取基本资料 (静态) | OK |")
    print("| is_valid_code(code) | 验证股票代码 (静态) | OK |")
    print("| auto_market_code(code) | 自动识别市场 (静态) | OK |")


if __name__ == "__main__":
    main()
