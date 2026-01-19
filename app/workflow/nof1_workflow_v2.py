"""NOF1 Workflow V2: 基于 Agno Team 的量化交易决策流程。

完整流程:
1. Fetch AkShare Data   - 并行获取 A 股行情、新闻、情绪数据
2. Fetch Longport Data  - 并行获取港股行情数据
3. Fetch Account Data   - 获取账户/持仓数据
4. Multi-Agent Team Execution - 使用 Trading Team 进行多维度分析
5. Execute Trades      - 执行交易指令
6. Notification        - 日志记录与通知
"""

from datetime import datetime

from agno.db.postgres import AsyncPostgresDb
from agno.db.sqlite import AsyncSqliteDb
from agno.workflow.step import Step
from agno.workflow.workflow import Workflow
from pydantic import BaseModel

from app.agent.trading_team import create_trading_team
from app.core.config import settings
from app.workflow.steps import (
    execute_trades_step,
    fetch_account_data_step,
    fetch_market_data_step,
    notification_step,
)
from app.workflow.steps.fetch_akshare_data import fetch_akshare_data_step

# ------------------- 配置 ------------------- #

# 默认监控标的: A 股 + 港股
DEFAULT_SYMBOLS = ["000001.SZ", "159300.SZ", "588000.SH"]
DEFAULT_ACCOUNT_NUMBER = "ACC123456"


# ------------------- 工作流输入结构 ------------------- #


class NOF1WorkflowV2Input(BaseModel):
    """NOF1 Workflow V2 输入参数。"""

    symbols: list[str] = DEFAULT_SYMBOLS
    account_number: str = DEFAULT_ACCOUNT_NUMBER
    end_date: datetime | None = None  # 数据截止时间,None 表示使用实时数据


# ------------------- 数据库配置 ------------------- #


def _get_workflow_db() -> AsyncPostgresDb | AsyncSqliteDb:
    """根据配置返回工作流使用的数据库连接。"""
    if settings.DATABASE_TYPE == "postgresql":
        return AsyncPostgresDb(id="nof1_workflow_v2_db", db_url=str(settings.postgre_url))
    return AsyncSqliteDb(id="nof1_workflow_v2_db", db_file="tmp/local.db")


# ------------------- Team Step ------------------- #

# Team 作为 Workflow 的一个 Step
trading_team_step = Step(
    name="Multi-Agent Team Execution",
    agent=create_trading_team(),
    description="使用 Trading Team 进行多维度交易分析",
    max_retries=2,
    timeout_seconds=300,
)


# ------------------- NOF1 Workflow V2 定义 ------------------- #


def create_nof1_workflow_v2(
    session_id: str | None = None,
    debug_mode: bool = False,
) -> Workflow:
    """创建 NOF1 Workflow V2 实例。

    Args:
        session_id: 会话 ID, 用于状态持久化
        debug_mode: 调试模式

    Returns:
        配置好的 Workflow 实例
    """
    return Workflow(
        name="nof1-workflow-v2",
        description="NOF1 量化交易决策工作流 V2（多 Agent 团队协作）",
        db=_get_workflow_db(),
        input_schema=NOF1WorkflowV2Input,
        session_id=session_id,
        debug_mode=debug_mode,
        steps=[
            fetch_akshare_data_step,  # Step 1: 获取 A 股数据
            fetch_market_data_step,  # Step 2: 获取港股数据
            fetch_account_data_step,  # Step 3: 获取账户数据
            trading_team_step,  # Step 4: Team 分析
            execute_trades_step,  # Step 5: 执行交易
            notification_step,  # Step 6: 通知
        ],
    )


# ------------------- 便捷运行函数 ------------------- #


async def run_nof1_workflow_v2(
    symbols: list[str] | None = None,
    account_number: str | None = None,
    end_date: datetime | None = None,
    session_id: str | None = None,
    debug_mode: bool = False,
):
    """运行 NOF1 Workflow V2。

    Args:
        symbols: 监控标的列表（A 股+港股）
        account_number: 账户编号
        end_date: 数据截止时间,None 表示使用实时数据(用于回测)
        session_id: 会话 ID
        debug_mode: 调试模式

    Returns:
        Workflow 运行结果
    """
    workflow = create_nof1_workflow_v2(
        session_id=session_id,
        debug_mode=debug_mode,
    )

    workflow_input = NOF1WorkflowV2Input(
        symbols=symbols or DEFAULT_SYMBOLS,
        account_number=account_number or DEFAULT_ACCOUNT_NUMBER,
        end_date=end_date,
    )

    return await workflow.arun(input=workflow_input)


def run_workflow_v2_sync(
    symbols: list[str] | None = None,
    account_number: str | None = None,
):
    """同步执行工作流(供非异步环境使用)。"""
    import asyncio

    return asyncio.run(run_nof1_workflow_v2(symbols, account_number))


__all__ = [
    "DEFAULT_ACCOUNT_NUMBER",
    "DEFAULT_SYMBOLS",
    "NOF1WorkflowV2Input",
    "create_nof1_workflow_v2",
    "run_nof1_workflow_v2",
    "run_workflow_v2_sync",
]
