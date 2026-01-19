# 综合架构演进方案

## 概述

本方案整合三个方向的改进：
1. **方案A**：向量化技术面回测（快速验证 Multi-Agent 质量）
2. **路径3-增强**：虚拟交易 → Paper Trading（含手续费、滑点、T+1）
3. **路径3-核心**：重构回测引擎（引入真实回测框架如 Backtrader/VectorBT）

---

## 目标

### 短期目标（1-2 周）
- 实现向量化技术面回测，快速验证策略有效性
- 增强虚拟交易包含真实交易特性（手续费、滑点）

### 中期目标（1-2 个月）
- 建立历史事件管理机制
- 重构回测引擎支持混合策略（技术面 + 历史事件）

### 长期目标（3-6 个月）
- 完整的 Paper Trading 环境
- 引入专业回测框架（Backtrader/VectorBT）
- 参数优化系统

---

## 架构设计

### 当前架构

```
实时交易（简化版）
┌─────────────────────────────────┐
│ Market Data  │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│ Multi-Agent Team             │
│ (News + Tech + Fund + Risk) │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│ 简化虚拟交易（无手续费/滑点）│
└─────────────────────────────────┘
```

### 目标架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    实时交易系统 (Paper Trading)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐                      ┌─────────────┐│
│  │Market Data │  │Event Data   │                      │Multi-Agent  ││
│  └─────────────┘  └─────────────┘                      └─────────────┘│
│         ↓               ↓                                 │        ↓     ││
│  ┌─────────────────────────────────────────────────────────────────┐  │        ↓     ││
│  │     向量化技术面回测                      │  │  Paper   ││
│  │     (快速策略验证)                            │  │  Trading ││
│  └─────────────────────────────────────────────────────────────────┘  │        ↓     ││
│                    ↓                                 │        ↓     ││
│         ┌─────────────────────────────────────────┐         │        ↓     ││
│         │    混合回测引擎                 │─────────┘  │        ↓     ││
│         │    (技术面 + 历史事件)            │                  │        ↓     ││
│         │                                     │  ┌─────────────────────┐│        ↓     ││
│         │                                     │  │  参数优化系统     │─────────┘│        ↓     ││
│         └─────────────────────────────────────────┘         │─────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 阶段 1：向量化技术面回测（快速，1-2 周）

### 目标
实现纯技术面向量化回测，快速验证 Multi-Agent 策略质量。

### 新增文件
- `app/backtest/vectorized_technical.py` - 向量化技术面回测引擎
- `app/models/backtest.py` - 回测相关模型（新增）

### 改造现有文件
- `app/backtest/engine.py` - 支持使用向量化引擎

### 技术方案

**向量化策略定义**：
```python
class VectorizedTechnicalStrategy:
    """向量化技术面策略"""

    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        """批量生成信号"""
        # EMA 交叉策略
        signals = pd.Series(0, index=bars.index, dtype=int)

        # EMA 金叉 → 买入
        signals[
            (bars['ema_5'] > bars['ema_20']) &
            (bars['ema_5'].shift(1) < bars['ema_20'].shift(1))
        ] = 1

        # EMA 死叉 → 卖出
        signals[
            (bars['ema_5'] < bars['ema_20']) &
            (bars['ema_5'].shift(1) > bars['ema_20'].shift(1))
        ] = -1

        return signals
```

**向量化回测引擎**：
```python
class VectorizedBacktestEngine:
    """向量化回测引擎"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.strategy = VectorizedTechnicalStrategy()

    def run(self) -> BacktestResult:
        """执行回测"""
        # 1. 获取历史数据
        bars = self._load_historical_bars()

        # 2. 批量生成信号
        signals = self.strategy.generate_signals(bars)

        # 3. 计算收益（向量化）
        bars['signal'] = signals
        bars['returns'] = bars['close'].pct_change()
        bars['strategy_returns'] = bars['signal'] * bars['returns'].shift(1)

        # 4. 计算绩效指标
        total_return = bars['strategy_returns'].sum()
        max_drawdown = self._calculate_max_drawdown(bars)
        sharpe_ratio = self._calculate_sharpe(bars['strategy_returns'])

        return BacktestResult(
            total_return=total_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            equity_curve=self._build_equity_curve(bars),
        )
```

### 回测配置扩展
```python
class BacktestConfig(BaseModel):
    """回测配置"""

    mode: Literal["virtual", "vectorized"] = "vectorized"  # 运行模式
    symbols: list[str]
    start_date: date
    end_date: date
    initial_capital: Decimal = Decimal("100000")
    # 向量化策略参数
    ema_short: int = 5
    ema_long: int = 20
```

---

## 阶段 2：虚拟交易增强为 Paper Trading（1-2 周）

### 目标
将当前的简化虚拟交易系统增强为包含真实交易特性的 Paper Trading 系统。

### 新增文件
- `app/virtual_trade/trading_config.py` - 交易配置模型
- `app/virtual_trade/paper_trading.py` - Paper Trading 逻辑

### 改造现有文件
- `app/virtual_trade/order.py` - 支持手续费、滑点计算
- `app/virtual_trade/account.py` - 调整以支持 Paper Trading

### 交易配置模型
```python
@dataclass
class TradingConfig:
    """交易配置"""

    commission_rate: Decimal = Decimal("0.0003")  # 万三手续费
    commission_mode: str = "percentage"  # percentage/ticks

    slippage_rate: Decimal = Decimal("0.001")  # 0.1% 滑点
    slippage_mode: str = "percentage"  # percentage/ticks

    t_plus_1_enabled: bool = True  # 是否启用 T+1
    t_plus_1_delay_seconds: int = 0  # T+1 延迟

    min_trade_amount: Decimal = Decimal("100")  # 最小交易金额
    position_limit_pct: Decimal = Decimal("0.2")  # 单个标的最大持仓比例

    # 止损止盈
    default_stop_loss_pct: Decimal = Decimal("0.02")  # 默认止损比例（2%）
    default_take_profit_pct: Decimal = Decimal("0.05")  # 默认止盈比例（5%）
```

### 手续费计算
```python
def calculate_commission(
    order: TradeOrder,
    config: TradingConfig,
) -> Decimal:
    """计算手续费"""
    if config.commission_mode == "percentage":
        return order.price * order.quantity * config.commission_rate
    else:
        return order.quantity * config.commission_rate
```

### 滑点计算
```python
def calculate_slippage(
    order: TradeOrder,
    side: OrderSide,
    config: TradingConfig,
) -> Decimal:
    """计算滑点"""
    if side == OrderSide.BUY:
        # 买入时，滑点是正向的（实际成交价更高）
        slippage_price = order.price * (1 + config.slippage_rate)
    else:
        # 卖出时，滑点是负向的（实际成交价更低）
        slippage_price = order.price * (1 - config.slippage_rate)

    return abs(slippage_price - order.price) * order.quantity
```

### T+1 交易
```python
async def execute_t_plus_1_order(
    session: AsyncSession,
    order: TradeOrder,
    config: TradingConfig,
) -> None:
    """执行 T+1 交易"""
    # 1. 立即生成限价单
    limit_order = create_limit_order(...)

    # 2. 等待开仓
    await session.execute(limit_order)

    # 3. 等待条件触发
    while not condition_met():
        await asyncio.sleep(1)

    # 4. 触发条件后，立即成交
    market_order = MarketOrder(...)
    await session.execute(market_order)
```

---

## 阶段 3：重构回测引擎（1-2 个月）

### 目标
引入专业回测框架，支持混合策略（技术面 + 历史事件）。

### 技术选型

| 框架 | 优点 | 缺点 | 学习曲线 |
|--------|------|--------|----------|
| **Backtrader** | 成熟、生态丰富、文档完善 | 相对笨重 | 中等 |
| **VectorBT** | 轻量级、向量化、快速 | 功能有限 | 低 |
| **自研框架** | 完全定制 | 需要自己实现 | 高 |

### 推荐方案：**逐步迁移到 Backtrader**

**阶段 3.1（2 周）**：引入 Backtrader，保留现有引擎
```python
# app/backtest/backtrader_engine.py
from backtrader import Cerebro, Strategy

class BacktraderAdapter:
    """Backtrader 适配器"""

    def __init__(self, multi_agent_signals: pd.DataFrame):
        self.multi_agent_signals = multi_agent_signals

    def run_backtest(self, data: pd.DataFrame, config: BacktestConfig) -> BacktestResult:
        """运行 Backtrader 回测"""
        cerebro = Cerebro()

        # 添加数据
        for symbol in config.symbols:
            symbol_data = data[data['symbol'] == symbol].copy()
            cerebro.adddata(vbt.feeds.PandasData(dataname=symbol, data=symbol_data))

        # 添加策略（可以复用 Multi-Agent 信号）
        cerebro.addstrategy(self._create_strategy(config))

        # 运行回测
        results = cerebro.run()

        # 转换为统一格式
        return self._convert_results(results)
```

**阶段 3.2（4-6 周）**：逐步迁移核心逻辑到 Backtrader
- 将现有回测逻辑逐步迁移到 Backtrader 策略
- 保持两个引擎并存，逐步验证

---

## 阶段 4：历史事件管理（2-3 个月）

### 目标
建立历史事件数据库，支持混合回测（技术面 + 历史事件）。

### 新增文件
- `app/models/historical_event.py` - 历史事件模型
- `app/backtest/event_manager.py` - 事件管理器

### 历史事件模型
```python
class HistoricalEvent(BaseModel, table=True):
    """历史事件模型"""

    id: UUID = Field(default_factory=uuid7)
    event_date: date
    symbol: str

    event_type: Literal["news", "financial", "policy", "macro"]

    title: str
    content: str | None = None

    impact_score: int = Field(ge=-5, le=5)  # -5 到 5

    source: str = Field(default="llm")  # llm/manual/api
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        table_name = "historical_events"
```

### 事件影响评分
```python
def calculate_impact_score(event_type: str, content: str) -> int:
    """计算事件影响评分"""
    if event_type == "news":
        # 关键词匹配
        positive_keywords = ["利好", "超预期", "突破", "增长", "收购"]
        negative_keywords = ["利空", "不及预期", "下跌", "风险", "监管"]

        positive_count = sum(1 for kw in positive_keywords if kw in content)
        negative_count = sum(1 for kw in negative_keywords if kw in content)

        # 基础分数（中性）
        score = 0

        # 根据关键词调整
        if positive_count > negative_count:
            score = min(3, positive_count - negative_count)
        elif negative_count > positive_count:
            score = max(-3, negative_count - positive_count)

        return score
    elif event_type == "financial":
        # 财报超预期 → 正面
        if "超预期" in content or "增长" in content:
            return 2
        elif "不及预期" in content or "下滑" in content:
            return -2
        else:
            return 0

    else:
        return 0
```

### 手动维护历史事件
```python
# 管理脚本
# scripts/manage_events.py

async def add_news_event(symbol: str, title: str, content: str, impact_score: int):
    """添加新闻事件"""
    event = HistoricalEvent(
        event_date=date.today(),
        symbol=symbol,
        event_type="news",
        title=title,
        content=content,
        impact_score=impact_score,
        source="manual",
    )
    await session.add(event)

async def bulk_import_events(csv_path: str):
    """批量导入历史事件"""
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        event = HistoricalEvent(
            event_date=pd.to_datetime(row['date']),
            symbol=row['symbol'],
            event_type=row['type'],
            title=row['title'],
            content=row['content'],
            impact_score=int(row['impact']),
            source="csv_import",
        )
        await session.add(event)
```

---

## 实施计划

### Week 1-2：向量化技术面回测

#### Task 1.1: 创建回测模型
- 创建 `app/models/backtest.py`
- 定义 `VectorizedBacktestRun` 模型

#### Task 1.2: 实现向量化策略引擎
- 创建 `app/backtest/vectorized_technical.py`
- 实现 EMA 交叉策略
- 实现向量化回测引擎

#### Task 1.3: 集成到现有回测流程
- 修改 `app/backtest/engine.py`
- 添加 `mode="vectorized"` 支持
- 保持向后兼容

#### Task 1.4: 创建回测配置 API
- 在 `app/api/` 添加回测配置端点
- 支持配置向量化策略参数

### Week 3-4：Paper Trading（阶段 1）

#### Task 2.1: 创建交易配置模型
- 创建 `app/virtual_trade/trading_config.py`
- 定义 `TradingConfig` 数据类

#### Task 2.2: 实现手续费计算
- 在 `app/virtual_trade/order.py` 添加 `calculate_commission()`
- 改造 `place_buy_order()` 和 `place_sell_order()`

#### Task 2.3: 实现滑点计算
- 在 `app/virtual_trade/order.py` 添加 `calculate_slippage()`
- 集成到订单执行逻辑

#### Task 2.4: 实现 T+1 交易
- 创建 `app/virtual_trade/paper_trading.py`
- 实现 T+1 交易逻辑
- 添加条件单支持

#### Task 2.5: 集成交易配置
- 修改 Workflow 使用交易配置
- 添加配置管理端点

### Week 5-6：历史事件管理（阶段 1）

#### Task 3.1: 创建历史事件模型
- 创建 `app/models/historical_event.py`
- 定义 `HistoricalEvent` 模型

#### Task 3.2: 实现事件管理器
- 创建 `app/backtest/event_manager.py`
- 实现事件的 CRUD 操作

#### Task 3.3: 创建事件评分逻辑
- 在 `app/backtest/event_manager.py` 实现 `calculate_impact_score()`

#### Task 3.4: 创建事件导入脚本
- 创建 `scripts/manage_events.py`
- 实现批量导入功能

### Week 7-10：重构回测引擎（阶段 2）

#### Task 4.1: 引入 Backtrader
- 添加 `backtrader` 依赖
- 创建 `app/backtest/backtrader_engine.py`
- 实现适配器

#### Task 4.2: 创建 Backtrader 策略包装器
- 创建 `app/backtest/backtrader_strategy.py`
- 实现 Multi-Agent 信号到 Backtrader 的转换

#### Task 4.3: 更新回测引擎
- 修改 `app/backtest/engine.py`
- 添加 Backtrader 运行模式

#### Task 4.4: 逐步迁移
- 逐步将现有功能迁移到 Backtrader
- 保持双引擎并存

### Week 11-14：混合回测系统

#### Task 5.1: 实现混合策略引擎
- 创建 `app/backtest/hybrid_strategy.py`
- 实现技术面 + 历史事件的混合策略

#### Task 5.2: 创建参数优化系统
- 创建 `app/backtest/optimizer.py`
- 实现参数优化（遗传算法、网格搜索等）

#### Task 5.3: 集成到回测引擎
- 将混合策略集成到回测引擎
- 提供参数优化接口

### Week 15-18：完善和优化

#### Task 6.1: 完善文档
- 更新 `AGENTS.md`
- 添加回测系统文档
- 添加 Paper Trading 文档

#### Task 6.2: 性能优化
- 优化向量化计算性能
- 添加结果缓存

#### Task 6.3: 测试和验证
- 端到端测试
- 性能测试
- 修复发现的问题

---

## 文件清单

### 新增文件

```
app/
├── backtest/
│   ├── vectorized_technical.py      # 向量化技术面回测
│   ├── backtrader_engine.py        # Backtrader 适配器
│   ├── backtrader_strategy.py      # Backtrader 策略包装
│   ├── event_manager.py           # 历史事件管理
│   └── optimizer.py               # 参数优化（可选）
├── models/
│   ├── backtest.py                # 回测模型
│   └── historical_event.py        # 历史事件模型
├── virtual_trade/
│   ├── trading_config.py          # 交易配置
│   └── paper_trading.py           # Paper Trading 逻辑
└── scripts/
    └── manage_events.py          # 事件管理脚本
```

### 改造文件

```
app/
├── backtest/
│   └── engine.py                 # 添加回测模式支持
├── virtual_trade/
│   ├── account.py                 # 支持 Paper Trading
│   └── order.py                  # 添加手续费/滑点
└── workflow/
    ├── nof1_workflow_v2.py     # 使用交易配置
    └── steps/
        ├── execute_trades_step.py # 使用交易配置
```

---

## 依赖管理

### 新增依赖

```toml
[project]
dependencies = [
    "backtrader>=1.4.0",  # 可选
]
```

---

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|--------|----------|
| 系统复杂度 | 中等 | 分阶段实施，保持向后兼容 |
| 开发时间 | 2-3 个月 | 规模适中，可快速交付价值 |
| 学习曲线 | 中等 | Backtrader 有良好文档 |
| 兼容性风险 | 低 | 双引擎并存，逐步迁移 |

---

## 成功指标

### 短期（2 周）
- ✅ 向量化技术面回测上线
- ✅ 快速验证策略有效性
- ✅ 回测性能提升 10 倍以上

### 中期（2 个月）
- ✅ Paper Trading 系统上线
- ✅ 交易配置化管理
- ✅ 手续费、滑点、T+1 功能

### 长期（3-6 个月）
- ✅ 历史事件管理系统
- ✅ Backtrader 引擎集成
- ✅ 混合回测系统

---

## 后续优化建议

1. **参数优化系统**：自动寻找最优策略参数
2. **实时模拟**：使用 Paper Trading 进行实时模拟
3. **机器学习**：基于历史数据训练预测模型
4. **风险管理**：动态调整仓位和止损
5. **可视化**：增强回测报告的可视化
