"""
ETF 和 F10 模块性能测试

测试内容:
- ETF: 连接、K线、行情、分时、逐笔、除权、财务、ETF列表
- F10: 分类列表、单分类内容、全量内容、文本解析

每项测试 5 次取平均值，统计平均/最小/最大响应时间。
"""

import time
import statistics
import sys
import io

# 修复 Windows 控制台 GBK 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 测试配置
ETF_CODE_SH = "510300"   # 沪深300ETF
ETF_CODE_SZ = "159915"   # 创业板ETF
F10_CODE = "600519"       # 贵州茅台
F10_MARKET = 1
ITERATIONS = 5
SERVER_IP = "180.153.18.170"
SERVER_PORT = 7709


def run_bench(name, func, iterations=ITERATIONS):
    """运行基准测试，返回统计结果"""
    times = []
    result = None
    for i in range(iterations):
        start = time.perf_counter()
        try:
            result = func()
            elapsed = (time.perf_counter() - start) * 1000  # ms
            times.append(elapsed)
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            print(f"  [{name}] 第{i+1}次失败: {e} ({elapsed:.1f}ms)")
            return None, None

    if not times:
        return None, None

    avg = statistics.mean(times)
    mn = min(times)
    mx = max(times)

    # 获取结果摘要
    if isinstance(result, list):
        summary = f"{len(result)} 条"
    elif isinstance(result, dict):
        summary = f"{len(result)} 项"
    elif isinstance(result, str):
        summary = f"{len(result)} 字符"
    elif isinstance(result, bool):
        summary = str(result)
    else:
        summary = str(type(result).__name__)

    return {"avg": avg, "min": mn, "max": mx, "count": len(times), "result": summary}, result


def print_result(name, stats):
    """打印测试结果"""
    if stats is None:
        print(f"  {name}: FAILED")
        return
    print(f"  {name}: avg={stats['avg']:.1f}ms  min={stats['min']:.1f}ms  max={stats['max']:.1f}ms  ({stats['result']})")


def bench_etf():
    """ETF 模块性能测试"""
    print("\n" + "=" * 60)
    print("ETF 模块性能测试")
    print("=" * 60)

    from tdxrs.pro import TdxHqEtfClient
    from tdxrs.constants import MARKET_SH, MARKET_SZ

    client = TdxHqEtfClient()

    # 连接测试
    print("\n[连接]")
    stats, _ = run_bench("connect_to_any", lambda: client.connect_to_any())
    print_result("connect_to_any", stats)

    if not client.is_connected():
        print("  连接失败，跳过后续测试")
        return

    # ETF 列表
    print("\n[ETF 列表]")
    stats, _ = run_bench("get_etf_list(SH)", lambda: client.get_etf_list(MARKET_SH))
    print_result("get_etf_list(SH)", stats)

    # K线数据
    print("\n[ETF K线]")
    stats, _ = run_bench("get_etf_bars(日线,10)", lambda: client.get_etf_bars(9, MARKET_SH, ETF_CODE_SH, 0, 10))
    print_result("get_etf_bars(日线,10)", stats)

    stats, _ = run_bench("get_etf_bars(日线,100)", lambda: client.get_etf_bars(9, MARKET_SH, ETF_CODE_SH, 0, 100))
    print_result("get_etf_bars(日线,100)", stats)

    stats, _ = run_bench("get_etf_bars(5分钟,10)", lambda: client.get_etf_bars(0, MARKET_SH, ETF_CODE_SH, 0, 10))
    print_result("get_etf_bars(5分钟,10)", stats)

    # K线自动分页
    stats, _ = run_bench("get_etf_bars_all(日线,800)", lambda: client.get_etf_bars_all(9, MARKET_SH, ETF_CODE_SH, 800))
    print_result("get_etf_bars_all(日线,800)", stats)

    # 实时行情
    print("\n[ETF 行情]")
    stats, _ = run_bench("get_etf_quotes(1只)", lambda: client.get_etf_quotes([(MARKET_SH, ETF_CODE_SH)]))
    print_result("get_etf_quotes(1只)", stats)

    stats, _ = run_bench("get_etf_quotes(2只)", lambda: client.get_etf_quotes([(MARKET_SH, ETF_CODE_SH), (MARKET_SZ, ETF_CODE_SZ)]))
    print_result("get_etf_quotes(2只)", stats)

    # 分时数据
    print("\n[ETF 分时]")
    stats, _ = run_bench("get_etf_minute_time_data", lambda: client.get_etf_minute_time_data(MARKET_SH, ETF_CODE_SH))
    print_result("get_etf_minute_time_data", stats)

    # 逐笔成交
    print("\n[ETF 逐笔]")
    stats, _ = run_bench("get_etf_transaction_data(100)", lambda: client.get_etf_transaction_data(MARKET_SH, ETF_CODE_SH, 0, 100))
    print_result("get_etf_transaction_data(100)", stats)

    # 除权除息
    print("\n[ETF 除权除息]")
    stats, _ = run_bench("get_etf_xdxr_info", lambda: client.get_etf_xdxr_info(MARKET_SH, ETF_CODE_SH))
    print_result("get_etf_xdxr_info", stats)

    # 财务信息
    print("\n[ETF 财务]")
    stats, _ = run_bench("get_etf_finance_info", lambda: client.get_etf_finance_info(MARKET_SH, ETF_CODE_SH))
    print_result("get_etf_finance_info", stats)

    client.disconnect()


def bench_f10():
    """F10 模块性能测试"""
    print("\n" + "=" * 60)
    print("F10 模块性能测试")
    print("=" * 60)

    from tdxrs.pro import TdxF10Client

    client = TdxF10Client(SERVER_IP, SERVER_PORT)

    # 分类列表
    print("\n[F10 分类列表]")
    stats, categories = run_bench("get_category", lambda: client.get_category(F10_MARKET, F10_CODE))
    print_result("get_category", stats)
    if categories:
        print(f"  分类数量: {len(categories)}")
        for cat in categories:
            print(f"    - {cat['name']}: {cat['length']} bytes")

    # 单分类内容 — 使用 get_content 直接传递分类字典
    print("\n[F10 单分类内容]")
    if categories:
        for cat in categories[:4]:  # 测试前 4 个分类
            cat_name = cat['name']
            stats, content = run_bench(
                f"get_content({cat_name})",
                lambda c=cat: client.get_content(F10_MARKET, F10_CODE, c)
            )
            print_result(f"get_content({cat_name})", stats)

    # 全量内容
    print("\n[F10 全量内容]")
    stats, all_data = run_bench("get_all_data", lambda: client.get_all_data(F10_MARKET, F10_CODE))
    print_result("get_all_data", stats)
    if all_data:
        print(f"  分类数: {all_data['category_count']}")
        print(f"  总字符: {all_data['total_chars']}")
        print(f"  总字节: {all_data['total_bytes']}")

    # 文本解析性能 (离线)
    print("\n[F10 文本解析 (离线)]")
    if categories:
        content = client.get_content(F10_MARKET, F10_CODE, categories[0])
        if content:
            stats, _ = run_bench("parse_f10(单分类)", lambda: TdxF10Client.parse_f10(content))
            print_result("parse_f10(单分类)", stats)

            stats, _ = run_bench("extract_basic_info(单分类)", lambda: TdxF10Client.extract_basic_info(content))
            print_result("extract_basic_info(单分类)", stats)

    # 解析全量数据
    if all_data and all_data['contents']:
        full_text = "\n".join(c['content'] for c in all_data['contents'])
        stats, _ = run_bench(f"parse_f10(全量 {len(full_text)} 字符)", lambda: TdxF10Client.parse_f10(full_text))
        print_result(f"parse_f10(全量 {len(full_text)} 字符)", stats)


def main():
    print("ETF / F10 模块性能测试")
    print(f"服务器: {SERVER_IP}:{SERVER_PORT}")
    print(f"每项测试 {ITERATIONS} 次取平均值")

    try:
        bench_etf()
    except Exception as e:
        print(f"\nETF 测试失败: {e}")

    try:
        bench_f10()
    except Exception as e:
        print(f"\nF10 测试失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    main()
