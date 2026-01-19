# Multi-Agent 交易系统架构演进

## Context

### Original Request
使用 agno 的 team 组装多个 Agent 来生产交易策略，news、market 等数据源使用 akshare，基于当前项目架构继续规划完善。

### Interview Summary
**Key Discussions**:
- 多 Agent 分工：新闻情绪 Agent、技术分析 Agent、基本面 Agent、决策综合 Agent（Team Leader）、风控 Agent
- 数据源策略：AkShare（A 股）+ Longport（港股）双数据源
- 市场覆盖：A 股市场（沪深两市）+ 港股市场
- 交易策略：中长期投资（基于日、周线的基本面和技术面综合分析）
- Workflow vs Team 关系：Team 作为 Workflow 的一个 Step，数据获取 steps 并行执行
- 风控机制：独立风控 Agent
- Agent 交互模式：星形拓扑（全部通过 Team Leader）
- Workflow 调整：重构 Workflow，集成 Team 作为 Step 4
- 测试策略：手动验证（放弃 TDD）

**Research Findings**:
- Agno Team 支持多 Agent 协调，Team Leader 负责分发任务和汇总结果
- AkShare 支持中国股市实时行情、新闻情绪数据、基本面数据、财报等
- Agno Workflow 支持并行执行步骤
- 现有项目已有 LongportSource、trader_agent、nof1_workflow 等组件

---

## Work Objectives

### Core Objective
重构现有交易系统，使用 Agno Team 组装多个专门 Agent 实现协同交易策略生成，集成 AkShare 数据源支持 A 股市场。

### Concrete Deliverables
- `app/data_source/akshare_source.py` - AkShare 数据源封装
- `app/agent/news_sentiment_agent.py` - 新闻情绪分析 Agent
- `app/agent/technical_analysis_agent.py` - 技术分析 Agent
- `app/agent/fundamental_analysis_agent.py` - 基本面分析 Agent
- `app/agent/decision_synthesis_agent.py` - 决策综合 Agent（Team Leader）
- `app/agent/risk_control_agent.py` - 风控 Agent
- `app/agent/trading_team.py` - Team 组装和协调逻辑
- `app/prompt_build/news_sentiment_prompt.py` - 新闻情绪 Prompt
- `app/prompt_build/fundamental_analysis_prompt.py` - 基本面 Prompt
- `app/prompt_build/decision_synthesis_prompt.py` - 决策综合 Prompt
- `app/prompt_build/risk_control_prompt.py` - 风控 Prompt
- `app/workflow/nof1_workflow_v2.py` - 重构的 Workflow
- `app/workflow/steps/fetch_akshare_data.py` - AkShare 数据获取 Step
- `app/core/config.py` - 新增 AkShare 相关配置（如需要）

### Definition of Done
- [ ] 所有 5 个 Agent 实现完成并能正常初始化
- [ ] Trading Team 能正确组装并协调 5 个 Agent
- [ ] AkShare 数据源能正常获取 A 股行情、新闻、基本面数据
- [ ] Workflow 能并行执行数据获取 steps，然后执行 Team 分析
- [ ] Team 输出符合 `AgentOutput` 结构的最终交易决策
- [ ] 手动验证：运行 workflow，各 Agent 输出正确

### Must Have
- Team 作为 Workflow 的一个 Step 集成
- 并行执行 3 个数据获取 steps
- 星形拓扑：Team Leader 协调所有子 Agent
- AkShare 数据源支持 A 股市场
- Longport 数据源保留用于港股市场

### Must NOT Have (Guardrails)
- 不要修改现有的 `trader_agent`（保留作为参考或降级方案）
- 不要修改现有 `nof1_workflow`（新增 `nof1_workflow_v2.py`）
- 不要编写自动化测试（手动验证）
- 不要实现 Agent UI/可视化界面
- 不要修改历史回测功能

---

## Verification Strategy (MANDATORY)

### Test Decision
- **Infrastructure exists**: YES (pytest 已配置)
- **User wants tests**: NO (手动验证)
- **Framework**: None

### Manual QA Only

**CRITICAL**: Without automated tests, manual verification MUST be exhaustive.

Each TODO includes detailed verification procedures:

**By Deliverable Type:**

| Type | Verification Tool | Procedure |
|------|------------------|-----------|
| **Agent/Team** | Python REPL | Import, create instance, verify initialization |
| **Data Source** | Python REPL | Call fetch methods, verify data structure |
| **Prompt** | Python REPL | Call builder functions, verify output format |
| **Workflow** | Python REPL | Run workflow async, verify step outputs |
| **Integration** | Debug Mode | Enable debug mode, trace execution flow |

**Evidence Required:**
- REPL 执行结果截图/输出
- Agent 输出的 JSON 结构
- Workflow 执行日志
- 数据获取的样本数据

---

## Task Flow

```
Task 0 (数据源并行组)
  ├─ Task 0.1: AkShare 数据源 (可并行)
  └─ Task 0.2: Prompt 架构调整 (可并行)

Task 1 (Agents 实现)
  ├─ Task 1.1: 新闻情绪 Agent
  ├─ Task 1.2: 技术分析 Agent
  ├─ Task 1.3: 基本面 Agent
  ├─ Task 1.4: 决策综合 Agent
  └─ Task 1.5: 风控 Agent

Task 2: Team 组装和协调

Task 3 (Workflow 重构)
  ├─ Task 3.1: AkShare 数据获取 Step
  └─ Task 3.2: 重构 Workflow (并行执行数据获取)

Task 4: 集成测试和验证
```

## Parallelization

| Group | Tasks | Reason |
|-------|-------|--------|
| A | 0.1, 0.2 | 独立的模块开发 |
| B | 1.1, 1.2, 1.3, 1.4, 1.5 | 独立的 Agent 实现（依赖 0.2） |
| C | 3.1, 3.2 | 相关的 Workflow 修改 |

| Task | Depends On | Reason |
|------|------------|--------|
| 2 | 1.1, 1.2, 1.3, 1.4, 1.5 | 需要所有 Agent 完成后组装 Team |
| 3.2 | 3.1, 2 | 需要 AkShare Step 和 Team 完成 |

---

## TODOs

> Implementation + Verification = ONE Task. Never separate.
> Specify parallelizability for EVERY task.

- [ ] 0.1. 创建 AkShare 数据源

  **What to do**:
  - 创建 `app/data_source/akshare_source.py`
  - 实现 `AkShareSource` 类，封装 akshare 数据获取
  - 支持的功能：
    - 获取实时行情（`stock_zh_a_spot_em`）
    - 获取历史 K 线数据（`stock_zh_a_hist`）
    - 获取新闻数据（`stock_news_em` 或相关函数）
    - 获取基本面数据（`stock_financial_analysis` 等函数）
  - 参考 `LongportSource` 的设计模式

  **Must NOT do**:
  - 不要实现港股数据获取（港股使用 Longport）
  - 不要过度封装，保持简单实用

  **Parallelizable**: YES (with 0.2)

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - `app/data_source/longport_source.py` - 数据源封装模式（初始化、方法设计、错误处理）
  - `app/data_feed/technical_indicator.py` - 技术指标 Feed 使用数据源的方式

  **API/Type References**:
  - akshare 官方文档: https://akshare.akfamily.xyz/data/stock/stock.html - 中国 A 股数据 API
  - 参考 LongportSource 的 `get_candles_frame()`, `get_realtime_quote()` 方法签名

  **Documentation References**:
  - `AGENTS.md` - 项目代码规范和约定
  - `README.md` - 项目架构说明

  **External References**:
  - AkShare GitHub: https://github.com/akfamily/akshare - 源码和示例
  - AkShare 文档: https://akshare.akfamily.xyz/ - 官方文档

  **WHY Each Reference Matters**:
  - `longport_source.py`: 遵循现有的数据源封装模式，保持代码一致性
  - AkShare 文档: 确保 API 调用正确，参数和返回值符合预期

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  *Python REPL verification:*
  ```
  >>> from app.data_source.akshare_source import AkShareSource
  >>> source = AkShareSource()
  >>> # 测试获取实时行情
  >>> quotes = source.get_spot_quotes(["000001.SZ", "600000.SH"])
  >>> print(quotes)  # 期望: 返回包含 symbol, price, volume 等字段的列表
  >>> # 测试获取 K 线数据
  >>> candles = source.get_candles_frame("000001.SZ", period="1d", count=120)
  >>> print(candles.head())  # 期望: DataFrame 包含 OHLCV 列
  >>> # 测试获取新闻数据
  >>> news = source.get_news("000001.SZ", limit=10)
  >>> print(news)  # 期望: 返回新闻列表
  ```

  **Evidence Required**:
  - [ ] REPL 执行截图（显示成功获取数据）
  - [ ] 数据结构示例输出

  **Commit**: YES
  - Message: `feat(data_source): add AkShare data source for A-share market`
  - Files: `app/data_source/akshare_source.py`

- [ ] 0.2. 调整 Prompt 架构（新增 Prompt 片段）

  **What to do**:
  - 创建以下 Prompt 片段文件：
    - `app/prompt_build/news_sentiment_prompt.py` - 新闻情绪分析 Prompt
    - `app/prompt_build/fundamental_analysis_prompt.py` - 基本面分析 Prompt
    - `app/prompt_build/decision_synthesis_prompt.py` - 决策综合 Prompt
    - `app/prompt_build/risk_control_prompt.py` - 风控 Prompt
  - 每个 Prompt 片段包含：
    - `build_xxx_prompt()` 函数，返回格式化的 Prompt 字符串
    - 参考现有的 `technical_prompt.py` 和 `account_prompt.py` 的设计

  **Must NOT do**:
  - 不要修改现有的 `technical_prompt.py` 和 `account_prompt.py`（技术分析 Agent 可以直接复用）

  **Parallelizable**: YES (with 0.1)

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - `app/prompt_build/technical_prompt.py` - 技术面 Prompt 的构建模式（模板函数、枚举、格式化）
  - `app/prompt_build/account_prompt.py` - 账户 Prompt 的构建模式（使用 dedent、格式化函数）
  - `app/prompt_build/formatters.py` - 格式化工具函数（fmt_number, fmt_pct, fmt_currency）

  **Documentation References**:
  - `app/agent/trader_agent.py:18-31` - Agent 的 instructions 和 description 示例

  **External References**:
  - 无（参考现有代码模式）

  **WHY Each Reference Matters**:
  - `technical_prompt.py` 和 `account_prompt.py`: 遵循现有的 Prompt 构建模式，确保一致性
  - `formatters.py`: 使用现有的格式化函数，保持输出格式统一

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  *Python REPL verification:*
  ```
  >>> from app.prompt_build.news_sentiment_prompt import build_news_sentiment_prompt
  >>> prompt = build_news_sentiment_prompt(symbol="000001.SZ", news_data=[...])
  >>> print(prompt)  # 期望: 格式化的 Markdown 字符串
  >>> from app.prompt_build.fundamental_analysis_prompt import build_fundamental_analysis_prompt
  >>> prompt = build_fundamental_analysis_prompt(symbol="000001.SZ", financial_data=[...])
  >>> print(prompt)  # 期望: 格式化的 Markdown 字符串
  >>> from app.prompt_build.decision_synthesis_prompt import build_decision_synthesis_prompt
  >>> prompt = build_decision_synthesis_prompt(
  ...     news_result="...",
  ...     technical_result="...",
  ...     fundamental_result="...",
  ...     account_info="..."
  ... )
  >>> print(prompt)  # 期望: 格式化的 Markdown 字符串
  >>> from app.prompt_build.risk_control_prompt import build_risk_control_prompt
  >>> prompt = build_risk_control_prompt(decision="...", account_info="...")
  >>> print(prompt)  # 期望: 格式化的 Markdown 字符串
  ```

  **Evidence Required**:
  - [ ] REPL 执行截图（显示成功构建 Prompt）
  - [ ] Prompt 输出示例

  **Commit**: YES
  - Message: `feat(prompt): add prompt fragments for multi-agent system`
  - Files: `app/prompt_build/news_sentiment_prompt.py`, `app/prompt_build/fundamental_analysis_prompt.py`, `app/prompt_build/decision_synthesis_prompt.py`, `app/prompt_build/risk_control_prompt.py`

- [ ] 1.1. 实现新闻情绪 Agent

  **What to do**:
  - 创建 `app/agent/news_sentiment_agent.py`
  - 定义 `NewsSentimentAgentInput` 和 `NewsSentimentAgentOutput` schema
  - 实现 `news_sentiment_agent()` 工厂函数，返回 `Agent` 实例
  - Agent 配置：
    - role: "负责分析股票新闻和舆情情绪，输出情绪评分、关键词摘要、风险提示"
    - instructions: 分析方法（情感分析、关键词提取、风险识别）
    - model: 使用 `get_available_model("kimi")` 或用户偏好
    - output_schema: `NewsSentimentAgentOutput`
    - input_schema: `NewsSentimentAgentInput`

  **Must NOT do**:
  - 不要直接在 Agent 内部调用 akshare（数据通过 Workflow Step 提供）

  **Parallelizable**: YES (with 1.2, 1.3, 1.4, 1.5, depends on 0.2)

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - `app/agent/trader_agent.py` - Agent 定义模式（description, instructions, input_schema, output_schema）
  - `app/agent/available_models.py` - 模型注册和获取方式

  **Prompt References**:
  - `app/prompt_build/news_sentiment_prompt.py` - 新闻情绪 Prompt 构建函数

  **Documentation References**:
  - Agno Team 文档: https://docs.agno.com/basics/teams/overview - Team 和 Agent 使用指南
  - Agno Agent 文档: https://docs.agno.com/basics/agents/overview - Agent 配置和最佳实践

  **External References**:
  - Medium: Building Multi-Agent Trading Application with Agno - 实际多 Agent 交易应用示例

  **WHY Each Reference Matters**:
  - `trader_agent.py`: 遵循现有的 Agent 定义模式
  - Agno 文档: 确保正确的 Agent 配置和使用方法

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  *Python REPL verification:*
  ```
  >>> from app.agent.news_sentiment_agent import news_sentiment_agent
  >>> agent = news_sentiment_agent()
  >>> print(agent.name)  # 期望: "news_sentiment_agent"
  >>> print(agent.description)  # 期望: 新闻情绪分析的描述
  >>> # 测试 Agent 运行（需要异步环境）
  ```

  **Evidence Required**:
  - [ ] Agent 初始化成功的截图
  - [ ] Agent 配置输出（name, description, model）

  **Commit**: YES
  - Message: `feat(agent): add news sentiment analysis agent`
  - Files: `app/agent/news_sentiment_agent.py`

- [ ] 1.2. 实现技术分析 Agent

  **What to do**:
  - 创建 `app/agent/technical_analysis_agent.py`
  - 定义 `TechnicalAnalysisAgentInput` 和 `TechnicalAnalysisAgentOutput` schema
  - 实现 `technical_analysis_agent()` 工厂函数
  - Agent 配置：
    - role: "负责技术指标分析，生成趋势判断、关键点位、技术面评分"
    - instructions: 技术分析方法（趋势判断、支撑阻力、形态识别）
    - 复用现有的 `app/prompt_build/technical_prompt.py` 作为输入构建

  **Must NOT do**:
  - 不要修改现有的 `technical_prompt.py`（直接复用）

  **Parallelizable**: YES (with 1.1, 1.3, 1.4, 1.5, depends on 0.2)

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - `app/agent/trader_agent.py` - Agent 定义模式
  - `app/prompt_build/technical_prompt.py` - 现有的技术面 Prompt 构建函数

  **Prompt References**:
  - `app/prompt_build/technical_prompt.py:build_technical_prompt()` - 技术面 Prompt 构建

  **WHY Each Reference Matters**:
  - `technical_prompt.py`: 直接复用现有的技术面 Prompt，避免重复开发

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  *Python REPL verification:*
  ```
  >>> from app.agent.technical_analysis_agent import technical_analysis_agent
  >>> agent = technical_analysis_agent()
  >>> print(agent.name)  # 期望: "technical_analysis_agent"
  >>> print(agent.description)  # 期望: 技术分析的描述
  ```

  **Evidence Required**:
  - [ ] Agent 初始化成功的截图

  **Commit**: YES
  - Message: `feat(agent): add technical analysis agent`
  - Files: `app/agent/technical_analysis_agent.py`

- [ ] 1.3. 实现基本面分析 Agent

  **What to do**:
  - 创建 `app/agent/fundamental_analysis_agent.py`
  - 定义 `FundamentalAnalysisAgentInput` 和 `FundamentalAnalysisAgentOutput` schema
  - 实现 `fundamental_analysis_agent()` 工厂函数
  - Agent 配置：
    - role: "负责财报分析和基本面评估，输出基本面评分、估值判断、投资建议"
    - instructions: 基本面分析方法（PE/PB 估值、财务健康度、盈利能力分析）

  **Parallelizable**: YES (with 1.1, 1.2, 1.4, 1.5, depends on 0.2)

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - `app/agent/trader_agent.py` - Agent 定义模式

  **Prompt References**:
  - `app/prompt_build/fundamental_analysis_prompt.py` - 基本面 Prompt 构建

  **WHY Each Reference Matters**:
  - `trader_agent.py`: 遵循现有的 Agent 定义模式

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  *Python REPL verification:*
  ```
  >>> from app.agent.fundamental_analysis_agent import fundamental_analysis_agent
  >>> agent = fundamental_analysis_agent()
  >>> print(agent.name)  # 期望: "fundamental_analysis_agent"
  ```

  **Evidence Required**:
  - [ ] Agent 初始化成功的截图

  **Commit**: YES
  - Message: `feat(agent): add fundamental analysis agent`
  - Files: `app/agent/fundamental_analysis_agent.py`

- [ ] 1.4. 实现决策综合 Agent（Team Leader）

  **What to do**:
  - 创建 `app/agent/decision_synthesis_agent.py`
  - 定义 `DecisionSynthesisAgentInput` 和 `DecisionSynthesisAgentOutput` schema
  - 实现 `decision_synthesis_agent()` 工厂函数
  - Agent 配置：
    - role: "Team Leader，汇总新闻情绪、技术分析、基本面的结论，输出最终交易决策"
    - instructions: 综合分析方法（权重分配、信号过滤、风险评估）
    - output_schema: 继承或参考现有的 `AgentOutput`

  **Must NOT do**:
  - 不要直接调用子 Agent（Team 负责协调，Agent 只负责分析）

  **Parallelizable**: YES (with 1.1, 1.2, 1.3, 1.5, depends on 0.2)

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - `app/agent/trader_agent.py:48-67` - AgentOutput 和 TradeAction 结构
  - `app/agent/trader_agent.py:83-110` - Agent 工厂函数实现

  **Prompt References**:
  - `app/prompt_build/decision_synthesis_prompt.py` - 决策综合 Prompt

  **Documentation References**:
  - Agno Team 文档: https://docs.agno.com/basics/teams/building-teams - Team Leader 配置

  **WHY Each Reference Matters**:
  - `trader_agent.py`: AgentOutput 结构确保与现有系统兼容

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  *Python REPL verification:*
  ```
  >>> from app.agent.decision_synthesis_agent import decision_synthesis_agent
  >>> agent = decision_synthesis_agent()
  >>> print(agent.name)  # 期望: "decision_synthesis_agent"
  ```

  **Evidence Required**:
  - [ ] Agent 初始化成功的截图

  **Commit**: YES
  - Message: `feat(agent): add decision synthesis agent (team leader)`
  - Files: `app/agent/decision_synthesis_agent.py`

- [ ] 1.5. 实现风控 Agent

  **What to do**:
  - 创建 `app/agent/risk_control_agent.py`
  - 定义 `RiskControlAgentInput` 和 `RiskControlAgentOutput` schema
  - 实现 `risk_control_agent()` 工厂函数
  - Agent 配置：
    - role: "负责风险控制检查，验证交易决策的风险敞口、仓位限制、止损止盈"
    - instructions: 风控规则（单笔风险≤账户1%、总仓位限制、止损检查）

  **Parallelizable**: YES (with 1.1, 1.2, 1.3, 1.4, depends on 0.2)

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - `app/agent/trader_agent.py` - Agent 定义模式

  **Prompt References**:
  - `app/prompt_build/risk_control_prompt.py` - 风控 Prompt

  **Documentation References**:
  - `app/workflow/steps/risk_check.py` - 现有的风控 Step，参考风控逻辑

  **WHY Each Reference Matters**:
  - `risk_check.py`: 理解现有风控逻辑，避免重复实现

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  *Python REPL verification:*
  ```
  >>> from app.agent.risk_control_agent import risk_control_agent
  >>> agent = risk_control_agent()
  >>> print(agent.name)  # 期望: "risk_control_agent"
  ```

  **Evidence Required**:
  - [ ] Agent 初始化成功的截图

  **Commit**: YES
  - Message: `feat(agent): add risk control agent`
  - Files: `app/agent/risk_control_agent.py`

- [ ] 2. 组装 Trading Team

  **What to do**:
  - 创建 `app/agent/trading_team.py`
  - 实现 `create_trading_team()` 工厂函数，返回 `Team` 实例
  - Team 配置：
    - name: "trading-team"
    - members: 包含上述 5 个 Agent
    - leader: `decision_synthesis_agent()` 作为 Team Leader
    - instructions: Team 协调逻辑（星形拓扑：Leader 分配任务 → 子 Agent 执行 → Leader 汇总）
    - mode: "coordinate" 模式（Leader 协调模式）

  **Must NOT do**:
  - 不要在 Team 内部实现数据获取逻辑（数据由 Workflow 提供）

  **Parallelizable**: NO (depends on 1.1, 1.2, 1.3, 1.4, 1.5)

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - `app/agent/trader_agent.py:83-110` - Agent 工厂函数模式

  **Documentation References**:
  - Agno Team 文档: https://docs.agno.com/basics/teams/overview - Team 概念和用法
  - Agno Team 文档: https://docs.agno.com/basics/teams/building-teams - Team 构建指南
  - Medium: HPE Developer Blog - Part 5: Agentic AI: Team coordination mode in action - Team 协调模式示例

  **Code Examples**:
  - Medium: Building Multi-Agent Trading Application with Agno Framework - 实际多 Agent 交易应用代码示例

  **WHY Each Reference Matters**:
  - Agno Team 文档: 确保正确的 Team 配置和协调模式
  - Medium 示例: 参考实际的多 Agent 交易应用实现

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  *Python REPL verification:*
  ```
  >>> from app.agent.trading_team import create_trading_team
  >>> team = create_trading_team()
  >>> print(team.name)  # 期望: "trading-team"
  >>> print(len(team.members))  # 期望: 5（包含所有子 Agent）
  >>> print([m.name for m in team.members])  # 期望: 包含所有 Agent 的名称
  ```

  **Evidence Required**:
  - [ ] Team 初始化成功的截图
  - [ ] Team 成员列表输出

  **Commit**: YES
  - Message: `feat(team): create trading team with 5 agents`
  - Files: `app/agent/trading_team.py`

- [ ] 3.1. 创建 AkShare 数据获取 Step

  **What to do**:
  - 创建 `app/workflow/steps/fetch_akshare_data.py`
  - 实现 `fetch_akshare_data_step`，返回 `Step` 实例
  - Step 功能：
    - 从 WorkflowInput 中获取 symbols（A 股标的列表）
    - 调用 `AkShareSource` 获取数据：
      - 实时行情
      - 新闻数据
      - 基本面数据
    - 返回 `StepOutput`，包含所有数据的字典结构

  **Must NOT do**:
  - 不要在这个 Step 中获取港股数据（港股数据由 Longport Step 获取）

  **Parallelizable**: YES (with 3.2, depends on 0.1)

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - `app/workflow/steps/fetch_market_data.py` - 现有的市场数据获取 Step
  - `app/workflow/steps/fetch_account_data.py` - 现有的账户数据获取 Step
  - `app/workflow/steps/build_prompts.py:28-81` - Step executor 函数实现模式

  **Data Source References**:
  - `app/data_source/akshare_source.py` - AkShare 数据源 API

  **Documentation References**:
  - Agno Workflow Step 文档: https://docs.agno.com/basics/workflows/steps - Step 配置和实现

  **WHY Each Reference Matters**:
  - `fetch_market_data.py`: 遵循现有的 Step 实现模式
  - `akshare_source.py`: 正确使用 AkShare 数据源 API

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  *Python REPL verification:*
  ```
  >>> from app.workflow.steps.fetch_akshare_data import fetch_akshare_data_step
  >>> from agno.workflow.types import StepInput
  >>> step_input = StepInput(workflow_input={"symbols": ["000001.SZ"]})
  >>> output = await fetch_akshare_data_step.executor(step_input)
  >>> print(output.content)  # 期望: 包含 market_data, news_data, fundamental_data 的字典
  ```

  **Evidence Required**:
  - [ ] Step 执行成功的截图
  - [ ] Step 输出结构示例

  **Commit**: YES
  - Message: `feat(workflow): add AkShare data fetch step`
  - Files: `app/workflow/steps/fetch_akshare_data.py`

- [ ] 3.2. 重构 Workflow（并行数据获取 + Team 执行）

  **What to do**:
  - 创建 `app/workflow/nof1_workflow_v2.py`
  - 定义 `NOF1WorkflowV2Input` schema
  - 实现重构的 Workflow：
    - **并行阶段**（3 个 steps）：
      - `fetch_akshare_data_step` - 获取 A 股数据
      - `fetch_market_data_step` (复用) - 获取港股数据
      - `fetch_account_data_step` (复用) - 获取账户数据
    - **Team 分析阶段**（1 个 step）：
      - 使用 `create_trading_team()` 创建 Team step
      - Team 接收所有数据源的输出
      - Team 协调 5 个 Agent 并输出最终决策
    - **执行阶段**（复用现有 steps）：
      - `execute_trades_step`
      - `notification_step`
  - 实现 `run_nof1_workflow_v2()` 函数

  **Must NOT do**:
  - 不要修改现有的 `nof1_workflow.py`（新增 `nof1_workflow_v2.py`）

  **Parallelizable**: NO (depends on 3.1, 2)

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - `app/workflow/nof1_workflow.py:75-104` - Workflow 构建模式
  - `app/workflow/nof1_workflow.py:110-140` - Workflow 运行函数

  **Step References**:
  - `app/workflow/steps/fetch_akshare_data.py` - AkShare 数据获取 Step
  - `app/workflow/steps/fetch_market_data.py` - Longport 数据获取 Step（需调整为仅获取港股）
  - `app/workflow/steps/fetch_account_data.py` - 账户数据获取 Step
  - `app/workflow/steps/execute_trades.py` - 交易执行 Step
  - `app/workflow/steps/notification.py` - 通知 Step

  **Team References**:
  - `app/agent/trading_team.py:create_trading_team()` - Trading Team 工厂函数

  **Documentation References**:
  - Agno Workflow 文档: https://docs.agno.com/basics/workflows/overview - Workflow 概念和配置
  - Agno Workflow 文档: https://docs.agno.com/basics/workflows/running-workflows - Workflow 运行指南

  **WHY Each Reference Matters**:
  - `nof1_workflow.py`: 遵循现有的 Workflow 构建模式
  - 各个 Step: 正确集成所有步骤

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  *Python REPL verification:*
  ```
  >>> from app.workflow.nof1_workflow_v2 import run_nof1_workflow_v2
  >>> result = await run_nof1_workflow_v2(
  ...     symbols=["000001.SZ", "159300.SZ"],
  ...     account_number="ACC123456",
  ...     debug_mode=True
  ... )
  >>> print(result)  # 期望: Workflow 执行结果，包含各步骤的输出
  ```

  **Evidence Required**:
  - [ ] Workflow 执行成功的日志截图
  - [ ] Workflow 输出结构示例

  **Commit**: YES
  - Message: `feat(workflow): add NOF1 workflow v2 with multi-agent team`
  - Files: `app/workflow/nof1_workflow_v2.py`

- [ ] 4. 集成测试和验证

  **What to do**:
  - 手动运行 `nof1_workflow_v2`
  - 验证各组件集成：
    - AkShare 数据源正常工作
    - 5 个 Agent 正常初始化和执行
    - Team 协调逻辑正确
    - Workflow 正确执行所有步骤
    - 最终输出符合 `AgentOutput` 结构
  - 记录执行日志和输出结果
  - 修复发现的问题

  **Must NOT do**:
  - 不要编写自动化测试用例
  - 不要修改核心逻辑（仅修复 bug）

  **Parallelizable**: NO (depends on 3.2)

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References**:
  - 无（集成测试）

  **Documentation References**:
  - 无（手动验证）

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  *Complete workflow run:*
  ```
  # 在项目根目录执行
  >>> import asyncio
  >>> from app.workflow.nof1_workflow_v2 import run_nof1_workflow_v2
  >>> result = asyncio.run(run_nof1_workflow_v2(
  ...     symbols=["000001.SZ", "159300.SZ"],
  ...     account_number="ACC123456",
  ...     debug_mode=True
  ... ))
  ```

  **验证要点**:
  - [ ] AkShare 数据获取成功（检查日志）
  - [ ] 5 个 Agent 执行成功（检查 Team 输出）
  - [ ] Team 输出包含交易决策（检查 result）
  - [ ] 无错误或异常（检查日志）

  **Evidence Required**:
  - [ ] 完整的 Workflow 执行日志
  - [ ] Team 输出截图
  - [ ] 最终交易决策截图

  **Commit**: YES
  - Message: `fix: integration testing and bug fixes`
  - Files: (修改的文件)

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 0.1 | `feat(data_source): add AkShare data source` | `app/data_source/akshare_source.py` | REPL 测试 |
| 0.2 | `feat(prompt): add prompt fragments for multi-agent system` | `app/prompt_build/*.py` | REPL 测试 |
| 1.1 | `feat(agent): add news sentiment analysis agent` | `app/agent/news_sentiment_agent.py` | REPL 测试 |
| 1.2 | `feat(agent): add technical analysis agent` | `app/agent/technical_analysis_agent.py` | REPL 测试 |
| 1.3 | `feat(agent): add fundamental analysis agent` | `app/agent/fundamental_analysis_agent.py` | REPL 测试 |
| 1.4 | `feat(agent): add decision synthesis agent (team leader)` | `app/agent/decision_synthesis_agent.py` | REPL 测试 |
| 1.5 | `feat(agent): add risk control agent` | `app/agent/risk_control_agent.py` | REPL 测试 |
| 2 | `feat(team): create trading team with 5 agents` | `app/agent/trading_team.py` | REPL 测试 |
| 3.1 | `feat(workflow): add AkShare data fetch step` | `app/workflow/steps/fetch_akshare_data.py` | REPL 测试 |
| 3.2 | `feat(workflow): add NOF1 workflow v2 with multi-agent team` | `app/workflow/nof1_workflow_v2.py` | 完整 Workflow 运行 |
| 4 | `fix: integration testing and bug fixes` | (修改的文件) | 完整 Workflow 运行 |

---

## Success Criteria

### Verification Commands

```bash
# 测试 AkShare 数据源
python -c "from app.data_source.akshare_source import AkShareSource; s = AkShareSource(); print(s.get_spot_quotes(['000001.SZ']))"

# 测试 Agent 初始化
python -c "from app.agent.news_sentiment_agent import news_sentiment_agent; a = news_sentiment_agent(); print(a.name)"

# 测试 Team 初始化
python -c "from app.agent.trading_team import create_trading_team; t = create_trading_team(); print(len(t.members))"

# 运行完整 Workflow（异步）
python -c "import asyncio; from app.workflow.nof1_workflow_v2 import run_nof1_workflow_v2; asyncio.run(run_nof1_workflow_v2(symbols=['000001.SZ'], debug_mode=True))"
```

### Final Checklist
- [ ] 所有 5 个 Agent 实现完成并能正常初始化
- [ ] Trading Team 能正确组装并协调 5 个 Agent
- [ ] AkShare 数据源能正常获取 A 股行情、新闻、基本面数据
- [ ] Workflow 能并行执行 3 个数据获取 steps
- [ ] Team 输出符合 `AgentOutput` 结构的最终交易决策
- [ ] 手动验证：运行 workflow，各 Agent 输出正确
