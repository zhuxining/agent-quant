"""Step 3: 构建 Agent Prompt。"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from agno.workflow.step import Step
from agno.workflow.types import StepInput, StepOutput
from loguru import logger

from app.prompt_build.account_snapshot import build_account_snapshot
from app.prompt_build.technical_snapshot import build_technical_snapshots


def _position_to_dict(p: Any) -> dict[str, Any]:
    """将 PositionSummary 转换为字典。"""
    return {
        "symbol": p.symbol_exchange,
        "quantity": p.quantity,
        "entry_price": p.average_cost,
        "current_price": p.market_price,
        "unrealized_pnl": p.unrealized_pnl,
        "profit_target": p.profit_target,
        "stop_loss": p.stop_loss,
        "confidence": p.notes or "N/A",
    }


async def _build_prompts(step_input: StepInput) -> StepOutput:
    """构建技术面和账户的 Markdown Prompt。

    从前序步骤获取 snapshots, account, positions,
    组装成 Agent 可用的 Prompt 格式。
    """
    previous_outputs = step_input.previous_step_outputs or {}

    # 从 Step 1 获取行情数据
    market_output = previous_outputs.get("Fetch Market Data")
    snapshots = []
    if market_output and market_output.content:
        content = market_output.content
        if isinstance(content, dict):
            snapshots = content.get("snapshots", [])

    # 从 Step 2 获取账户数据
    account_output = previous_outputs.get("Fetch Account Data")
    account = None
    positions = []
    if account_output and account_output.content:
        content = account_output.content
        if isinstance(content, dict):
            account = content.get("account")
            positions = content.get("positions", [])

    # 构建技术面 Prompt
    technical_prompt = build_technical_snapshots(snapshots)

    # 构建账户 Prompt
    if account:
        position_dicts = [_position_to_dict(p) for p in positions]
        total_market_value = sum(
            (p.market_value for p in positions), start=Decimal("0")
        )
        total_unrealized_pnl = sum(
            (p.unrealized_pnl for p in positions), start=Decimal("0")
        )

        account_prompt = build_account_snapshot(
            return_pct=account.return_pct,
            sharpe_ratio=account.sharpe_ratio,
            cash_available=account.cash_available,
            positions=position_dicts,
            total_market_value=total_market_value,
            total_unrealized_pnl=total_unrealized_pnl,
        )
    else:
        account_prompt = "(账户信息不可用)"

    combined_prompt = f"{account_prompt}\n\n{technical_prompt}"

    logger.info(
        f"Prompt 构建完成: 技术面={len(technical_prompt)}字符, "
        f"账户={len(account_prompt)}字符"
    )

    return StepOutput(
        content={
            "technical_prompt": technical_prompt,
            "account_prompt": account_prompt,
            "combined_prompt": combined_prompt,
        },
    )


build_prompts_step = Step(
    name="Build Prompts",
    executor=_build_prompts,
    description="构建 Agent 输入的 Markdown Prompt",
    max_retries=1,
    timeout_seconds=10,
)

__all__ = ["build_prompts_step"]
