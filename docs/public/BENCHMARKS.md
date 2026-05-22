# 性能基准

> 测试环境: Windows 11, Rust 1.95.0 (x86_64-pc-windows-gnu), Python 3.13  
> 测试脚本: `examples/bench_network.rs` / `examples/bench_concurrent.rs`

---

## 1. 顺序请求性能

### 测试方法

7 次顺序 API 调用（K线×4 + 行情×1 + 数量×1 + 列表×1），对比三种客户端方案的总耗时。

### 结果

| 方案 | K线 | 行情 | 数量 | 列表 | **总耗时** | 相对 |
|------|-----:|-----:|-----:|-----:|--------:|:---:|
| 裸连接 (Direct) | 1.30s | 296ms | 311ms | 372ms | 2.28s | 4.0× |
| 连接池 (Pool) | 290ms | 75ms | 62ms | 146ms | **573ms** | 1.0× |
| 异步 (Async) | 294ms | 66ms | 63ms | 137ms | **560ms** | 1.0× |

> 连接池与异步在顺序场景下持平（差异 < 3%，落在测量误差内）。

### 分析

裸连接每次请求经历 **TCP 建连 (50-80ms) + 三步握手 (150-200ms)**，7 次请求累计握手开销约 1.7s，占总耗时 85%。连接池和异步通过复用连接消除了这 85% 的重复开销，这是连接池的核心价值。

---

## 2. 高并发性能

### 测试方法

5 / 20 / 60 个并发线程，每线程请求 50 条日 K 线，测量 wall-clock 总耗时（最后一个线程完成的时间）。

### 结果

| 用户数 | 裸连接 | 连接池 | 异步 |
|:-----:|------:|------:|------:|
| 5 | 381ms | 337ms | 345ms |
| 20 | 389ms | 1.41s | 1.34s |
| 60 | 344ms | 4.11s | 3.88s |
| **从 5→60 扩展比** | **0.9×** | 12.2× | 11.2× |

### 分析

**裸连接**：每线程持有独立 TCP 连接，相互无干扰，天然并行。60 线程只需 344ms（≈ 单个连接+握手+请求的串行耗时），扩展比接近 1×（几乎不退化）。

**连接池**：瓶颈在 `Mutex<Arc<ConnectionPool>>`。
- 池上限 5 连接，60 线程争用一个锁
- `borrow()` 无空闲连接时触发新建，新建过程中持锁 250-300ms
- 其余线程排队等锁，形成串行化
- 60 线程退化 12 倍

**异步**：底层 `tokio::sync::Mutex<Option<AsyncTcpConnection>>` 保护唯一连接，同一时间只有一个请求在执行。60 任务串行排队，退化 11 倍。

> **注意**：连接池的退化不是因为"连接池"这个设计不好，而是当前 `Mutex` 锁粒度过粗 + 池上限固定导致高并发争用。理论上把池容量提升到与并发量匹配，并改为无锁/细粒度锁结构，连接池同样可以支撑高并发。这是当前实现的优化方向，不是架构缺陷。

---

## 3. 连接池 vs 裸连接 — 何时用哪个

两者的核心区别在于 **是否值得为连接复用付出同步代价**：

| 维度 | TdxHqClient (连接池) | TdxDirectClient (裸连接) |
|------|:---:|:---:|
| 单次请求延迟 | 低 (免握手) | 高 (每次握手 200ms+) |
| 多线程并发瓶颈 | Mutex 争用 | 无 (天然并行) |
| 心跳保活 | ✅ 10s 间隔 | ❌ |
| 自动重试 | ✅ 4 次指数退避 | ❌ |
| 数据缓存 | ✅ count/list | ❌ |
| 自动分页 | ✅ `_all()` | ❌ (可手动循环) |
| DataFrame / Tuple 输出 | ✅ | ❌ (仅 dict) |
| Python `connect_to_any()` | ✅ | ❌ (须指定 IP) |

**决策逻辑**:

```
请求是同时并发的吗?
  ├─ 是, 且并发数 > 连接池上限 → TdxDirectClient
  └─ 否
       └─ 需要心跳/重试/缓存/分页? → TdxHqClient
            └─ 只是偶发一两次查询 → TdxDirectClient (更轻量)
```

| 具体场景 | 推荐 | 理由 |
|------|:---:|------|
| 单个脚本顺序拉取数千条 K 线 | Pool | 免握手，4× 快，分页自动 |
| Web 服务，单请求单响应 | Pool | 连接复用，重试兜底 |
| 定时任务，每 5 分钟查询 10 只股票 | Pool | 心跳保活免反复建连 |
| 回测引擎，60 线程并发跑不同品种 | **Direct** | 12× 快，无机锁竞争 |
| 一次性查询，用完即弃 | Direct | 无需管理连接生命周期 |
| 异步生态 (tokio) | Async | 框架一致性 |

---

## 4. tdxrs vs Python tdxpy

### 本地文件解析

| 操作 | tdxrs (Rust) | tdxpy (Python) | 加速比 |
|------|------------:|--------------:|:-----:|
| 日线解析 (1000 条) | 0.3ms | 2.8ms | **9×** |
| 分钟线解析 (1000 条) | 0.5ms | 5.1ms | **10×** |
| 板块解析 (500 条) | 1.2ms | 12.0ms | **10×** |
| 财务解析 (500 条) | 0.8ms | 8.5ms | **11×** |

Rust 解析层利用零拷贝和 SIMD 友好的内存布局，本地文件速度提升约一个数量级。

### 网络 API

| 操作 | tdxrs (Rust) | tdxpy (Python) | 加速比 |
|------|------------:|--------------:|:-----:|
| K 线 (100 条) | 73ms | 110ms | **1.5×** |
| 行情 (3 只) | 75ms | 95ms | **1.3×** |
| 证券列表 (全量) | 146ms | 210ms | **1.4×** |

网络 API 端到端延迟主要由 TCP 往返主导（~50-100ms/请求），解析仅占 5-15ms。Rust 将这部分从 Python 的 10-20ms 压到 1-2ms，在总延迟中占比有限，因此加速比收敛在 1.3-1.5×。本地解析不受 I/O 限制，加速比可达 9-11×。

---

## 5. pip 安装版性能实测

> 测试环境: Windows 11, Python 3.13, `tdxrs==0.5.0` (PyPI wheel)  
> 测试脚本: `examples/gen_bench_charts.py`

### 5.1 本地文件解析 (Reader)

| 操作 | tdxrs (Rust) | 加速比 | 说明 |
|------|------------:|:-----:|------|
| 日线 800 条 | 0.35ms | — | 日线二进制解析 |
| 分钟线 800 条 | 0.34ms | — | 整数价格格式 |
| 板块 5 条 | 0.005ms | — | 变长 GBK 编码解析 |

> 未做 vs tdxpy 逐项对比，本地 9-11× 加速比已在 §4 中建立。

### 5.2 网络 K 线 (800 条/次, 多品类)

| K 线类型 | tdxrs (连接池) | 说明 |
|---------|-------------:|------|
| 日K (daily) | 290ms | 含复权计算 |
| 周K (weekly) | 210ms | 数据量较小 |
| 月K (monthly) | 190ms | 同上 |
| 5分钟线 | 280ms | 日内高频数据 |
| 1分钟线 | 260ms | 日内高频数据 |

> 各品类耗时差异主要由响应体大小决定，日 K 和分钟 K 数据量大，周/月 K 数据量小。

### 5.3 性能对比图

运行以下命令 (基于 pip 版 tdxrs, 无需 Rust 源码)：

```bash
pip install tdxrs matplotlib numpy
python examples/gen_bench_charts.py
```

输出 4 张柱状图到 `docs/public/`:

| 文件 | 内容 |
|------|------|
| `bench_reader_vs_python.png` | ① 本地解析: tdxrs vs tdxpy |
| `bench_network_kline_by_cat.png` | ② 网络 K 线: 多品类 800 条对比 |
| `bench_client_strategy.png` | ③ 网络方案: Pool/Direct/Async |
| `bench_concurrent_scaling.png` | ④ 高并发扩展比 |

---

## 6. 复现

```bash
# === Python 基准 ===

# Reader 本地文件解析
python tests/bench_reader.py
python tests/bench_reader.py --method daily --rounds 50 --json report.json

# 网络 API 性能
python tests/bench_network.py
python tests/bench_network.py --method kline --md report.md

# tdxrs vs tdxpy 对比 (需要 tdxpy 在 PYTHONPATH)
python tests/bench_performance.py --mode all

# === Rust 基准 ===

# 顺序性能 (三种客户端对比)
cargo run --example bench_network --release

# 并发性能 (5/20/60 用户)
cargo run --example bench_concurrent --release

# Criterion 微基准 (解析器/复权算法)
cargo bench
```

### 脚本结构

```
tests/
├── bench_utils.py           # 共享: 计时、统计、报告生成
├── bench_reader.py          # Reader 文件解析
├── bench_network.py         # 网络 API
├── bench_optimization.py    # dict vs tuple 模式对比
├── bench_performance.py     # tdxrs vs tdxpy 全面对比
└── compare_tdxpy_tdxrs.py   # 功能兼容性验证

examples/
├── bench_network.rs         # Rust 顺序性能
└── bench_concurrent.rs      # Rust 并发性能

benches/
└── reader_bench.rs          # Criterion 微基准
```

---

## 7. 已知局限

1. 顺序请求样本量有限（7 次 API），单次网络波动可能影响个别数据点
2. 连接池并发退化根因为锁粒度，非架构缺陷
3. Python TdxDirectClient 绑定不支持 `_all` / `_tuples` / `_dataframe`（Rust 侧同步不支持）
4. `AsyncTdxHqClient` 暂无 Python 绑定

---

## 8. 场景选择速查

根据实际使用模式，对照选择最合适的客户端：

### 量化/回测场景

```
复盘选股, 单线程遍历 5000 只股票逐只取日线
  → TdxHqClient
  复用连接，5000 次请求每次免 200ms 握手
  若裸连: 5000 × 0.2s = 额外 1000s 握手开销
```

```
多因子回测, 60 线程并发, 每线程取不同股票的 500 条日线
  → TdxDirectClient
  每线程独立连接零争用，344ms 全完成
  若连接池: Mutex 串行化 → 4s+
```

### Web 服务场景

```
Flask/FastAPI 后端, QPS < 10, 每请求调用 1-2 次 TDX API
  → TdxHqClient (全局单例)
  connect_to_any() 一次 → 所有请求复用
  心跳保活防止空闲断开
```

```
高并发微服务, QPS > 100, 每个请求独立取数据
  → 每个 worker 线程一个 TdxDirectClient
  或: 连接池扩大到 worker 数 + 优化锁粒度
```

### 定时任务场景

```
每天 9:30 拉取全市场日线做选股
  → TdxHqClient
  get_security_list 获取代码列表 → 遍历 get_security_bars_tuples 批量获取
  复用连接免握手 + tuple 模式省解析时间
```

```
每 5 分钟监控 10 只自选股行情
  → TdxHqClient (全局单例)
  长连接 + 心跳保活 → 每 5 分钟一次 get_security_quotes 批量查询
```

### 一次性场景

```
研究特定股票的除权历史: 取 xdxr + fq=0 K 线 + fq=1 K 线
  → TdxHqClient (最方便)
  一条龙: connect_to_any → 三个 API → disconnect
```

```
脚本里临时取 3 只股票的今日行情
  → TdxDirectClient
  指定 IP 即可，用完即走，最轻量
```

### 财务数据场景

```
下载最新季报 gpcw 数据 (~12MB)
  → TdxFinanceClient (Rust API)
  独立 15s 超时 + 分片 30KB/每次 + 自动重组
  不占用行情连接，不影响其他请求
```

```
查询特定股票实时财务 (34 字段)
  → TdxHqClient.get_finance_info()
  单次小请求 (<1KB)，混在行情请求中无影响
```
