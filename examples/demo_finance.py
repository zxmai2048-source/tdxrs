"""tdxrs 财务数据获取 — 完整演示

覆盖:
  1. 实时财务 (get_finance_info) — 34 字段, TDX 原始值, 中文 key
  2. 多股票批量财务对比
  3. 本地 gpcw 文件解析 (FinancialReader)
  4. gpcw 文件下载 + 全市场解析 (TdxHqClient.get_and_parse_block_info 模式)
  5. 财务 DataFrame 输出

注意: v0.5.1 起 get_finance_info 返回 TDX 原始值，不再做 ×10000 转换。
      单位可能为万元、千元或元，需用户根据实际数据自行判断。
"""

import os
from tdxrs import TdxHqClient, FinancialReader
from tdxrs.constants import MARKET_SH, MARKET_SZ

# ═══════════════════════════════════════════════════════════════
# 共享配置
# ═══════════════════════════════════════════════════════════════
WATCHLIST = [
    (MARKET_SH, "600519", "贵州茅台"),
    (MARKET_SZ, "000858", "五粮液"),
    (MARKET_SZ, "300750", "宁德时代"),
    (MARKET_SZ, "000001", "平安银行"),
]
SHOW_N = 3


def header(title: str):
    print(f"\n{'=' * 65}")
    print(f"  {title}")
    print(f"{'=' * 65}")


# ═══════════════════════════════════════════════════════════════
# 1. 实时财务 — 单股票 34 字段
# ═══════════════════════════════════════════════════════════════
header("1. 实时财务 (get_finance_info) — 贵州茅台")

client = TdxHqClient()
client.set_auto_retry(False)
client.connect_to_any(timeout=5.0)

fin = client.get_finance_info(market=1, code="600519")

# 单位说明: 全部为 TDX 原始值
#   股本类 → 万元/万股 (÷10000 = 亿股)
#   资产/收入/利润类 → 万元 (÷10000 = 亿元)
#   每股指标 → 元 (无需转换)
#   股东人数 → 户 (原始值)
print(f"\n  {'─' * 55}")
print(f"  {'字段':20s} {'原始值':>18s}  {'推测实际值':>16s}")
print(f"  {'─' * 55}")

key_fields = [
    ("liutongguben",   "流通股本",      1e-4, "亿股"),
    ("zongguben",      "总股本",        1e-4, "亿股"),
    ("zongzichan",     "总资产",        1e-4, "亿元"),
    ("jingzichan",     "净资产",        1e-4, "亿元"),
    ("zhuyingshouru",  "主营收入",      1e-4, "亿元"),
    ("jinglirun",      "净利润",        1e-4, "亿元"),
    ("meigujingzichan","每股净资产",    1.0,  "元"),
    ("gudongrenshu",   "股东人数",      1.0,  "户"),
    ("ipo_date",       "上市日期",      1.0,  "YYYYMMDD"),
    ("updated_date",   "更新日期",      1.0,  "YYYYMMDD"),
]
for field, label, scale, unit in key_fields:
    raw = fin[field]
    actual = raw * scale
    print(f"  {label:20s} {raw:>18.4f}  {actual:>16.2f} {unit}")

# ═══════════════════════════════════════════════════════════════
# 2. 多股票批量对比
# ═══════════════════════════════════════════════════════════════
header("2. 多股票财务对比")

compare_fields = [
    ("jingzichan", "净资产(万元)"),
    ("jinglirun",  "净利润(万元)"),
    ("zhuyingshouru", "主营收入(万元)"),
    ("meigujingzichan", "每股净资产(元)"),
]

print(f"\n  {'代码':8s} {'名称':8s}", end="")
for _, label in compare_fields:
    print(f" {label:>16s}", end="")
print()

for mkt, code, name in WATCHLIST:
    try:
        f = client.get_finance_info(mkt, code)
        print(f"  {code:8s} {name:8s}", end="")
        for field, _ in compare_fields:
            print(f" {f[field]:>16.2f}", end="")
        print()
    except Exception as e:
        print(f"  {code:8s} {name:8s}  ERROR: {e}")

# ═══════════════════════════════════════════════════════════════
# 3. 财务 DataFrame 输出
# ═══════════════════════════════════════════════════════════════
header("3. DataFrame 模式 (多股票)")

try:
    stocks = [(mkt, code) for mkt, code, _ in WATCHLIST]
    df = client.get_finance_info_dataframe(stocks)
    print(f"\n  DataFrame: {df.shape[0]} rows × {df.shape[1]} cols")
    # 选取部分列展示
    cols = ["code", "liutongguben", "jingzichan", "jinglirun", "meigujingzichan", "gudongrenshu"]
    available = [c for c in cols if c in df.columns]
    print(df[available].to_string(index=False))
except ImportError:
    print("  (跳过: 需要 pip install pandas)")
except Exception as e:
    print(f"  Error: {e}")

client.disconnect()

# ═══════════════════════════════════════════════════════════════
# 4. 本地 gpcw 文件解析 (FinancialReader)
# ═══════════════════════════════════════════════════════════════
header("4. 本地 gpcw 文件解析 (FinancialReader)")

# 如果你有下载好的 gpcw*.dat 文件, 放在 examples/local/ 目录
gpcw_dir = os.path.join(os.path.dirname(__file__), "local")
gpcw_files = []
if os.path.isdir(gpcw_dir):
    gpcw_files = sorted([f for f in os.listdir(gpcw_dir) if f.endswith('.dat')])

if gpcw_files:
    reader = FinancialReader()
    for fname in gpcw_files[:SHOW_N]:
        path = os.path.join(gpcw_dir, fname)
        records = reader.parse_file(path)
        print(f"\n  {fname}: {len(records)} 只股票")
        if records:
            # 展示前 3 只股票的前 5 个字段值
            for r in records[:SHOW_N]:
                preview = ", ".join(f"{v:.2f}" for v in r['fields'][:5])
                print(f"    {r['code']}  report_date={r['report_date']}  "
                      f"fields[{len(r['fields'])}]: [{preview} ...]")
else:
    print(f"\n  (跳过: 将 gpcw*.dat 文件放到 examples/local/ 目录即可测试)")
    print(f"  下载方式 (Rust API): TdxFinanceClient.get_report_file_by_size()")
    print(f"  或从通达信 vipdoc 目录复制: vipdoc/{'sh/sz'}/cw/gpcw*.dat")

# ═══════════════════════════════════════════════════════════════
# 5. 从 TDX 服务器下载 gpcw 文件列表
# ═══════════════════════════════════════════════════════════════
header("5. gpcw 文件列表 (需要 TdxFinanceClient — Rust API)")

print(f"\n  Python 绑定暂未暴露 TdxFinanceClient。")
print(f"  以下为等效 Rust 调用示例:")
print(f"")
print(f"  use tdxrs::net::finance_client::TdxFinanceClient;")
print(f"")
print(f"  let fc = TdxFinanceClient::new(\"120.76.152.87\", 7709, None);")
print(f"")
print(f"  // 列出可用报告期")
print(f"  let files = fc.get_financial_list()?;")
print(f"  // → [GpcwFileInfo {{ filename: \"gpcw20260331.dat\", filesize: 12931990 }}, ...]")
print(f"")
print(f"  // 下载 + 解析指定报告期")
print(f"  let records = fc.get_financial_data(\"gpcw20260331.dat\", 12931990)?;")
print(f"  // → Vec<FinancialRecord> (全市场 ~5500 只股票 × 584 字段)")
print(f"")
print(f"  // 提取单只股票 45 个命名指标 (英文 key, 原始值)")
print(f"  let ind = fc.get_finance_indicators(\"gpcw20260331.dat\", 12931990, \"600519\")?;")
print(f"  // → {{\"eps\": 1.87, \"roe_weighted\": 8.28, \"total_assets\": 5.77e12, ...}}")
print(f"")
print(f"  // 带中文标签 (适合校验)")
print(f"  let labeled = fc.get_finance_indicators_labeled(...)?;")
print(f"  // → [(\"eps\", \"基本每股收益\", 1.87), ...]")

print(f"\n{'=' * 65}")
print("演示完成。")
