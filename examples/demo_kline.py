"""tdxrs K线数据获取 — 完整演示

覆盖:
  - 个股K线: 日/周/月/1分钟/5分钟
  - 指数K线: 上证/深证
  - 复权类型: 前复权(默认)/后复权/未复权
  - 分页: 手动分页 / 自动分页
  - 输出格式: dict / tuple (高性能) / DataFrame
  - 连接池配置最佳实践

默认每请求 100 条, 展示前 5 条。
"""

from tdxrs import TdxHqClient
from tdxrs.constants import (
    MARKET_SH, MARKET_SZ,
    KLINE_DAILY, KLINE_WEEKLY, KLINE_MONTHLY,
    KLINE_1MIN, KLINE_5MIN,
    FQ_QFQ, FQ_HFQ, FQ_NONE,
    MAX_KLINE_COUNT, DEFAULT_POOL_SIZE,
)

# ═══════════════════════════════════════════════════════════════
# 共享参数
# ═══════════════════════════════════════════════════════════════
STOCK = "600519"          # 贵州茅台
INDEX_SH = "000001"       # 上证指数
INDEX_SZ = "399001"       # 深证成指
DEFAULT_COUNT = 100
SHOW_N = 5


def header(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def show_first(bars, n=SHOW_N):
    """打印前 n 条记录"""
    for b in bars[:n]:
        dt = b.get("datetime", "")
        print(f"  {dt:16s}  O={b['open']:>10.2f}  H={b['high']:>10.2f}  "
              f"L={b['low']:>10.2f}  C={b['close']:>10.2f}  V={b['vol']:>10.0f}")


# ═══════════════════════════════════════════════════════════════
# 初始化客户端 (生产环境推荐配置)
# ═══════════════════════════════════════════════════════════════
client = TdxHqClient()
client.set_connect_timeout(5.0)
client.set_auto_retry(False)   # 生产环境关闭内置重试
client.set_cache_ttl(120)       # 证券列表缓存 2 分钟

print("连接 TDX 服务器...")
client.connect_to_any(timeout=5.0)
print(f"已连接, 连接池状态: {client.pool_stats()}")

# ═══════════════════════════════════════════════════════════════
# 1. 个股日K线 — 默认前复权 (最常用)
# ═══════════════════════════════════════════════════════════════
header(f"1. 个股日K (前复权, 默认) — {STOCK}")

# fq 缺省 → 前复权
bars = client.get_security_bars(KLINE_DAILY, MARKET_SH, STOCK, 0, DEFAULT_COUNT)
print(f"  获取 {len(bars)} 条 (默认 fq=1 前复权)")
show_first(bars)

# ═══════════════════════════════════════════════════════════════
# 2. 复权类型对比 — 未复权 / 前复权 / 后复权
# ═══════════════════════════════════════════════════════════════
header(f"2. 复权对比 — {STOCK} 日K (各 100 条)")

for fq_val, fq_name in [(FQ_NONE, "未复权"), (FQ_QFQ, "前复权"), (FQ_HFQ, "后复权")]:
    bars = client.get_security_bars(KLINE_DAILY, MARKET_SH, STOCK, 0, DEFAULT_COUNT, fq=fq_val)
    print(f"\n  [{fq_name} fq={fq_val}] 最新: {bars[-1]['datetime']} C={bars[-1]['close']:.2f}")
    show_first(bars)

# ═══════════════════════════════════════════════════════════════
# 3. 不同 K 线种类
# ═══════════════════════════════════════════════════════════════
header(f"3. 多周期K线 — {STOCK}")

categories = [
    (KLINE_DAILY,   "日K"),
    (KLINE_WEEKLY,  "周K"),
    (KLINE_MONTHLY, "月K"),
    (KLINE_5MIN,    "5分钟"),
    (KLINE_1MIN,    "1分钟"),
]
for cat, name in categories:
    bars = client.get_security_bars(cat, MARKET_SH, STOCK, 0, DEFAULT_COUNT)
    print(f"\n  [{name}] {len(bars)} 条")
    show_first(bars)

# ═══════════════════════════════════════════════════════════════
# 4. 指数K线 — 不复权 (fq 被忽略)
# ═══════════════════════════════════════════════════════════════
header("4. 指数K线")

for mkt, code, name in [(MARKET_SH, INDEX_SH, "上证"), (MARKET_SZ, INDEX_SZ, "深证")]:
    bars = client.get_index_bars(KLINE_DAILY, mkt, code, 0, DEFAULT_COUNT)
    print(f"\n  [{name} {code}] {len(bars)} 条")
    # 指数有额外字段 up_count / down_count
    for b in bars[:SHOW_N]:
        print(f"  {b['datetime']:16s}  O={b['open']:>10.2f}  C={b['close']:>10.2f}  "
              f"↑{b['up_count']:>5d}  ↓{b['down_count']:>5d}")

# ═══════════════════════════════════════════════════════════════
# 5. 自动分页 — 获取超过 800 条
# ═══════════════════════════════════════════════════════════════
header(f"5. 自动分页 — {STOCK} 日K 3000 条")

bars_all = client.get_security_bars_all(KLINE_DAILY, MARKET_SH, STOCK, 3000)
print(f"  获取 {len(bars_all)} 条")
print(f"  最早: {bars_all[0]['datetime']}  最新: {bars_all[-1]['datetime']}")

# ═══════════════════════════════════════════════════════════════
# 6. 手动翻页 (精确控制)
# ═══════════════════════════════════════════════════════════════
header(f"6. 手动翻页 — {STOCK} 日K (每页 800 条)")

for page, start in enumerate([0, 800, 1600]):
    bars = client.get_security_bars(KLINE_DAILY, MARKET_SH, STOCK, start, 800, FQ_NONE)
    if not bars:
        break
    print(f"  Page {page + 1} (start={start}): {bars[0]['datetime']} .. {bars[-1]['datetime']} ({len(bars)} 条)")

# ═══════════════════════════════════════════════════════════════
# 7. Tuple 高性能模式
# ═══════════════════════════════════════════════════════════════
header("7. Tuple 高性能模式")

tuples = client.get_security_bars_tuples(KLINE_DAILY, MARKET_SH, STOCK, 0, DEFAULT_COUNT)
print(f"  {len(tuples)} 条, tuple 结构: (open, close, high, low, vol, amount, y, m, d, h, mi, dt)")
for t in tuples[:SHOW_N]:
    # t = (open, close, high, low, vol, amount, year, month, day, hour, minute, datetime)
    print(f"  {t[11]:16s}  O={t[0]:>10.2f}  C={t[1]:>10.2f}  V={t[4]:>10.0f}")

# ═══════════════════════════════════════════════════════════════
# 8. DataFrame 模式 (需要 pandas)
# ═══════════════════════════════════════════════════════════════
header("8. DataFrame 模式")

try:
    df = client.get_security_bars_dataframe(KLINE_DAILY, MARKET_SH, STOCK, 0, DEFAULT_COUNT)
    print(f"  DataFrame: {df.shape[0]} rows × {df.shape[1]} cols")
    print(f"  Columns: {list(df.columns)}")
    print(df.tail(5).to_string())
except ImportError:
    print("  (跳过: 需要 pip install pandas)")

# ═══════════════════════════════════════════════════════════════
# 9. 多股票批量获取
# ═══════════════════════════════════════════════════════════════
header("9. 多股票批量日K")

watchlist = [
    (MARKET_SH, "600519", "茅台"),
    (MARKET_SZ, "000858", "五粮液"),
    (MARKET_SZ, "300750", "宁德"),
]
for mkt, code, name in watchlist:
    bars = client.get_security_bars(KLINE_DAILY, mkt, code, 0, DEFAULT_COUNT)
    last = bars[-1] if bars else None
    if last:
        print(f"  {name:6s} {code}  {last['datetime']}  C={last['close']:>10.2f}")

# ═══════════════════════════════════════════════════════════════
# 清理
# ═══════════════════════════════════════════════════════════════
client.disconnect()
print(f"\n{'─' * 60}")
print("已断开。所有演示完成。")
