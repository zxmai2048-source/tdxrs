"""
从 golden reference (JSON) 生成二进制测试文件
用于验证 Rust Reader 的解析正确性
"""
import json
import struct
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
FIXTURE_DIR = SCRIPT_DIR / "fixtures"
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

GOLDEN_DIR = SCRIPT_DIR / ".." / ".." / "tdxpy" / "test_data" / "golden"

U32_MAX = 4294967295


def filter_valid_records(data: list) -> list:
    """过滤无效记录: 年月日不合理或数值溢出的记录"""
    valid = []
    skipped = 0
    for bar in data:
        year = bar.get("year", 0)
        month = bar.get("month", 0)
        day = bar.get("day", 0)
        volume = bar.get("volume", 0)
        amount = bar.get("amount", 0)
        open_p = bar.get("open", 0)
        high_p = bar.get("high", 0)
        low_p = bar.get("low", 0)
        close_p = bar.get("close", 0)

        if not (1990 <= year <= 2100):
            skipped += 1
            continue
        if not (1 <= month <= 12):
            skipped += 1
            continue
        if not (1 <= day <= 31):
            skipped += 1
            continue
        if volume > U32_MAX or volume < 0:
            skipped += 1
            continue
        if amount > 1e15 or amount < 0:
            skipped += 1
            continue
        # 价格必须为正数且合理 (A股价格 0~100000)
        for price in [open_p, high_p, low_p, close_p]:
            if price <= 0 or price > 100000:
                skipped += 1
                break
        else:
            valid.append(bar)
            continue

    if skipped > 0:
        print(f"    过滤掉 {skipped} 条无效记录")
    return valid


def encode_tdx_date(year, month, day):
    """编码 TDX 日期: (year-2004)*2048 + month*100 + day"""
    return (year - 2004) * 2048 + month * 100 + day


def gen_day_files():
    """从 golden reference 生成 .day 二进制文件"""
    print("=== 生成 .day 测试文件 ===")
    for f in sorted(GOLDEN_DIR.glob("bars_*_cat9_*.json")):
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)

        code = f.stem.split("_")[1]  # e.g. "600519"
        data = filter_valid_records(data)
        if not data:
            print(f"  {code}.day: 跳过 (无有效记录)")
            continue

        day_file = FIXTURE_DIR / f"{code}.day"

        with open(day_file, "wb") as out:
            for bar in data:
                date_num = encode_tdx_date(bar["year"], bar["month"], bar["day"])
                # A股系数 0.01: open_raw = open / 0.01 = open * 100
                open_raw = int(round(bar["open"] * 100))
                high_raw = int(round(bar["high"] * 100))
                low_raw = int(round(bar["low"] * 100))
                close_raw = int(round(bar["close"] * 100))
                amount = float(bar["amount"])
                volume = int(bar["volume"])

                out.write(struct.pack("<IIIIIfII",
                    date_num, open_raw, high_raw, low_raw, close_raw,
                    float(amount), volume, 0))

        size = day_file.stat().st_size
        records = len(data)
        print(f"  {code}.day: {records} 条, {size} bytes")

        # 验证: 读回来对比
        verify_day_file(day_file, data, code)


def verify_day_file(day_file, golden_data, code):
    """验证二进制文件与 golden reference 一致"""
    with open(day_file, "rb") as f:
        content = f.read()

    record_size = 32
    num_records = len(content) // record_size

    assert num_records == len(golden_data), \
        f"{code}: 记录数不匹配 {num_records} vs {len(golden_data)}"

    for i in range(min(3, num_records)):  # 检查前3条
        offset = i * record_size
        date_num = struct.unpack_from("<I", content, offset)[0]
        open_raw = struct.unpack_from("<I", content, offset + 4)[0]

        year = date_num // 2048 + 2004
        month = (date_num % 2048) // 100
        day = (date_num % 2048) % 100
        open_val = open_raw * 0.01

        g = golden_data[i]
        assert year == g["year"], f"{code}[{i}]: year {year} != {g['year']}"
        assert month == g["month"], f"{code}[{i}]: month {month} != {g['month']}"
        assert day == g["day"], f"{code}[{i}]: day {day} != {g['day']}"
        assert abs(open_val - g["open"]) < 0.02, \
            f"{code}[{i}]: open {open_val} != {g['open']}"

    print(f"    验证通过: {code} 前3条匹配")


def gen_min5_files():
    """从 golden reference 生成 5分钟线 .lc5 文件"""
    print("\n=== 生成 .lc5 测试文件 ===")
    for f in sorted(GOLDEN_DIR.glob("bars_*_cat0_*.json")):
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)

        code = f.stem.split("_")[1]
        data = filter_valid_records(data)
        if not data:
            print(f"  {code}.lc5: 跳过 (无有效记录)")
            continue

        lc5_file = FIXTURE_DIR / f"{code}.lc5"

        with open(lc5_file, "wb") as out:
            for bar in data:
                date_num = encode_tdx_date(bar["year"], bar["month"], bar["day"])
                time_num = bar["hour"] * 60 + bar["minute"]
                open_raw = int(round(bar["open"] * 100))
                high_raw = int(round(bar["high"] * 100))
                low_raw = int(round(bar["low"] * 100))
                close_raw = int(round(bar["close"] * 100))
                amount = float(bar["amount"])
                volume = int(bar["volume"])

                out.write(struct.pack("<HHIIIIfII",
                    date_num & 0xFFFF, time_num & 0xFFFF,
                    open_raw, high_raw, low_raw, close_raw,
                    float(amount), volume, 0))

        size = lc5_file.stat().st_size
        print(f"  {code}.lc5: {len(data)} 条, {size} bytes")


def gen_min1_files():
    """从 golden reference 生成 1分钟线 .lc1 文件 (整数格式)"""
    print("\n=== 生成 .lc1 测试文件 ===")
    for f in sorted(GOLDEN_DIR.glob("bars_*_cat8_*.json")):
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)

        code = f.stem.split("_")[1]
        data = filter_valid_records(data)
        if not data:
            print(f"  {code}_1min.lc1: 跳过 (无有效记录)")
            continue

        lc1_file = FIXTURE_DIR / f"{code}_1min.lc1"

        with open(lc1_file, "wb") as out:
            for bar in data:
                date_num = encode_tdx_date(bar["year"], bar["month"], bar["day"])
                time_num = bar["hour"] * 60 + bar["minute"]
                open_raw = int(round(bar["open"] * 100))
                high_raw = int(round(bar["high"] * 100))
                low_raw = int(round(bar["low"] * 100))
                close_raw = int(round(bar["close"] * 100))
                amount = float(bar["amount"])
                volume = int(bar["volume"])

                out.write(struct.pack("<HHIIIIfII",
                    date_num & 0xFFFF, time_num & 0xFFFF,
                    open_raw, high_raw, low_raw, close_raw,
                    float(amount), volume, 0))

        size = lc1_file.stat().st_size
        print(f"  {code}_1min.lc1: {len(data)} 条, {size} bytes")


def gen_block_file():
    """构造板块测试文件"""
    print("\n=== 生成板块测试文件 ===")
    block_file = FIXTURE_DIR / "test_block.dat"

    # 构造简单的板块数据
    # 文件头 384 字节 (全0)
    header = b'\x00' * 384

    # 板块数量: 2
    num_blocks = 2

    # 板块1: "测试板块" (GBK编码)
    block1_name = "测试板块".encode("gbk").ljust(9, b'\x00')
    block1_count = 3
    block1_type = 1
    # 股票代码: 600000, 000001, 300750
    codes1 = [b'600000\x00', b'000001\x00', b'300750\x00']
    codes1_block = b''.join(codes1).ljust(2800, b'\x00')

    # 板块2: "指数板块"
    block2_name = "指数板块".encode("gbk").ljust(9, b'\x00')
    block2_count = 2
    block2_type = 2
    codes2 = [b'000001\x00', b'399001\x00']
    codes2_block = b''.join(codes2).ljust(2800, b'\x00')

    with open(block_file, "wb") as out:
        out.write(header)
        out.write(struct.pack("<H", num_blocks))
        # 板块1
        out.write(block1_name)
        out.write(struct.pack("<HH", block1_count, block1_type))
        out.write(codes1_block)
        # 板块2
        out.write(block2_name)
        out.write(struct.pack("<HH", block2_count, block2_type))
        out.write(codes2_block)

    size = block_file.stat().st_size
    print(f"  test_block.dat: {num_blocks} 个板块, {size} bytes")


def gen_financial_file():
    """构造财务数据测试文件"""
    print("\n=== 生成财务测试文件 ===")
    fin_file = FIXTURE_DIR / "test_finance.dat"

    # 财务数据格式:
    # Header (16 bytes): <1hI1H3L>
    #   i16: record_type
    #   u32: report_date
    #   u16: max_count (股票数量)
    #   u32: reserved
    #   u32: report_size (每只股票报告字段总字节数)
    #   u32: reserved
    #
    # Stock Index (11 bytes each): <6s1c1L>
    #   [u8; 6]: stock code
    #   u8: separator (0x00)
    #   u32: file offset to report data
    #
    # Report Data: report_size/4 little-endian f32 values

    stocks = [
        ("600519", [1835.0, 1849.98, 1807.82, 1841.2]),  # 茅台
        ("000858", [150.5, 155.0, 148.0, 152.3]),         # 五粮液
    ]

    report_size = len(stocks[0][1]) * 4  # 4 floats × 4 bytes = 16 bytes
    max_count = len(stocks)

    # Header
    header = struct.pack("<hI1H3L", 1, 20241231, max_count, 0, report_size, 0)

    # Calculate offsets
    header_size = 20  # <hI1H3L> = 2+4+2+12 = 20 bytes
    index_size = 11 * max_count
    report_offset_1 = header_size + index_size
    report_offset_2 = report_offset_1 + report_size

    with open(fin_file, "wb") as out:
        out.write(header)

        # Stock index
        for i, (code, _) in enumerate(stocks):
            code_bytes = code.encode("utf-8").ljust(6, b'\x00')[:6]
            out.write(code_bytes)
            out.write(b'\x00')  # separator
            offset = report_offset_1 + i * report_size
            out.write(struct.pack("<I", offset))

        # Report data
        for _, fields in stocks:
            for val in fields:
                out.write(struct.pack("<f", val))

    size = fin_file.stat().st_size
    print(f"  test_finance.dat: {max_count} stocks, {size} bytes")


if __name__ == "__main__":
    gen_day_files()
    gen_min5_files()
    gen_min1_files()
    gen_block_file()
    gen_financial_file()
    print("\n所有测试文件生成完成!")
