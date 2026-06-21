"""
ETF 模块功能测试
验证新创建的 TdxHqEtfClient 类的功能
"""
import sys
sys.path.insert(0, "E:\\claudeProjects\\tdxrs")

from tdxrs.pro import TdxHqEtfClient
from tdxrs.constants import MARKET_SH, MARKET_SZ, KLINE_DAILY

def test_etf_client_creation():
    """测试 ETF 客户端创建"""
    print("[1] Test ETF client creation...")
    client = TdxHqEtfClient()
    assert not client.is_connected()
    print("    OK: Client created successfully")

def test_is_etf_static():
    """测试 is_etf 静态方法"""
    print("[2] Test is_etf static method...")
    assert TdxHqEtfClient.is_etf(MARKET_SH, "510300")
    assert TdxHqEtfClient.is_etf(MARKET_SZ, "159915")
    assert not TdxHqEtfClient.is_etf(MARKET_SH, "600519")
    assert not TdxHqEtfClient.is_etf(MARKET_SZ, "000858")
    print("    OK: is_etf works correctly")

def test_auto_market_code():
    """测试 auto_market_code 静态方法"""
    print("[3] Test auto_market_code static method...")
    assert TdxHqEtfClient.auto_market_code("510300") == MARKET_SH
    assert TdxHqEtfClient.auto_market_code("159915") == MARKET_SZ
    assert TdxHqEtfClient.auto_market_code("600519") == MARKET_SH
    print("    OK: auto_market_code works correctly")

def test_etf_connection():
    """测试连接"""
    print("[4] Test ETF client connection...")
    client = TdxHqEtfClient()
    if client.connect_to_any(timeout=5.0):
        print("    OK: Connected to server")
        return client
    else:
        print("    WARN: Connection failed")
        return None

def test_etf_list(client):
    """测试 ETF 列表获取"""
    client = TdxHqEtfClient()
    if client.connect_to_any( timeout=5.0 ):
        print( "    OK: Connected to server" )
        return client
    print("[5] Test ETF list...")
    sh_etfs = client.get_etf_list(MARKET_SH)
    print(f"    SH ETFs: {len(sh_etfs)}")
    if sh_etfs:
        print(f"    Sample: {sh_etfs[0]['code']} - {sh_etfs[0]['name']}")

    sz_etfs = client.get_etf_list(MARKET_SZ)
    print(f"    SZ ETFs: {len(sz_etfs)}")
    if sz_etfs:
        print(f"    Sample: {sz_etfs[0]['code']} - {sz_etfs[0]['name']}")
    print("    OK: ETF list retrieved")

def test_etf_bars(client):
    """测试 ETF K线"""
    print("[6] Test ETF K-line...")
    client = TdxHqEtfClient()
    if client.connect_to_any( timeout=5.0 ):
        print( "    OK: Connected to server" )
        return client
    bars = client.get_etf_bars(KLINE_DAILY, MARKET_SH, "510300", 0, 5)
    if bars:
        print(f"    OK: Got {len(bars)} bars")
        b = bars[0]
        print(f"    Latest: {b['datetime']} O={b['open']:.3f} C={b['close']:.3f}")
    else:
        print("    WARN: No bars returned")

def test_etf_quotes(client):
    """测试 ETF 实时行情"""
    print("[7] Test ETF quotes...")
    client = TdxHqEtfClient()
    if client.connect_to_any( timeout=5.0 ):
        print( "    OK: Connected to server" )
        return client
    quotes = client.get_etf_quotes([
        (MARKET_SH, "510300"),
        (MARKET_SZ, "159915"),
    ])
    if quotes:
        print(f"    OK: Got {len(quotes)} quotes")
        for q in quotes:
            print(f"    {q['code']}: price={q['price']:.3f}")
    else:
        print("    WARN: No quotes returned")

def test_etf_xdxr(client):
    """测试 ETF 除权除息"""
    print("[8] Test ETF xdxr info...")
    xdxr = client.get_etf_xdxr_info(MARKET_SH, "510300")
    if xdxr:
        print(f"    OK: Got {len(xdxr)} xdxr records")
        for x in xdxr[:3]:
            print(f"    {x['year']}-{x['month']:02d}-{x['day']:02d} cat={x['category']}")
    else:
        print("    WARN: No xdxr records")

def test_etf_finance(client):
    """测试 ETF 财务信息"""
    print("[9] Test ETF finance info...")
    info = client.get_etf_finance_info(MARKET_SH, "510300")
    if info:
        print(f"    OK: Got finance info")
        print(f"    zongguben = {info['zongguben']}")
        print(f"    meigujingzichan = {info['meigujingzichan']}")
    else:
        print("    WARN: No finance info")

def main():
    print("=" * 60)
    print("ETF Module Test")
    print("=" * 60)

    test_etf_client_creation()
    test_is_etf_static()
    test_auto_market_code()

    client = test_etf_connection()
    if client:
        try:
            test_etf_list(client)
            test_etf_bars(client)
            test_etf_quotes(client)
            test_etf_xdxr(client)
            test_etf_finance(client)
        finally:
            client.disconnect()

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
