"""Step 2: 获取账户和持仓数据。"""

from __future__ import annotations

from agno.workflow.step import Step
from agno.workflow.types import StepInput, StepOutput
from loguru import logger

from app.core.db import async_session_maker
from app.virtual_trade.account import AccountOverview, build_account_overview
from app.virtual_trade.position import PositionSummary, list_position_summaries


async def _fetch_account_data(step_input: StepInput) -> StepOutput:
    """获取账户和持仓信息。

    从 step_input.input 中读取 account_number,
    查询数据库获取账户概览和持仓列表。
    """
    input_data = step_input.input or {}
    if hasattr(input_data, "model_dump"):
        input_data = input_data.model_dump()

    account_number: str = input_data.get("account_number", "")

    if not account_number:
        logger.warning("未提供 account_number, 跳过账户获取")
        return StepOutput(
            content={"account": None, "positions": []},
        )

    try:
        async with async_session_maker() as session:
            account: AccountOverview = await build_account_overview(
                session, account_number=account_number
            )
            positions: list[PositionSummary] = await list_position_summaries(
                session, account_number
            )

        logger.info(
            f"获取账户 {account_number} 数据: 余额={account.cash_available}, "
            f"持仓数={len(positions)}"
        )

        return StepOutput(
            content={
                "account": account,
                "positions": positions,
                "account_number": account_number,
            },
        )
    except Exception as e:
        logger.error(f"获取账户数据失败: {e}")
        return StepOutput(
            content={"error": str(e), "account": None, "positions": []},
            success=False,
            error=str(e),
        )


fetch_account_data_step = Step(
    name="Fetch Account Data",
    executor=_fetch_account_data,
    description="获取账户和持仓信息",
    max_retries=2,
    timeout_seconds=30,
)

__all__ = ["fetch_account_data_step"]
