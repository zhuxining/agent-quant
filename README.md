# Agent Quant

获取股票市场数据,构建 Prompt 给 Agent,得到交易信号,模拟交易并记录分析结果。

## 🚀 快速开始

> 推荐使用 [uv](https://github.com/astral-sh/uv) 作为 Python 包管理与执行工具。

```bash
# 安装依赖
uv sync

# 启动服务器(默认读取 .env)
uv run serve.py

# 代码规范检查
uv run ruff check --fix

# 运行测试
uv run pytest
```

## 📂 目录速览

| 路径                | 说明                                                        |
| ------------------- | ----------------------------------------------------------- |
| `app/main.py`       | FastAPI 入口,初始化 AgentOS,挂载路由/中间件/异常处理。     |
| `app/core/`         | 配置、数据库会话、依赖与初始化数据(create_user/账户等)。   |
| `app/api/`          | 业务路由(auth/user/post 等)。                              |
| `app/agent/`        | 可用 Agent 定义与工厂(示例交易 Agent 等)。                 |
| `app/data_source/`  | 市场数据源适配层(如 Longport)。                            |
| `app/data_feed/`    | 行情拼装与指标/情绪/新闻等数据加工。                       |
| `app/prompt_build/` | Prompt 组装的片段与快照(账户/技术面等)。                    |
| `app/models/`       | SQLModel + Pydantic 模型,含虚拟交易相关实体。               |
| `app/virtual_trade/`| 虚拟交易账户、订单、持仓的业务逻辑。                       |
| `app/workflow/`     | 工作流/调度逻辑(如 nof1_workflow)。                         |
| `app/scheduler/`    | 后台定时任务(基于 APScheduler),定期运行工作流。        |
| `app/backtest/`     | 回测引擎与性能分析(与 `quantstats` 集成)。                 |
| `app/utils/`        | 响应包装、异常、日志、指标计算等跨层工具。                  |
| `tests/`            | pytest 用例、fixture、测试辅助工具。                        |
| `serve.py`          | 本地运行脚本,封装 `uvicorn`/`granian` 启动逻辑。            |
| `Dockerfile`        | 生产镜像构建配置。                                          |

更多协作规范(如测试约定、目录约束)请参考 [AGENTS.md](AGENTS.md)。

## 路线图

- Quant
  - [x] 标的列表:制定要获取数据的股票标的列表
  - [x] 行情获取:通过longport获取市场数据,通过ta-lib计算指标
  - [x] 交易账户:初始化账户信息,每次交易更新最新持仓
  - [x] 指令聚合:将股票数据、账户数据组装成 prompt
  - [x] 模型调用:将 prompt 提供给多个 Agent 交易员
  - [x] 交易执行:根据交易信号,执行交易动作并更新账户
  - [x] 运行日志:记录 Agent 的输入输出信息
  - [x] 交易回测:借助 quantstats 组合投资情况
  - [x] 自动运行:根据定时任务自动运行,并将交易信号通知出去
