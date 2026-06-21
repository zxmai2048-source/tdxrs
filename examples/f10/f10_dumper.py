# -*- coding: utf-8 -*-
# @Time    : 2026/3/24 
# @File    : f10_dumper.py
# @Project : Alkaid-main
# @Author  : Chiang Tao
# @Version : 0.1.00
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
F10 数据采集器：将 F10 各键的原始内容保存到文件。
用于离线分析，方便确认各键的实际格式。
"""

import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from alkaid.collect.tdx.quotes import StdQuotes
from alkaid.paths import get_path_manager


def sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符，仅保留字母数字、下划线、连字符和中文"""
    import re
    # 允许中文、字母、数字、下划线、连字符
    return re.sub(r'[^\w\u4e00-\u9fa5-]', '_', name)


def dump_f10(symbol: str, output_dir: Path = None) -> Dict[str, Path]:
    """
    获取 F10 数据并保存到文件
    :param symbol: 股票代码
    :param output_dir: 输出目录，默认使用路径管理器的 data_dir/f10_dump/{symbol}
    :return: 保存的文件路径字典 {键名: 文件路径}
    """
    if output_dir is None:
        pm = get_path_manager()
        output_dir = pm.get_data_path("f10_dump") / symbol

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"保存目录: {output_dir}")

    quotes = StdQuotes()
    print(f"正在获取 {symbol} F10 数据...")
    f10_data = quotes.F10(symbol)

    if not f10_data:
        print("未获取到数据")
        return {}

    if not isinstance(f10_data, dict):
        print("F10 返回的不是字典结构，无法按键保存")
        # 保存为单个文件
        filepath = output_dir / f"{symbol}_full.txt"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f10_data)
        print(f"已保存完整内容到 {filepath}")
        return {"full": filepath}

    saved_files = {}
    index_lines = []

    for key, content in f10_data.items():
        # 清理键名作为文件名
        filename = sanitize_filename(key) + ".txt"
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        saved_files[key] = filepath
        size_kb = len(content.encode('utf-8')) / 1024
        index_lines.append(f"{key:15s}  {filepath.name}  {len(content):8d} 字符  {size_kb:.2f} KB")

        # 可选：打印前几行预览
        preview = content.split('\n')[:3]
        print(f"保存 {key} -> {filepath.name} ({len(content)} 字符)")
        for line in preview:
            if line.strip():
                print(f"    {line[:80]}...")
        print()

    # 保存索引文件
    index_path = output_dir / "index.txt"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(f"股票代码: {symbol}\n")
        f.write(f"保存时间: {Path(__file__).stat().st_ctime}\n")
        f.write("=" * 60 + "\n")
        f.write("键名           文件                   字符数      大小\n")
        f.write("-" * 60 + "\n")
        f.write("\n".join(index_lines))
    print(f"索引文件已保存: {index_path}")

    return saved_files


if __name__ == "__main__":
    # 使用示例
    symbol = input("请输入股票代码（如 002444）: ").strip()
    if not symbol:
        symbol = "603993"
    dump_f10(symbol)