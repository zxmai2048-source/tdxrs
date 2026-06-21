#!/usr/bin/env python3
"""
F10 数据下载脚本

下载指定股票的完整 F10 数据到本地目录。
"""

import os
import sys
import time

# 添加路径
sys.path.insert(0, r"E:\claudeProjects\tdxrs\python")

from tdxrs.pro import TdxF10Client


def download_f10_data(code: str, market: int = None, output_dir: str = None):
    """
    下载 F10 数据到本地

    Args:
        code: 股票代码
        market: 市场代码 (0=SZ, 1=SH)，None 则自动识别
        output_dir: 输出目录，None 则使用默认目录
    """
    # 自动识别市场
    if market is None:
        market = TdxF10Client.auto_market_code(code)

    # 设置输出目录
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "output", code)

    os.makedirs(output_dir, exist_ok=True)

    print(f"股票代码: {code}")
    print(f"市场代码: {market} ({'SH' if market == 1 else 'SZ'})")
    print(f"输出目录: {output_dir}")
    print()

    # 创建客户端
    client = TdxF10Client("180.153.18.170", 7709)
    print()

    # 获取分类列表
    print("正在获取分类列表...")
    categories = client.get_category(market, code)
    print(f"获取到 {len(categories)} 个分类")
    print()

    # 下载每个分类
    print("正在下载数据...")
    success_count = 0
    total_chars = 0

    for i, cat in enumerate(categories, 1):
        # 清理名称中的特殊字符和 null 字符
        name = cat['name'].replace('\x00', '').replace('�', '_').strip()
        if not name:
            name = f"category_{i}"
        filename = cat['filename']

        try:
            content = client.get_content(market, code, cat)

            # 保存到文件
            output_file = os.path.join(output_dir, f"{name}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

            char_count = len(content)
            total_chars += char_count
            success_count += 1

            print(f"  [{i:2d}/{len(categories)}] {name:10s} -> {output_file} ({char_count:,d} 字符)")

        except Exception as e:
            print(f"  [{i:2d}/{len(categories)}] {name:10s} -> 失败: {e}")

    print()

    # 保存索引文件
    index_file = os.path.join(output_dir, "index.txt")
    with open(index_file, 'w', encoding='utf-8') as idx_f:
        idx_f.write(f"股票代码: {code}\n")
        idx_f.write(f"市场代码: {market} ({'SH' if market == 1 else 'SZ'})\n")
        idx_f.write(f"下载时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        idx_f.write(f"分类数量: {len(categories)}\n")
        idx_f.write(f"成功数量: {success_count}\n")
        idx_f.write(f"总字符数: {total_chars:,d}\n")
        idx_f.write("=" * 60 + "\n")
        idx_f.write(f"{'分类名称':<12s} {'文件名':<20s} {'字节数':>10s} {'字符数':>10s}\n")
        idx_f.write("-" * 60 + "\n")
        for cat in categories:
            # 清理名称中的特殊字符和 null 字符
            name = cat['name'].replace('\x00', '').replace('�', '_').strip()
            if not name:
                name = f"category_{i}"
            output_file = os.path.join(output_dir, f"{name}.txt")
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as content_f:
                    char_count = len(content_f.read())
                idx_f.write(f"{name:<12s} {cat['filename']:<20s} {cat['length']:>10,d} {char_count:>10,d}\n")

    print(f"索引文件: {index_file}")
    print()

    # 汇总
    print("=" * 60)
    print(f"下载完成!")
    print(f"  成功: {success_count}/{len(categories)} 个分类")
    print(f"  总字符数: {total_chars:,d}")
    print(f"  输出目录: {output_dir}")
    print("=" * 60)

    return output_dir


def main():
    """主函数"""
    # 默认下载贵州茅台
    code = sys.argv[1] if len(sys.argv) > 1 else "600519"
    market = int(sys.argv[2]) if len(sys.argv) > 2 else None

    print("=" * 60)
    print("F10 数据下载工具")
    print("=" * 60)
    print()

    output_dir = download_f10_data(code, market)

    print()
    print("提示: 可以使用以下命令查看数据:")
    print(f"  dir /b \"{output_dir}\"")
    print(f"  type \"{output_dir}\\公司概况.txt\"")


if __name__ == "__main__":
    main()
