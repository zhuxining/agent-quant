# Draft: Multi-Agent 交易系统架构演进

## 用户需求
使用 agno 的 team 组装多个 Agent 来生产交易策略，news、market 等数据源使用 akshare，基于当前项目架构继续规划完善。

## 当前架构分析

### 现有组件
- **Agent**: `trader_agent` - 单一交易 Agent，接收技术面和账户数据
- **Workflow**: `nof1_workflow` - 7 步骤流水线（获取行情 → 获取账户 → 构建 Prompt → Agent 决策 → 风控检查 → 执行交易 → 通知）
- **数据源**: `LongportSource` - 基于 Longport API 的行情数据
- **Prompt 组装**: `app/prompt_build/` - 分为技术面（`technical_prompt.py`）和账户（`account_prompt.py`）
- **项目已安装**: akshare >=1.18.6, agno >=2.3.26

### Agno Team 能力（从文档研究）
- Team 可包含多个 Agent 或 sub-team
- Team leader 负责协调和分发任务
- 支持专门的 Agent 处理不同子任务
- 有实际的多 Agent 交易应用示例（Reasoning Team, HackerNews Team 等）

### AkShare 数据能力（从文档研究）
- 支持中国股市实时行情、历史价格数据
- 支持新闻情绪数据（`stock_news_em` 相关函数）
- 支持市场情绪指标
- 支持基本面数据、财报等
- 支持多个周期（分钟、小时、日线等）

## 技术决策（已确认）

### 多 Agent 分工
1. **新闻情绪 Agent** - 负责新闻情感分析、市场情绪判断、舆情监控
2. **技术分析 Agent** - 负责技术指标分析（K线、EMA、MACD、RSI 等），生成技术面报告
3. **基本面 Agent** - 负责财报分析、估值分析、基本面评估
4. **决策综合 Agent**（Team Leader）- 负责最终决策综合，汇总各 Agent 结论，输出交易信号

### 数据源策略
- **AkShare** - 提供 A 股市场数据（新闻情绪、实时行情、基本面等）
- **Longport** - 提供港股市场数据（K线、实时行情等）
- 双数据源并行，根据市场类型选择对应数据源

### 市场覆盖
- **A 股市场**（沪深两市） - 使用 AkShare
- **港股市场** - 使用 Longport

### 交易策略
- **中长期投资** - 基于日、周线的基本面和技术面综合分析

## 架构设计要点（已确认）

### Team 协调策略（星形拓扑）
```
Team Leader (决策综合 Agent)
    ├── 分配任务给新闻情绪 Agent
    ├── 分配任务给技术分析 Agent
    ├── 分配任务给基本面分析 Agent
    ├── 分配任务给风控 Agent
    └── 汇总所有 Agent 的结论，输出最终交易决策
```

### Workflow vs Team 的集成关系
**Team 作为 Workflow 的一个 Step，数据获取 steps 并行执行**：

```
Workflow (外层流程编排)
  ├─ [并行阶段 - 数据获取]
  │     ├─ Step 1: Fetch Market Data (AkShare)      → 获取 A 股行情、新闻、情绪数据
  │     ├─ Step 2: Fetch Market Data (Longport)     → 获取港股行情数据
  │     └─ Step 3: Fetch Account Data                → 获取账户/持仓数据（保持不变）
  ├─ Step 4: Multi-Agent Team Execution              → [Team 作为 Step，依赖前面所有数据]
  │     ├─ Team Leader (决策综合 Agent)
  │     │     ├─ 调用新闻情绪 Agent
  │     │     ├─ 调用技术分析 Agent
  │     │     ├─ 调用基本面 Agent
  │     │     ├─ 调用风控 Agent
  │     │     └─ 汇总结论，输出最终交易决策
  │     └─ 返回 Team 决策结果给 Workflow
  ├─ Step 5: Execute Trades                        → 执行交易指令（保持不变）
  └─ Step 6: Notification                         → 日志记录与通知（保持不变）
```

### Workflow 重构
将原有的 7 步骤 workflow 调整为 6 步骤：
1. **Fetch Market Data (AkShare)** - 新增：获取 A 股行情、新闻、情绪数据
2. **Fetch Market Data (Longport)** - 调整：仅获取港股行情数据
3. **Fetch Account Data** - 保持不变：获取账户/持仓数据
4. **Multi-Agent Team Execution** - 替换原 Agent Decision Step：使用 agno.Team 替代原有的单 Agent
5. **Execute Trades** - 保持不变：执行交易指令
6. **Notification** - 保持不变：日志记录与通知

### 5 个 Agent 角色定义
1. **新闻情绪 Agent** (news_sentiment_agent)
   - 输入：标的列表、新闻数据
   - 输出：情绪评分、关键词摘要、风险提示
   - 数据源：AkShare

2. **技术分析 Agent** (technical_analysis_agent)
   - 输入：标的列表、K线数据、技术指标
   - 输出：趋势判断、关键点位、技术面评分
   - 数据源：AkShare (A股) / Longport (港股)

3. **基本面分析 Agent** (fundamental_analysis_agent)
   - 输入：标的列表、财报数据、估值指标
   - 输出：基本面评分、投资建议、估值判断
   - 数据源：AkShare

4. **决策综合 Agent** (decision_synthesis_agent) - Team Leader
   - 输入：上述 3 个 Agent 的分析结论 + 账户信息
   - 输出：最终交易决策（buy/sell/hold/weight）
   - 协调：汇总各 Agent 结论，进行综合判断

5. **风控 Agent** (risk_control_agent)
   - 输入：决策综合 Agent 的初步决策 + 账户信息
   - 输出：风控检查结果、调整后的交易决策
   - 作用：检查风险敞口、仓位限制、止损止盈

### Prompt 架构调整
为每个 Agent 设计专门的 Prompt 片段：
- `app/prompt_build/news_sentiment_prompt.py` - 新闻情绪分析 Prompt
- `app/prompt_build/technical_analysis_prompt.py` - 技术分析 Prompt（基于现有的 technical_prompt.py）
- `app/prompt_build/fundamental_analysis_prompt.py` - 基本面分析 Prompt
- `app/prompt_build/decision_synthesis_prompt.py` - 决策综合 Prompt
- `app/prompt_build/risk_control_prompt.py` - 风控 Prompt

### 数据分发机制
- 根据 market_type (A股/港股) 选择对应数据源
- A 股：全部使用 AkShare
- 港股：使用 Longport，新闻/情绪可考虑 AkShare（如支持）

## 测试策略
- **手动验证**（不编写自动化测试）
- 验证方式：
  - 手动运行 workflow，检查各 Agent 输出
  - 验证 AkShare 数据获取是否正常
  - 验证 Team 协调逻辑是否正确
  - 使用日志和调试模式验证数据流

## 范围边界
- INCLUDE:
  - 多 Agent Team 架构设计
  - AkShare 数据源集成（app/data_source/akshare_source.py）
  - 5 个专门 Agent 的实现（app/agent/）
  - 新的 Prompt 片段（app/prompt_build/）
  - Workflow 重构（app/workflow/nof1_workflow_v2.py）
  - Team 协调逻辑和数据流设计
  - 完整的测试覆盖（TDD）
- EXCLUDE:
  - Agent UI/可视化界面
  - Agent 性能优化和调优
  - 历史回测功能改造（可在后续优化）
