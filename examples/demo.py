"""
tdxrs Python 使用示例

运行方式:
    python examples/demo.py

前提:
    1. pip install tdxrs  (或 maturin develop)
    2. 需要网络连接到 TDX 服务器 (默认 218.75.126.9:7709)
"""

from tdxrs import TdxHqClient, DailyBarReader, BlockReader


def demo_local_readers():
    """本地文件解析示例 (需要 TDX 数据文件)"""
    print("=== Local File Readers ===\n")

    # 日线解析器
    reader = DailyBarReader(coefficient=0.01)
    print(f"DailyBarReader created (coefficient={reader.coefficient if hasattr(reader, 'coefficient') else 0.01})")

    # 如果有本地数据文件，可以这样使用:
    # bars = reader.parse_file("C:/tdx/v600/day/600519.day")
    # for bar in bars[:3]:
    #     print(f"  {bar['date']}: O={bar['open']:.2f} C={bar['close']:.2f}")

    # 板块解析器
    block_reader = BlockReader()
    print("BlockReader created")

    # blocks = block_reader.parse_file("C:/tdx/v600/T0002/blocknew.dat")
    # for b in blocks[:5]:
    #     print(f"  {b['blockname']}: {b['code']}")

    print()


def demo_network_client():
    """网络行情客户端示例"""
    print("=== Network Client ===\n")

    client = TdxHqClient()

    # 1. 连接
    try:
        ok = client.connect("218.75.126.9", 7709, timeout=5.0)
        if ok:
            print("[OK] Connected to 218.75.126.9:7709")
        else:
            print("[FAIL] Connection rejected")
            return
    except Exception as e:
        print(f"[ERROR] {e}")
        print("  Trying connect_to_any...")
        try:
            client.connect_to_any(timeout=5.0)
            print("[OK] Connected via failover")
        except Exception as e2:
            print(f"[FAIL] {e2}")
            return

    # 2. 证券数量
    sh_count = client.get_security_count(1)
    sz_count = client.get_security_count(0)
    print(f"\n--- Security Count ---")
    print(f"  Shanghai: {sh_count}")
    print(f"  Shenzhen: {sz_count}")

    # 3. 贵州茅台日K
    print(f"\n--- 600519 Daily K-line (last 5) ---")
    try:
        bars = client.get_security_bars(category=4, market=1, code="600519", start=0, count=5)
        for bar in bars:
            print(f"  {bar['datetime']}: O={bar['open']:.2f} C={bar['close']:.2f} H={bar['high']:.2f} L={bar['low']:.2f}")
    except Exception as e:
        print(f"  Error: {e}")

    # 4. 自动分页获取 (超过800条)
    print(f"\n--- 600519 Daily K-line (auto-paginate, 1000 bars) ---")
    try:
        bars = client.get_security_bars_all(category=4, market=1, code="600519", count=1000)
        print(f"  Fetched {len(bars)} bars")
        if bars:
            # bars are chronological (oldest→newest); bars[0]=earliest, bars[-1]=latest
            print(f"  Earliest: {bars[0]['datetime']}")
            print(f"  Latest:   {bars[-1]['datetime']}")
    except Exception as e:
        print(f"  Error: {e}")

    # 5. 实时行情
    print(f"\n--- Real-time Quotes ---")
    try:
        quotes = client.get_security_quotes([(1, "600519"), (0, "000858")])
        for q in quotes:
            print(f"  {q['code']}: Price={q['price']:.2f} Vol={q['vol']:.0f} Amount={q['amount']:.0f}")
    except Exception as e:
        print(f"  Error: {e}")

    # 6. 分时数据
    print(f"\n--- 000001 Intraday (first 5 ticks) ---")
    try:
        data = client.get_minute_time_data(market=1, code="000001")
        for d in data[:5]:
            print(f"  Price={d['price']:.2f} Vol={d['vol']:.0f}")
        print(f"  ... total {len(data)} ticks")
    except Exception as e:
        print(f"  Error: {e}")

    # 7. 逐笔成交
    print(f"\n--- 600519 Ticks (first 5) ---")
    try:
        ticks = client.get_transaction_data(market=1, code="600519", start=0, count=5)
        for t in ticks:
            direction = "B" if t['buyorsell'] == 0 else "S"
            print(f"  {t['time']} Price={t['price']:.2f} Vol={t['vol']:.0f} [{direction}]")
    except Exception as e:
        print(f"  Error: {e}")

    # 8. 财务信息
    print(f"\n--- 600519 Finance Info ---")
    try:
        info = client.get_finance_info(market=1, code="600519")
        print(f"  Total shares: {info['zongguben']:.0f}")
        print(f"  Net assets:   {info['jingzichan']:.0f}")
        print(f"  Revenue:      {info['zhuyingshouru']:.0f}")
        print(f"  Net profit:   {info['jinglirun']:.0f}")

        print( info)

    except Exception as e:
        print(f"  Error: {e}")

    # 9. 连接池状态
    stats = client.pool_stats()
    print(f"\n--- Pool Stats ---")
    print(f"  idle={stats['idle']} active={stats['active']} total={stats['total']} max={stats['max_size']}")

    # 10. 断开
    client.disconnect()
    print(f"\n[OK] Disconnected")


if __name__ == "__main__":
    # demo_local_readers()
    demo_network_client()
