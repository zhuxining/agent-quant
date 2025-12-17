"""Step 5: 风控检查。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from agno.workflow.step import Step
from agno.workflow.types import StepInput, StepOutput
from loguru import logger


@dataclass
class RiskCheckResult:
    """风控检查结果。"""

    passed: bool
    original_actions: list[Any]
    approved_actions: list[Any]
    rejected_actions: list[Any]
    reasons: list[str]


# 风控参数
MAX_SINGLE_TRADE_PCT = Decimal("0.10")  # 单笔交易不超过账户 10%
MAX_POSITION_PCT = Decimal("0.30")  # 单个标的持仓不超过 30%
MIN_CASH_RESERVE_PCT = Decimal("0.05")  # 保留 5% 现金


def _check_single_action(
    action: Any,
    account: Any,
    positions: list[Any],
) -> tuple[bool, str | None]:
    """检查单个交易动作是否符合风控规则。"""
    if not action or not hasattr(action, "action"):
        return True, None

    action_type = action.action.lower() if hasattr(action, "action") else ""

    # hold/wait 不需要检查
    if action_type in ("hold", "wait"):
        return True, None

    # 买入检查
    if action_type == "buy":
        if not account:
            return False, "账户信息不可用"

        # 这里可以添加更多风控逻辑
        # 例如检查单笔金额、仓位占比等
        return True, None

    # 卖出检查
    if action_type == "sell":
        symbol = getattr(action, "symbol", "")
        quantity = getattr(action, "quantity", 0) or 0

        # 检查是否有足够持仓
        position = next((p for p in positions if p.symbol_exchange == symbol), None)
        if position is None:
            return False, f"无 {symbol} 持仓, 无法卖出"
        if quantity > position.available_quantity:
            return False, (
                f"{symbol} 可用数量 {position.available_quantity}, 请求卖出 {quantity}"
            )
        return True, None

    return True, None


async def _risk_check(step_input: StepInput) -> StepOutput:
    """执行风控检查。

    从 Agent 决策步骤获取 actions,
    检查每个动作是否符合风控规则。
    """
    previous_outputs = step_input.previous_step_outputs or {}

    # 从 Agent Decision 步骤获取输出
    agent_output = previous_outputs.get("Agent Decision")
    actions = []
    if agent_output and agent_output.content:
        content = agent_output.content
        if hasattr(content, "actions"):
            actions = content.actions
        elif isinstance(content, dict):
            actions = content.get("actions", [])

    # 从 Fetch Account Data 步骤获取账户信息
    account_output = previous_outputs.get("Fetch Account Data")
    account = None
    positions = []
    if account_output and account_output.content:
        content = account_output.content
        if isinstance(content, dict):
            account = content.get("account")
            positions = content.get("positions", [])

    approved_actions = []
    rejected_actions = []
    reasons = []

    for action in actions:
        passed, reason = _check_single_action(action, account, positions)
        if passed:
            approved_actions.append(action)
        else:
            rejected_actions.append(action)
            if reason:
                reasons.append(reason)

    result = RiskCheckResult(
        passed=len(rejected_actions) == 0,
        original_actions=actions,
        approved_actions=approved_actions,
        rejected_actions=rejected_actions,
        reasons=reasons,
    )

    if rejected_actions:
        logger.warning(f"风控拦截 {len(rejected_actions)} 个操作: {reasons}")
    else:
        logger.info(f"风控检查通过: {len(approved_actions)} 个操作待执行")

    return StepOutput(
        content={
            "risk_check_result": result,
            "approved_actions": approved_actions,
            "rejected_reasons": reasons,
        },
    )


risk_check_step = Step(
    name="Risk Check",
    executor=_risk_check,
    description="风控规则检查",
    max_retries=1,
    timeout_seconds=10,
)

__all__ = ["RiskCheckResult", "risk_check_step"]
