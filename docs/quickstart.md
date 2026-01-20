# Agent Quant 快速开始指南

欢迎使用 Agent Quant - 一个基于 LLM 的股票交易决策系统。本指南将帮助你快速上手。

## 📋 目录

- [系统要求](#系统要求)
- [快速安装](#快速安装)
- [配置环境](#配置环境)
- [启动服务](#启动服务)
- [使用 Multi-Agent 系统](#使用-multi-agent-系统)
- [向量化回测](#向量化回测)
- [Paper Trading](#paper-trading)
- [常用命令](#常用命令)

## 系统要求

- Python 3.14+
- [uv](https://github.com/astral-sh/uv) 包管理器
- PostgreSQL 或 SQLite 数据库
- Longport API Token (可选，用于获取市场数据）

## 快速安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd agent-quant
```

### 2. 安装依赖

```bash
# 使用 uv 安装（推荐）
uv sync

# 或使用 pip（较慢）
pip install -r requirements.txt
```

### 3. 配置环境

复制环境变量配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要参数：

```env
# 数据库配置
DATABASE_TYPE=postgresql  # 或 sqlite
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=agent_quant

# Longport API 配置（可选）
LONGPORT_APP_KEY=your_app_key
LONGPORT_APP_SECRET=your_app_secret
LONGPORT_TOKEN=your_token

# LLM 配置
OPENAI_API_KEY=your_openai_api_key
```

## 配置环境

### 数据库初始化

```bash
# 创建数据库表
uv run alembic upgrade head

# 创建初始用户和账户
uv run python -m app.core.create_db_and_tables
```

### 验证安装

```bash
# 运行代码检查
uv run ruff check --fix

# 运行测试
uv run pytest -m "not integration"
```

## 启动服务

### 开发模式

```bash
# 启动开发服务器（带热重载）
uv run serve.py
```

服务器将在 `http://localhost:8000` 启动。

### 生产模式

```bash
# 使用 granian（更快）
uv run granian serve:app.main:app
```

## 使用 Multi-Agent 系统

### 架构概览

Agent Quant 使用 Multi-Agent Team 模式进行交易决策：

```
┌─────────────────────────────────────────┐
│       Market Data Feed              │
└──────────────┬──────────────────┘
               │
        ┌──────▼──────┐
        │  Multi-Agent   │
        │    Team        │
        └──────┬───────┘
               │
    ┌──────────┴──────────────┐
    │  Trading Decisions     │
    └──────────┬─────────────┘
               │
               ▼
    ┌───────────────────────┐
    │  Paper Trading      │
    └───────────────────────┘
```

### Multi-Agent 成员

| Agent | 职责 | 输入 | 输出 |
|--------|--------|------|------|
| NewsAgent | 新闻情绪分析 | 实时新闻 | 情绪评分（-5 到 5）|
| TechAgent | 技术面分析 | K线数据、技术指标 | 趋势判断（多头/空头/震荡）|
| FundAgent | 基本面分析 | 财报数据 | 估值判断（低估/合理/高估）|
| RiskAgent | 风控评估 | 交易信号、仓位 | 风险评分（低/中/高）|
| DecisionAgent | 综合决策 | 各 Agent 输出 | 最终交易建议（买入/卖出/持有）|

### 运行 NOF1 Workflow

```bash
# 手动触发一次完整的 NOF1 工作流
uv run python -m app.workflow.nof1_workflow_v2
```

或者通过 API 触发：

```bash
curl -X POST http://localhost:8000/api/v1/workflow/nof1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["000001.SZ", "000002.SZ"],
    "period": "1d"
  }'
```

### 查看交易建议

```bash
# 获取最新的交易建议
curl http://localhost:8000/api/v1/trading/suggestions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 向量化回测

### 快速开始

向量化回测使用纯技术面指标进行快速策略验证，无需调用 LLM。

### 配置回测

创建 `backtest_config.py`:

```python
from datetime import date
from decimal import Decimal
from app.models.backtest import BacktestMode, VectorizedBacktestConfig, VectorizedStrategyConfig

config = VectorizedBacktestConfig(
    mode=BacktestMode.VECTORIZED,
    symbols=["000001.SZ"],  # 平安银行
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    initial_capital=Decimal("100000"),
    strategy_config=VectorizedStrategyConfig(
        ema_short=5,
        ema_long=20,
    ),
    commission_rate=Decimal("0.0003"),  # 万三手续费
    slippage_rate=Decimal("0.001"),  # 0.1% 滑点
)
```

### 运行回测

```python
from app.backtest import VectorizedBacktestEngine

engine = VectorizedBacktestEngine(config)
result_df, metrics = engine.run()

# 打印结果
print(f"总收益率: {float(metrics.total_return):.2%}")
print(f"最大回撤: {float(metrics.max_drawdown):.2%}")
print(f"夏普比率: {float(metrics.sharpe_ratio):.4f}")
```

### 回测策略说明

**EMA 交叉策略**：
- **金叉（买入）**：短期 EMA 上穿长期 EMA
- **死叉（卖出）**：短期 EMA 下穿长期 EMA
- **参数**：默认 EMA(5) 和 EMA(20)
- **适用场景**：趋势明显的市场，震荡市场效果较差

### 通过 API 配置回测

```bash
# 获取策略配置
curl http://localhost:8000/api/v1/backtest/config/strategies

# 保存策略配置
curl -X POST http://localhost:8000/api/v1/backtest/config/strategies \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ema_short": 10,
    "ema_long": 30
  }'
```

## Paper Trading

### 配置交易参数

Paper Trading 模块支持真实的交易特性：手续费、滑点、T+1。

### 交易配置示例

```python
from app.paper_trading.trading_config import TradingConfig

config = TradingConfig(
    commission_rate=Decimal("0.0003"),  # 万三手续费
    commission_mode="percentage",
    slippage_rate=Decimal("0.001"),  # 0.1% 滑点
    slippage_mode="percentage",
    t_plus_1_enabled=True,  # 启用 T+1
    min_trade_amount=Decimal("100"),  # 最小交易金额
    position_limit_pct=Decimal("0.2"),  # 单个标的最大持仓比例
    default_stop_loss_pct=Decimal("0.02"),  # 默认止损 2%
    default_take_profit_pct=Decimal("0.05"),  # 默认止盈 5%
)
```

### 手续费计算

支持多种手续费模式：

- **percentage**: 按成交金额百分比
- **fixed**: 固定手续费
- **tiered**: 阶梯式手续费（大额交易优惠）

### 滑点计算

支持多种滑点模式：

- **percentage**: 按成交金额百分比
- **ticks**: 按固定跳数
- **volume_weighted**: 按成交量加权的滑点

### T+1 交易规则

- **当天买入**：次日才能卖出
- **市价单优先**：T+1 规则下市价单优先成交
- **限价单**：可设定价格限制

## 常用命令

### 代码检查

```bash
# 检查所有代码
uv run ruff check

# 自动修复问题
uv run ruff check --fix
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/api/routes/test_auth.py

# 排除集成测试
uv run pytest -m "not integration"
```

### 数据库迁移

```bash
# 创建新迁移
uv run alembic revision --autogenerate -m "描述变更"

# 应用迁移
uv run alembic upgrade head

# 回滚到上一版本
uv run alembic downgrade -1
```

### 查看日志

```bash
# 查看实时日志
tail -f logs/app.log

# 查看测试日志
uv run pytest --log-cli-level=INFO
```

## API 端点

### 认证

```bash
# 登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password"
  }'
```

### 用户管理

```bash
# 获取用户信息
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 更新用户配置
curl -X PUT http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "新昵称"
  }'
```

### 标的管理

```bash
# 添加标的到关注列表
curl -X POST http://localhost:8000/api/v1/watchlist \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "000001.SZ",
    "name": "平安银行"
  }'

# 获取关注列表
curl http://localhost:8000/api/v1/watchlist \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 下一步

- 阅读 [架构文档](./architecture.md) 了解系统设计
- 查看 [NOF1 Prompt 文档](./nof1-prompt.md) 了解 Prompt 构建
- 探索 [Trader Agent 文档](./trader_agent.md) 了解 Agent 细节
- 配置你的交易标的列表
- 运行一次完整的回测，验证系统功能

## 获取帮助

- **GitHub Issues**: [项目 Issues 页面](https://github.com/your-org/agent-quant/issues)
- **文档**: 查看 `docs/` 目录下的详细文档
- **代码注释**: 主要代码都有详细的中文注释

## 注意事项

⚠️ **重要提示**：

1. **API Token 安全**：不要将 `.env` 文件提交到版本控制
2. **数据库备份**：定期备份数据库
3. **交易风险**：本系统仅供学习和研究，不构成投资建议
4. **测试环境**：使用 SQLite 进行快速测试，生产环境使用 PostgreSQL
5. **数据源限制**：AkShare 有请求频率限制，避免过快请求

---

祝你使用愉快！🚀
