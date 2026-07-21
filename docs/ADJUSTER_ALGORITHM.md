# 复权价格调整算法文档

> 对应实现: `src/protocol/adjuster.rs`, `src/protocol/fq_service.rs`
> 最后更新: 2026-07-17 | 当前版本: v0.6.6

---

## 1. 算法概要

### 1.1 公式 (中国A股标准除权除息公式)

```
除权除息日开盘参考价:
  P_ex = (P_close - D + P_rights × R_rights) / (1 + R_bonus + R_rights)

前复权因子: factor = P_ex / P_close
  所有除权日之前的 K 线价格 × cumulative_factor

后复权因子: factor = P_close / P_ex
  所有除权日当天及之后的 K 线价格 × cumulative_factor
```

### 1.2 参数单位映射

| TDX 原始字段 | 含义 | 单位 | 算法中使用 |
|-------------|------|------|-----------|
| `fenhong` | 每股派息(税前) | 元/10股 | `÷10 = 元/股` |
| `songzhuangu` | 送转股数 | 股/10股 | `÷10 = 比例(如0.8=10送8)` |
| `peigu` | 配股数 | 股/10股 | `÷10 = 比例` |
| `peigujia` | 配股价 | 元/股 | 直接使用 |

### 1.3 复权类型

| 类型 | 值 | 说明 |
|------|:--:|------|
| `FQ_NONE` | 0 | 未复权，直接返回 |
| `FQ_QFQ` | 1 | 前复权，历史价向下调整，现价不变 |
| `FQ_HFQ` | 2 | 后复权，现价向上调整，首日价不变 |

### 1.4 精度约定

- 内部全程 f64 计算，不截断
- 最终输出按 `FQ_PRICE_PRECISION = 3` 位小数四舍五入
- O/H/L/C 四个价格乘以相同因子，比值保持不变
- 成交量不做调整

---

## 2. 版本迭代历史

### v0.1.0 — 初始实现 (2026-05-01)

**文件**: `src/protocol/adjuster.rs`

- `adjust_security_bars(bars, xdxr_list, fq_type)`
- 仅在 `bars` 范围内搜索每个除权日的前收盘价 (`close_before`)
- QFQ/HFQ 基本因子累乘

**问题**: 当除权日期早于 K 线数据范围时，找不到 close_before，事件被静默丢弃，导致累积因子少乘。

### v0.2.0 — 因子计算修复 (2026-05-01)

- 修复单价（分红/送转/配股）与单位转换一致性问题
- 完善单元测试

### v0.3.0 — context_bars 支持 (2026-05-04)

**新增特性**: 早期除权事件补全

- **新增函数** `find_close_before_event(bars, context_bars, date_key)`
  - 先在 `bars` 中正向搜索 `< date_key` 的最后一条 bar (最近匹配)
  - 未找到时回退到 `context_bars` 反向搜索 (更早数据)
- **签名变更**: `adjust_security_bars(bars, context_bars, xdxr_list, fq_type)`
  - 追加 `context_bars: &[SecurityBar]` 参数（只读，仅用于因子计算）
- **客户端改动** (`client.rs`, `direct_client.rs`, `async_client.rs`)
  - 新增 `fetch_context_bars_for_adjust()` 自动获取历史上下文
  - 检测最早除权日 `ee_date`，若 `bars[0] > ee_date` 则触发翻页拉取
  - 向后翻页最多 8 页 (6400 根 K 线)，查到 `ee_date` 为止

**触发场景**: 300750 的 800 根日 K 线仅覆盖 2023-01 至 2026-05，而 2019–2022 年有 4 个除权除息事件。若无 context_bars，这 4 个事件全部被丢弃。

**验证案例**: 300750 2023-04-25 完整 10 事件累积因子 `0.515522`

### v0.3.1 — 送股+分红联合验证 (2026-05-05)

- 系统性验证 300750 2023-04-26 同时分红(25.2元/10股)+送股(10送8)场景
- 逐事件追踪累积因子，确认所有 6 个事件边界穿越正确
- 验证 O/H/L/C 比例不变性 (差异 < 3e-6)
- 与"其他平台"对比复权后行情，确认差异源于原始 raw data 不同，非算法问题
- 当前版本暂定为此方案

### v0.6.0 — FqContextTier 分档 (2026-07-17)

**新增特性**: 复权上下文拉取分档控制

- **FqContextTier** 枚举: Low (2400根≈10年), Mid (4800根≈20年), High (7200根≈30年)
- 默认档位: Mid
- 客户端 API: `set_fq_context_tier(tier)`, `fq_context_tier()`
- Python 绑定: `client.set_fq_context_tier("high")`

**分档依据**: 按历史 K 线数量控制翻页数，平衡精度与网络开销。

| 档位 | K 线数 | 翻页数 | 适用场景 |
|------|--------|--------|---------|
| Low | 2400 | 3 | 近 10 年新股 |
| Mid | 4800 | 6 | 大部分股票 (默认) |
| High | 7200 | 9 | 长历史股票 (如600900) |

### v0.6.6 — FqService 解耦 + 自动档位 (2026-07-17)

**架构改动**: 复权业务逻辑从客户端解耦

- **新增模块** `src/protocol/fq_service.rs`
  - `FqService::auto_detect_tier(xdxr_list, current_year)` — O(1) 自动档位检测
  - `FqService::apply_fq(bars, context_bars, xdxr_list, fq_type)` — 复权应用
  - `FqService::calc_factors(xdxr_list, bars, context_bars)` — 因子计算
- **自动档位逻辑**:
  - 读取 XDXR 首条记录的年份
  - 计算与当前年份差值: ≤10年→Low, 11-20年→Mid, >20年→High
- **线程安全**: 使用 `AtomicU8` 替代 `Cell<FqContextTier>`，满足 PyO3 Send+Sync 要求

---

## 3. 算法设计细节

### 3.1 前复权 (QFQ)

```
核心逻辑: 从最新到最旧遍历 K 线，累计所有在 bar 之后发生的除权因子
```

```
events 按日期升序排列 [(date, parts), ...]
factors BTreeMap: date → factor_value

cumulative = 1.0
event_iter = events.rev()  // 从最新到最旧

for bar in bars.rev():      // 从最新到最旧
    // 把所有日期 > bar.date 的 event 因子累乘
    while event_iter.peek().date > bar.date:
        cumulative *= factors[event_iter.next().date]
    
    // 应用累积因子
    bar.O *= cumulative
    bar.H *= cumulative
    bar.L *= cumulative
    bar.C *= cumulative
```

**数学意义**: QFQ 回答"如果所有后续除权事件已经发生，某日的价格应该是多少"。最新 bar 不被调整，历史 bar 按后续所有事件的比例因子向下调整。

### 3.2 后复权 (HFQ)

```
核心逻辑: 从最旧到最新遍历 K 线，累计所有 ≤ bar 的除权因子
```

```
cumulative = 1.0
event_iter = events (从最旧到最新)

for bar in bars (从最旧到最新):
    while event_iter.peek().date ≤ bar.date:
        cumulative *= 1.0 / factor  // 后复权用倒数
        event_iter.next()
    
    bar.O *= cumulative
    ...
```

### 3.3 close_before 搜索策略

```
find_close_before_event(bars, context_bars, date_key):
    1. bars.iter() 正向扫描，take_while(d < date_key)，取 last()
    2. 若未找到，context_bars.iter().rev() 反向扫描，find(d < date_key)
    3. 均未找到 → return None (该事件被跳过)
```

搜索顺序保证: 在 `bars` 中找到的是距离除权日最近的可用交易日的 close，这是正确的前收盘价。仅在 `bars` 完全不够时回退到 `context_bars`。

### 3.4 因子独立性

每个除权事件的 factor 独立计算:
```
factor_i = (close_before_i - D_i + rights_price_i × rights_ratio_i)
         / (close_before_i × (1 + bonus_ratio_i + rights_ratio_i))
```

**关键特性**: `close_before_i` 来自原始未复权数据。对于送股后的分红事件，其 `close_before` 已是送股后价位(因为原始数据中的送股后交易日价格自然在送股后水平)。各因子独立、互不依赖，累乘顺序不影响结果。

### 3.5 除权日处理

- 除权日本身不应用该除权日的事件因子（`evt_date > bar_key`，严格大于）
- 除权日的原始数据已经反映了除权结果（降低的开盘价、连续的复权后价格）
- QFQ 中后续除权因子仍会被应用到此 bar

---

## 4. 边界条件处理

### 4.1 除权日在 K 线数据范围之前

```
bars 范围: 2023-01 至 2026-05
早期事件: 2019-07-22, 2020-06-04, 2021-07-05, 2022-09-28

→ bars 中没有 < 这些日期的数据
→ 回退到 context_bars (从 offset=800 向后翻页最多 6400 根)
→ context_bars 中找到合适的 close_before
→ 累积因子正确包含早期事件
```

**无 context_bars 时的影响**: 累积因子偏大，QFQ 调整不足，早期价格偏高。

### 4.2 纯分红 vs 分红+送股

| 场景 | 因子公式 | 示例 |
|------|---------|------|
| 纯分红 | `(P - D) / P` | 2026-04-22: `(447.60 - 6.957) / 447.60 = 0.984457` |
| 分红+送股 | `(P - D) / (P × (1+R_bonus))` | 2023-04-26: `(385.90 - 2.52) / (385.90 × 1.8) = 0.551928` |
| 分红+配股 | `(P - D + P_rights × R_rights) / (P × (1+R_rights))` | — |

### 4.3 多事件同日

当前实现按 `BTreeMap` 按日期去重。若同一天有多个 category=1 事件，仅最后写入的生效。该情况在 A 股极少发生，当前未做合并处理。

### 4.4 缺失 close_before

若 `find_close_before_event` 返回 `None`，该事件跳过 (`factor_map` 中无该日期条目)。最可能的原因是 context_bars 也不包含足够早的数据。

### 4.5 指数复权

`adjust_index_bars` 为空操作。指数不存在复权概念，保留为接口一致性。

---

## 5. 性能与精度

### 5.1 计算复杂度

| 阶段 | 复杂度 | 说明 |
|------|:------:|------|
| 构建 events | O(N_events) | 遍历 xdxr list |
| 构建 factor_map | O(N_events × N_bars) | 每个事件搜索 close_before |
| QFQ 调整 | O(N_bars + N_events) | 双指针扫描，一次遍历 |
| HFQ 调整 | O(N_bars + N_events) | 同上 |

### 5.2 context_bars 拉取开销

- 触发条件: `bars[0] 日期 > 最早除权日`
- 每次拉取: 1-9 次网络请求 (每页 800 根，取决于档位)
- 典型场景: 800 根日 K 线除外全事件 → 需要 0 次 (不触发)
- 极端场景: 100 根日 K 线 + 2019 年除权 → 最多 9 次 (High 档)

| 档位 | 最大翻页 | 最大 K 线数 | 典型耗时增量 |
|------|---------|------------|-------------|
| Low | 3 | 2400 | +50ms |
| Mid | 6 | 4800 | +150ms |
| High | 9 | 7200 | +300ms |

### 5.3 精度

- 内计算: f64，无中间截断
- 输出 rounding: `round_price(p, 3)` = `(p * 1000).round() / 1000`
- 浮点尾噪声: 经 rounding 消除 (< 1e-12 级别)

---

## 6. 验证方法

### 6.1 单元测试

| 测试 | 覆盖场景 |
|------|---------|
| `test_calc_qfq_factor_cash_div` | 纯分红因子计算 |
| `test_calc_qfq_factor_bonus` | 送股因子计算 (10送10) |
| `test_adjust_no_event` | 无事件时不调整 |
| `test_find_close_before_fallback_to_context` | close_before 回退到 context |
| `test_adjust_context_hfq` | 后复权 + context_bars |
| `test_auto_detect_tier_low` | 自动档位: ≤10年→Low |
| `test_auto_detect_tier_mid` | 自动档位: 11-20年→Mid |
| `test_auto_detect_tier_high` | 自动档位: >20年→High |
| `test_auto_detect_tier_empty` | 空 XDXR→Mid (默认) |

### 6.2 已知验证点 (300750)

| 日期 | 事件 | 验证值 |
|------|------|--------|
| 2023-04-26 | 分红25.2+送股8 | `close_before=385.90, factor=0.551928, P_ex=212.989` |
| 2024-04-30 | 分红50.28 | `close_before=209.63, factor=0.976015` |
| 2025-01-24 | 分红12.30 | `close_before=257.50, factor=0.995223` |
| 2025-04-22 | 分红45.53 | `close_before=231.36, factor=0.980321` |
| 2025-08-20 | 分红10.07 | `close_before=277.80, factor=0.996375` |
| 2026-04-22 | 分红69.57 | `close_before=447.60, factor=0.984457` |

2023-04-25 累积因子 (全部 10 个事件) = `0.515522`

### 6.3 比例不变性

QFQ/HFQ 不改变 O/H/L/C 之间的比例关系:
```
raw_C/raw_O = fq1_C/fq1_O  (误差 < 3e-6)
```
因为四个价格乘以同一因子，商不变。

### 6.4 多周期验证 (600900)

2026-07-17 除权日验证，各周期 QFQ 差额一致:

| 周期 | RAW[0] open | QFQ[0] open | 差额 |
|------|-------------|-------------|------|
| Daily | 27.19 | 26.43 | 0.76 |
| Weekly | 27.03 | 26.27 | 0.76 |
| 1Hour | 27.00 | 26.25 | 0.75 |
| 30Min | 27.09 | 26.33 | 0.76 |
| 15Min | 27.06 | 26.30 | 0.76 |
| 5Min | 26.52 | 25.78 | 0.74 |

差额 ≈ 分红金额 0.79 元/股，各周期一致。

---

## 7. 平台差异分析

### 7.1 复权方法对比

不同平台使用不同的复权计算方法，导致结果差异:

| 方法 | 公式 | 特点 | 使用平台 |
|------|------|------|---------|
| **等比复权** (乘法) | `QFQ = RAW × 累积因子` | 结果始终为正，比例不变 | tdxrs, 通达信 |
| **累计调整** (加法) | `QFQ = RAW - 累积调整额` | 早期价格可能为0或负 | 腾讯, 部分券商 |

**tdxrs 使用等比复权法**，这是通达信原生的标准方法。

### 7.2 600900 (长江电力) 案例分析

600900 自 2003 年上市以来共有 26 次除权除息事件，其中包含 2 次送股:

| 日期 | 事件 | 因子影响 |
|------|------|---------|
| 2005-08-15 | 分红 0.59元/股 + **送股 1.7股/10股** | QFQ × 0.799, HFQ × 1.250 |
| 2010-07-20 | 分红 0.32元/股 + **送股 5股/10股** | QFQ × 0.650, HFQ × 1.535 |

**送股对复权的影响**:

| 计算方式 | 累积因子 | HFQ 收盘 (2026-07-17) |
|---------|---------|----------------------|
| 含送股 (tdxrs) | 3.9063 | 109.34 |
| 不含送股 (仅现金分红) | 2.2312 | 62.45 |
| 腾讯平台 (参考) | ~2.3-2.5 | ~66-69 |

**结论**: 腾讯的后复权计算可能不包含送股事件，或使用不同的处理方式。tdxrs 的计算包含所有 category=1 事件，符合通达信标准。

### 7.3 QFQ 价格对比

| 年份 | RAW | tdxrs QFQ | 腾讯 QFQ (参考) |
|------|-----|-----------|----------------|
| 2003 | 8.68 | 1.244 | ~0 或负数 |
| 2005 | 8.94 | 1.294 | ~0 或负数 |
| 2010 | 13.19 | 1.705 | ~0 或负数 |
| 2015 | 11.18 | 5.802 | ~0 |
| 2026 | 27.99 | 27.99 | 27.99 |

腾讯 QFQ 早期价格为 0 或负数，是因为使用累计调整法 (加法复权)。当累积调整额超过原始价格时，结果为负。tdxrs 使用等比复权法，结果始终为正。

### 7.4 2005-08-15 数据核实

该事件送股比例为 0.17 (每10股送1.7股)，不是常见的整数比例。建议核实 TDX 服务器数据是否正确。若实际为 10送2 (0.20)，则因子会有差异。

---

## 8. 当前限制与优化方向

### 8.1 已知限制

- **多事件同日**: 按 date_key 去重，同一天多个 category=1 事件无法合并
- **context_bars 数量分档**: Low/Mid/High 三档，若某股票除权日在更早且未覆盖，事件失效
- **每次请求重新计算**: 未做因子结果缓存，同股票多次 `get_security_bars` 重复拉取 xdxr + 计算
- **平台差异**: 等比复权法与累计调整法结果不同，无法与部分平台对齐

### 8.2 可优化项

| 方向 | 方案 | 预期效果 |
|------|------|---------|
| 因子缓存 | 按 (market, code) 缓存计算好的累积因子序列，过期 TTL | 同股票多次请求免重复计算 |
| 惰性计算 | 仅计算实际使用的 bar 范围内的因子，而非全部事件 | 减少 events 遍历 |
| context_bars 上限 | 根据最早除权日按需请求，而非固定档位 | 减少网络请求 |
| 提前终止 | 当累积因子与 1.0 差异可忽略时跳过 | 微优化 |
| 并行 context 拉取 | 多个早期事件需要 context 时分页并行请求 | 加速首次冷启动 |
| 自动档位优化 | 结合 XDXR 记录数和最早日期动态选择 | 更精准的上下文拉取 |

---

## 9. API 使用示例

### 9.1 Python 复权控制

```python
import tdxrs

client = tdxrs.TdxHqClient()

# 查看当前档位
print(client.fq_context_tier())  # "mid"

# 设置档位 (长历史股票建议用 high)
client.set_fq_context_tier("high")

# 获取前复权数据
bars_qfq = client.get_security_bars(4, 1, '600900', 0, 10, 1)

# 获取后复权数据
bars_hfq = client.get_security_bars(4, 1, '600900', 0, 10, 2)

# 计算复权因子 (不修改 K 线)
result = client.calc_fq_factors(1, '600900', 0, 800)
print(f"累积 QFQ 因子: {result['cumulative_qfq']:.6f}")
print(f"累积 HFQ 因子: {result['cumulative_hfq']:.6f}")
print(f"因子事件数: {len(result['factors'])}")
```

### 9.2 CLI 使用

```bash
# 前复权
tdxrs bars 600900 --fq 1 --count 10

# 后复权
tdxrs bars 600900 --fq 2 --count 10

# 不复权
tdxrs bars 600900 --fq 0 --count 10
```
