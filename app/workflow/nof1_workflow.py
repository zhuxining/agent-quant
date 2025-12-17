"""NOF1 工作流: 基于 Agno Workflow 的量化交易决策流程。

完整流程:
1. Fetch Market Data   - 获取技术指标数据
2. Fetch Account Data  - 获取账户/持仓数据
3. Build Prompts       - 构建 Agent Prompt
4. Agent Decision      - 调用 Agent 生成交易决策
5. Risk Check          - 风控规则检查
6. Execute Trades      - 执行交易指令
7. Notification        - 日志记录与通知
"""

from __future__ import annotations

from agno.db.postgres import AsyncPostgresDb
from agno.db.sqlite import AsyncSqliteDb
from agno.workflow.step import Step
from agno.workflow.workflow import Workflow
from pydantic import BaseModel

from app.agent.trader_agent import trader_agent
from app.core.config import settings
from app.workflow.steps import (
    build_prompts_step,
    execute_trades_step,
    fetch_account_data_step,
    fetch_market_data_step,
    notification_step,
    risk_check_step,
)

# ------------------- 配置 ------------------- #

DEFAULT_SYMBOLS = ["159300.SZ", "159500.SZ", "680536.SH", "159937.SZ"]
DEFAULT_ACCOUNT_NUMBER = "ACC123456"


# ------------------- 工作流输入结构 ------------------- #


class NOF1WorkflowInput(BaseModel):
    """NOF1 工作流输入参数。"""

    symbols: list[str] = DEFAULT_SYMBOLS
    account_number: str = DEFAULT_ACCOUNT_NUMBER


# ------------------- 数据库配置 ------------------- #


def _get_workflow_db() -> AsyncPostgresDb | AsyncSqliteDb:
    """根据配置返回工作流使用的数据库连接。"""
    if settings.DATABASE_TYPE == "postgresql":
        return AsyncPostgresDb(id="nof1_workflow_db", db_url=str(settings.postgre_url))
    return AsyncSqliteDb(id="nof1_workflow_db", db_file="tmp/workflow.db")


# ------------------- Agent Decision Step ------------------- #

# Step 4 使用 trader_agent, 直接集成到 workflow
agent_decision_step = Step(
    name="Agent Decision",
    agent=trader_agent(),
    description="调用 Agent 生成交易决策",
    max_retries=2,
    timeout_seconds=120,
)


# ------------------- NOF1 Workflow 定义 ------------------- #


def create_nof1_workflow(
    session_id: str | None = None,
    debug_mode: bool = False,
) -> Workflow:
    """创建 NOF1 工作流实例。

    Args:
        session_id: 会话 ID, 用于状态持久化
        debug_mode: 调试模式

    Returns:
        配置好的 Workflow 实例
    """
    return Workflow(
        name="nof1-workflow",
        description="NOF1 量化交易决策工作流",
        db=_get_workflow_db(),
        input_schema=NOF1WorkflowInput,
        session_id=session_id,
        debug_mode=debug_mode,
        steps=[
            fetch_market_data_step,  # Step 1: 获取行情
            fetch_account_data_step,  # Step 2: 获取账户
            build_prompts_step,  # Step 3: 构建 Prompt
            agent_decision_step,  # Step 4: Agent 决策
            risk_check_step,  # Step 5: 风控检查
            execute_trades_step,  # Step 6: 执行交易
            notification_step,  # Step 7: 通知
        ],
    )


# ------------------- 便捷运行函数 ------------------- #


async def run_nof1_workflow(
    symbols: list[str] | None = None,
    account_number: str | None = None,
    session_id: str | None = None,
    debug_mode: bool = False,
):
    """运行 NOF1 工作流。

    Args:
        symbols: 监控标的列表
        account_number: 账户编号
        session_id: 会话 ID
        debug_mode: 调试模式

    Returns:
        Workflow 运行结果
    """
    workflow = create_nof1_workflow(
        session_id=session_id,
        debug_mode=debug_mode,
    )

    workflow_input = NOF1WorkflowInput(
        symbols=symbols or DEFAULT_SYMBOLS,
        account_number=account_number or DEFAULT_ACCOUNT_NUMBER,
    )

    return await workflow.arun(input=workflow_input)


def run_workflow_sync(
    symbols: list[str] | None = None,
    account_number: str | None = None,
):
    """同步执行工作流(供非异步环境使用)。"""
    import asyncio

    return asyncio.run(run_nof1_workflow(symbols, account_number))


__all__ = [
    "DEFAULT_ACCOUNT_NUMBER",
    "DEFAULT_SYMBOLS",
    "NOF1WorkflowInput",
    "create_nof1_workflow",
    "run_nof1_workflow",
    "run_workflow_sync",
]
