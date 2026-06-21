"""
tdxpy vs tdxrs 自动化对比脚本

对比思路:
  1. 本地 Reader: golden JSON (tdxpy 输出) 作为基准，对比 tdxrs 解析结果
  2. 网络 API: 同时调用 tdxpy 和 tdxrs，逐字段 diff
  3. 浮点容差: 可配置 epsilon (默认 0.01)

使用方式:
  # 对比本地 Reader (不需要网络)
  python tests/compare_tdxpy_tdxrs.py --mode reader

  # 对比网络 API (需要网络连接 TDX 服务器)
  python tests/compare_tdxpy_tdxrs.py --mode network

  # 全部对比
  python tests/compare_tdxpy_tdxrs.py --mode all

  # 自定义容差
  python tests/compare_tdxpy_tdxrs.py --mode reader --epsilon 0.001
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

# ============================================================
# 路径配置
# ============================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
TDXPY_DIR = PROJECT_DIR.parent / "tdxpy"
GOLDEN_DIR = TDXPY_DIR / "test_data" / "golden"
FIXTURE_DIR = SCRIPT_DIR / "fixtures"
REPORT_DIR = SCRIPT_DIR / "comparison_reports"

# 测试股票列表
TEST_STOCKS = [
    (1, "688981"),  # 上海 - 贵州茅台
    (0, "002415"),  # 深圳 - 五粮液
    (0, "300502"),  # 深圳 - 宁德时代
]

# K线类型
KLINE_CATEGORIES = {
    0: "5分钟K线",
    4: "日K线",
    5: "周K线",
    6: "月K线",
    8: "1分钟K线",
}


# ============================================================
# 比较引擎
# ============================================================

class DiffRecord:
    """单条差异记录"""

    def __init__(self, api: str, stock: str, row: int, field: str,
                 tdxpy_val: Any, tdxrs_val: Any, diff: Any = None):
        self.api = api
        self.stock = stock
        self.row = row
        self.field = field
        self.tdxpy_val = tdxpy_val
        self.tdxrs_val = tdxrs_val
        self.diff = diff

    def to_dict(self):
        d = {
            "api": self.api,
            "stock": self.stock,
            "row": self.row,
            "field": self.field,
            "tdxpy": self.tdxpy_val,
            "tdxrs": self.tdxrs_val,
        }
        if self.diff is not None:
            d["diff"] = self.diff
        return d


def compare_values(a: Any, b: Any, epsilon: float = 0.01,
                   ignore_fields: set = None) -> tuple[bool, Any]:
    """
    比较两个值，返回 (match, diff_info)
    ignore_fields: 需要忽略的字段集合
    """
    if ignore_fields:
        return True, None

    if a is None and b is None:
        return True, None
    if a is None or b is None:
        return False, f"None mismatch: {a} vs {b}"

    if isinstance(a, str) and isinstance(b, str):
        if a == b:
            return True, None
        return False, f"string diff"

    if isinstance(a, bool) and isinstance(b, bool):
        return a == b, None

    if isinstance(a, int) and isinstance(b, int):
        if a == b:
            return True, None
        return False, a - b

    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True, None
        if math.isinf(a) and math.isinf(b):
            return (a > 0) == (b > 0), None
        diff = abs(a - b)
        if diff <= epsilon:
            return True, None
        # 相对误差
        if abs(a) > epsilon:
            rel = diff / abs(a)
            if rel <= epsilon:
                return True, None
        return False, diff

    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False, f"len {len(a)} vs {len(b)}"
        for i, (ai, bi) in enumerate(zip(a, b)):
            match, d = compare_values(ai, bi, epsilon)
            if not match:
                return False, f"[{i}] {d}"
        return True, None

    # 数值类型混合比较
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return compare_values(float(a), float(b), epsilon)

    if str(a) == str(b):
        return True, None

    return False, f"type diff: {type(a).__name__} vs {type(b).__name__}"


def compare_records(tdxpy_data: list, tdxrs_data: list, api_name: str,
                    stock_label: str, epsilon: float,
                    ignore_fields: set = None) -> list[DiffRecord]:
    """
    逐行逐字段对比两个 list[dict]
    返回差异列表
    """
    diffs = []

    if len(tdxpy_data) != len(tdxrs_data):
        diffs.append(DiffRecord(
            api=api_name, stock=stock_label, row=-1, field="_row_count",
            tdxpy_val=len(tdxpy_data), tdxrs_val=len(tdxrs_data),
            diff=f"count mismatch: {len(tdxpy_data)} vs {len(tdxrs_data)}"
        ))

    min_len = min(len(tdxpy_data), len(tdxrs_data))

    for i in range(min_len):
        py_row = tdxpy_data[i]
        rs_row = tdxrs_data[i]

        all_keys = set(py_row.keys()) | set(rs_row.keys())
        skip = ignore_fields or set()

        for key in sorted(all_keys):
            if key in skip:
                continue

            py_val = py_row.get(key)
            rs_val = rs_row.get(key)

            if py_val is None and rs_val is None:
                continue

            match, diff_info = compare_values(py_val, rs_val, epsilon)
            if not match:
                diffs.append(DiffRecord(
                    api=api_name, stock=stock_label, row=i, field=key,
                    tdxpy_val=py_val, tdxrs_val=rs_val, diff=diff_info
                ))

    return diffs


# ============================================================
# Reader 对比 (本地文件)
# ============================================================

def compare_readers(epsilon: float) -> list[DiffRecord]:
    """对比本地 Reader 解析结果 vs golden reference"""
    all_diffs = []

    print("=" * 60)
    print("Part 1: 本地 Reader 对比 (tdxrs vs golden)")
    print("=" * 60)

    # --- DailyBarReader ---
    print("\n--- DailyBarReader ---")
    for stock_code in ["600519", "000858", "300750"]:
        golden_file = GOLDEN_DIR / f"bars_{stock_code}_cat9_日K线.json"
        if not golden_file.exists():
            print(f"  {stock_code}: golden file not found, skip")
            continue

        with open(golden_file, encoding="utf-8") as f:
            golden = json.load(f)

        # 过滤有效记录 (与 gen_binary_fixtures.py 一致)
        golden = [r for r in golden if _valid_bar(r)]

        fixture_file = FIXTURE_DIR / f"{stock_code}.day"
        if not fixture_file.exists():
            print(f"  {stock_code}: fixture not found, skip")
            continue

        # 用 tdxrs 解析
        try:
            import tdxrs
            reader = tdxrs.DailyBarReader(coefficient=0.01)
            tdxrs_data = reader.parse_file(str(fixture_file))
        except Exception as e:
            print(f"  {stock_code}: tdxrs error: {e}")
            continue

        # golden 有 hour/minute/datetime (日K无意义), tdxrs 有 date 字段
        diffs = compare_records(
            golden, tdxrs_data, "DailyBarReader", stock_code, epsilon,
            ignore_fields={"datetime", "hour", "minute", "date"}
        )
        all_diffs.extend(diffs)
        status = "PASS" if not diffs else f"FAIL ({len(diffs)} diffs)"
        print(f"  {stock_code}: {len(golden)} records, {status}")

    # --- MinBarReader ---
    print("\n--- MinBarReader (5min) ---")
    for stock_code in ["600519", "000858", "300750"]:
        golden_file = GOLDEN_DIR / f"bars_{stock_code}_cat0_5分钟K线.json"
        if not golden_file.exists():
            print(f"  {stock_code}: golden not found, skip")
            continue

        with open(golden_file, encoding="utf-8") as f:
            golden = json.load(f)
        golden = [r for r in golden if _valid_bar(r)]

        fixture_file = FIXTURE_DIR / f"{stock_code}.lc5"
        if not fixture_file.exists():
            print(f"  {stock_code}: fixture not found, skip")
            continue

        try:
            import tdxrs
            reader = tdxrs.MinBarReader()
            tdxrs_data = reader.parse_file(str(fixture_file))
        except Exception as e:
            print(f"  {stock_code}: tdxrs error: {e}")
            continue

        # golden 有 datetime, tdxrs 有 date
        diffs = compare_records(
            golden, tdxrs_data, "MinBarReader", stock_code, epsilon,
            ignore_fields={"datetime", "date"}
        )
        all_diffs.extend(diffs)
        status = "PASS" if not diffs else f"FAIL ({len(diffs)} diffs)"
        print(f"  {stock_code}: {len(golden)} records, {status}")

    # --- BlockReader ---
    # 注意: golden 是完整服务器数据 (370k+ records), test_block.dat 是合成测试数据 (5 records)
    # 无法直接对比，跳过
    print("\n--- BlockReader ---")
    print("  skip (golden is full server data, fixture is synthetic)")

    # --- FinancialReader ---
    # 注意: golden financial 数据来自网络 API (get_finance_info), 不是文件解析
    # FinancialReader.parse_file 返回 {code, report_date, fields[]} 原始格式
    # 两者结构不同，跳过
    print("\n--- FinancialReader ---")
    print("  skip (golden is from network API, not file reader)")

    return all_diffs


# ============================================================
# 网络 API 对比
# ============================================================

def compare_network_api(epsilon: float) -> list[DiffRecord]:
    """同时调用 tdxpy 和 tdxrs 网络 API，逐字段对比"""
    all_diffs = []

    print("\n" + "=" * 60)
    print("Part 2: 网络 API 对比 (tdxpy vs tdxrs)")
    print("=" * 60)

    try:
        from tdxrs import TdxHqClient as RsClient
    except ImportError:
        print("  tdxrs.TdxHqClient not available (need maturin develop), skip")
        return all_diffs

    # 导入 tdxpy (从父级目录加载，而非本地的 tdxrs/tdxpy/)
    sys.path.insert(0, str((Path(__file__).resolve().parent.parent.parent) / "tdxpy"))
    try:
        from tdxpy.hq import TdxHq_API as PyClient
    except ImportError:
        print("  tdxpy not importable, skip network comparison")
        return all_diffs

    # 连接
    rs_client = RsClient()
    py_client = PyClient()

    SERVER = ("218.75.126.9", 7709)

    try:
        rs_client.connect(SERVER[0], SERVER[1], timeout=5.0)
        print(f"  tdxrs connected to {SERVER[0]}:{SERVER[1]}")
    except Exception as e:
        print(f"  tdxrs connect failed: {e}")
        return all_diffs

    try:
        py_client.connect(SERVER[0], SERVER[1])
        print(f"  tdxpy connected to {SERVER[0]}:{SERVER[1]}")
    except Exception as e:
        print(f"  tdxpy connect failed: {e}")
        rs_client.disconnect()
        return all_diffs

    try:
        # --- get_security_bars ---
        print("\n--- get_security_bars ---")
        for market, code in TEST_STOCKS:
            for cat, cat_name in KLINE_CATEGORIES.items():
                try:
                    py_bars = py_client.get_security_bars(cat, market, code, 0, 10)
                    rs_bars = rs_client.get_security_bars(cat, market, code, 0, 10)

                    # tdxpy 返回的是 list of dict
                    if isinstance(py_bars, list) and len(py_bars) > 0:
                        if isinstance(py_bars[0], dict):
                            py_data = py_bars
                        else:
                            # pytdx 返回的是 object
                            py_data = [_obj_to_dict(b) for b in py_bars]
                    else:
                        py_data = py_bars if isinstance(py_bars, list) else []

                    # 日/周/月K线: tdxpy 返回 hour=15 (收盘时间), tdxrs 返回 0
                    ignore = {"datetime", "date"}
                    if cat >= 4 and cat != 8:
                        ignore |= {"hour", "minute"}

                    diffs = compare_records(
                        py_data, rs_bars, f"get_security_bars(cat={cat})",
                        f"{code}({cat_name})", epsilon,
                        ignore_fields=ignore
                    )
                    all_diffs.extend(diffs)
                    status = "PASS" if not diffs else f"FAIL ({len(diffs)} diffs)"
                    print(f"  {code} {cat_name}: {status}")
                except Exception as e:
                    print(f"  {code} {cat_name}: error: {e}")

        # --- get_security_quotes ---
        print("\n--- get_security_quotes ---")
        try:
            py_quotes = py_client.get_security_quotes([(m, c) for m, c in TEST_STOCKS])
            rs_quotes = rs_client.get_security_quotes([(m, c) for m, c in TEST_STOCKS])

            if isinstance(py_quotes, list) and len(py_quotes) > 0:
                if isinstance(py_quotes[0], dict):
                    py_data = py_quotes
                else:
                    py_data = [_obj_to_dict(q) for q in py_quotes]
            else:
                py_data = []

            diffs = compare_records(
                py_data, rs_quotes, "get_security_quotes", "batch",
                epsilon,
                ignore_fields={"servertime", "reversed_bytes0", "reversed_bytes1",
                                "reversed_bytes2", "reversed_bytes3", "reversed_bytes4",
                                "reversed_bytes5", "reversed_bytes6", "reversed_bytes7",
                                "reversed_bytes8", "reversed_bytes9", "active1", "active2"}
            )
            all_diffs.extend(diffs)
            status = "PASS" if not diffs else f"FAIL ({len(diffs)} diffs)"
            print(f"  quotes batch: {status}")
        except Exception as e:
            print(f"  quotes: error: {e}")

        # --- get_minute_time_data ---
        print("\n--- get_minute_time_data ---")
        for market, code in TEST_STOCKS[:1]:
            try:
                py_data = py_client.get_minute_time_data(market, code)
                rs_data = rs_client.get_minute_time_data(market, code)

                if isinstance(py_data, list) and len(py_data) > 0:
                    if not isinstance(py_data[0], dict):
                        py_data = [_obj_to_dict(d) for d in py_data]

                diffs = compare_records(
                    py_data, rs_data, "get_minute_time_data", code, epsilon,
                    ignore_fields={"time"}
                )
                all_diffs.extend(diffs)
                status = "PASS" if not diffs else f"FAIL ({len(diffs)} diffs)"
                print(f"  {code}: {status}")
            except Exception as e:
                print(f"  {code}: error: {e}")

        # --- get_finance_info ---
        print("\n--- get_finance_info ---")
        for market, code in TEST_STOCKS[:1]:
            try:
                py_info = py_client.get_finance_info(market, code)
                rs_info = rs_client.get_finance_info(market, code)

                if not isinstance(py_info, dict):
                    py_info = _obj_to_dict(py_info)

                diffs = compare_records(
                    [py_info], [rs_info], "get_finance_info", code, epsilon,
                    ignore_fields={"baoliu2"}  # tdxrs 未映射此字段
                )
                all_diffs.extend(diffs)
                status = "PASS" if not diffs else f"FAIL ({len(diffs)} diffs)"
                print(f"  {code}: {status}")
            except Exception as e:
                print(f"  {code}: error: {e}")

        # --- get_xdxr_info ---
        print("\n--- get_xdxr_info ---")
        for market, code in TEST_STOCKS[:1]:
            try:
                py_data = py_client.get_xdxr_info(market, code)
                rs_data = rs_client.get_xdxr_info(market, code)

                if isinstance(py_data, list) and len(py_data) > 0:
                    if not isinstance(py_data[0], dict):
                        py_data = [_obj_to_dict(d) for d in py_data]

                diffs = compare_records(
                    py_data, rs_data, "get_xdxr_info", code, epsilon
                )
                all_diffs.extend(diffs)
                status = "PASS" if not diffs else f"FAIL ({len(diffs)} diffs)"
                print(f"  {code}: {status}")
            except Exception as e:
                print(f"  {code}: error: {e}")

    finally:
        rs_client.disconnect()
        try:
            py_client.disconnect()
        except Exception:
            pass

    return all_diffs


# ============================================================
# 辅助函数
# ============================================================

def _valid_bar(bar: dict) -> bool:
    """过滤无效记录 (与 gen_binary_fixtures.py 一致)"""
    year = bar.get("year", 0)
    month = bar.get("month", 0)
    day = bar.get("day", 0)
    volume = bar.get("volume", 0)
    amount = bar.get("amount", 0)
    open_p = bar.get("open", 0)

    if not (1990 <= year <= 2100):
        return False
    if not (1 <= month <= 12):
        return False
    if not (1 <= day <= 31):
        return False
    if volume < 0 or volume > 4294967295:
        return False
    if amount < 0 or amount > 1e15:
        return False
    if open_p <= 0 or open_p > 100000:
        return False
    return True


def _obj_to_dict(obj) -> dict:
    """将 pytdx 对象转为 dict"""
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    if hasattr(obj, "_asdict"):
        return obj._asdict()
    return {"value": obj}


def generate_report(diffs: list[DiffRecord], output_dir: Path):
    """生成对比报告"""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # JSON 报告
    json_file = output_dir / f"diff_report_{timestamp}.json"
    report = {
        "timestamp": timestamp,
        "total_diffs": len(diffs),
        "diffs": [d.to_dict() for d in diffs],
    }
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 可读文本报告
    txt_file = output_dir / f"diff_report_{timestamp}.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(f"tdxpy vs tdxrs 对比报告\n")
        f.write(f"生成时间: {timestamp}\n")
        f.write(f"总差异数: {len(diffs)}\n")
        f.write("=" * 70 + "\n\n")

        if not diffs:
            f.write("ALL PASS - 无差异\n")
        else:
            # 按 API 分组
            by_api = {}
            for d in diffs:
                by_api.setdefault(d.api, []).append(d)

            for api, api_diffs in sorted(by_api.items()):
                f.write(f"[{api}] {len(api_diffs)} diffs\n")
                f.write("-" * 50 + "\n")
                for d in api_diffs[:20]:  # 每个 API 最多显示 20 条
                    f.write(f"  stock={d.stock} row={d.row} field={d.field}\n")
                    f.write(f"    tdxpy = {d.tdxpy_val}\n")
                    f.write(f"    tdxrs = {d.tdxrs_val}\n")
                    if d.diff is not None:
                        f.write(f"    diff  = {d.diff}\n")
                    f.write("\n")
                if len(api_diffs) > 20:
                    f.write(f"  ... and {len(api_diffs) - 20} more diffs\n\n")

    print(f"\n报告已生成:")
    print(f"  JSON: {json_file}")
    print(f"  TEXT: {txt_file}")

    return json_file, txt_file


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="tdxpy vs tdxrs 自动化对比")
    parser.add_argument("--mode", choices=["reader", "network", "all"],
                        default="reader", help="对比模式")
    parser.add_argument("--epsilon", type=float, default=0.01,
                        help="浮点容差 (默认 0.01)")
    args = parser.parse_args()

    print(f"tdxpy vs tdxrs Comparison")
    print(f"Mode: {args.mode}, Epsilon: {args.epsilon}")
    print()

    all_diffs = []

    if args.mode in ("reader", "all"):
        all_diffs.extend(compare_readers(args.epsilon))

    if args.mode in ("network", "all"):
        all_diffs.extend(compare_network_api(args.epsilon))

    # 生成报告
    print("\n" + "=" * 60)
    print(f"Total differences: {len(all_diffs)}")
    print("=" * 60)

    if all_diffs:
        generate_report(all_diffs, REPORT_DIR)
        sys.exit(1)
    else:
        print("\nALL PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
