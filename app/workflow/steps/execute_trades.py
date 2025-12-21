"""Step 6: 执行交易。"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from agno.workflow.step import Step
from agno.workflow.types import StepInput, StepOutput
from loguru import logger

from app.core.db import async_session_maker
from app.data_feed.technical_indicator import TechnicalIndicatorFeed
from app.virtual_trade.order import (
    OrderExecutionResult,
    place_buy_order,
    place_sell_order,
)
from app.workflow.steps.utils import parse_step_input


@dataclass
class TradeExecutionSummary:
    """交易执行汇总。"""

    total_actions: int = 0
    executed_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    results: list[OrderExecutionResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _get_current_price(symbol: str) -> Decimal | None:
    """获取标的当前价格。"""
    try:
        feed = TechnicalIndicatorFeed()
        return feed.get_latest_price(symbol)
    except Exception as e:
        logger.warning(f"获取 {symbol} 价格失败: {e}")
        return None


async def _execute_single_action(
    session: Any,
    action: Any,
    account_number: str,
) -> tuple[OrderExecutionResult | None, str | None]:
    """执行单个交易动作。"""
    action_type = getattr(action, "action", "").lower()
    symbol = getattr(action, "symbol", "")
    quantity = getattr(action, "quantity", 0) or 0

    # 调试日志
    logger.info(
        f"执行交易: symbol={symbol}, action={action_type}, quantity={quantity}, "
        f"account={account_number}"
    )

    # 跳过 hold/wait
    if action_type in ("hold", "wait"):
        return None, None

    if not symbol:
        return None, "缺少 symbol"

    if quantity <= 0:
        return None, f"{symbol}: quantity 必须为正数 (当前值: {quantity})"

    # 获取当前价格
    price = _get_current_price(symbol)
    if price is None:
        return None, f"{symbol}: 无法获取当前价格"

    logger.info(
        f"交易详情: {symbol} {action_type} {quantity} 股 @ {price}, 总金额={price * quantity}"
    )

    try:
        if action_type == "buy":
            result = await place_buy_order(
                session,
                account_number=account_number,
                symbol_exchange=symbol,
                quantity=quantity,
                price=price,
                auto_commit=True,
            )
            logger.info(f"买入成功: {symbol} x {quantity} @ {price}")
            return result, None

        elif action_type == "sell":
            result = await place_sell_order(
                session,
                account_number=account_number,
                symbol_exchange=symbol,
                quantity=quantity,
                price=price,
                auto_commit=True,
            )
            logger.info(f"卖出成功: {symbol} x {quantity} @ {price}")
            return result, None

        else:
            return None, f"未知操作类型: {action_type}"

    except Exception as e:
        error_msg = f"{symbol} {action_type} 失败: {e}"
        logger.error(error_msg)
        return None, error_msg


async def _execute_trades(step_input: StepInput) -> StepOutput:
    """执行风控通过的交易动作。"""
    previous_outputs = step_input.previous_step_outputs or {}
    input_data = parse_step_input(step_input.input)

    account_number: str = input_data.get("account_number", "")

    # 从 Risk Check 步骤获取已批准的操作
    risk_output = previous_outputs.get("Risk Check")
    approved_actions = []
    if risk_output and risk_output.content and isinstance(risk_output.content, dict):
        approved_actions = risk_output.content.get("approved_actions", [])

    summary = TradeExecutionSummary(total_actions=len(approved_actions))

    if not approved_actions:
        logger.info("无待执行的交易操作")
        return StepOutput(
            content={"execution_summary": summary},
        )

    if not account_number:
        error = "未提供 account_number, 无法执行交易"
        logger.error(error)
        summary.errors.append(error)
        return StepOutput(
            content={"execution_summary": summary},
        )

    async with async_session_maker() as session:
        for action in approved_actions:
            action_type = getattr(action, "action", "").lower()

            # 跳过 hold/wait
            if action_type in ("hold", "wait"):
                summary.skipped_count += 1
                continue

            result, error = await _execute_single_action(session, action, account_number)

            if error:
                summary.failed_count += 1
                summary.errors.append(error)
            elif result:
                summary.executed_count += 1
                summary.results.append(result)
            else:
                summary.skipped_count += 1

    logger.info(
        f"交易执行完成: 成功={summary.executed_count}, "
        f"跳过={summary.skipped_count}, 失败={summary.failed_count}"
    )

    return StepOutput(
        content={
            "execution_summary": summary,
            "executed_count": summary.executed_count,
            "failed_count": summary.failed_count,
        },
    )


execute_trades_step = Step(
    name="Execute Trades",
    executor=_execute_trades,
    description="执行风控通过的交易指令",
    max_retries=1,
    timeout_seconds=120,
    skip_on_failure=True,
)

__all__ = ["TradeExecutionSummary", "execute_trades_step"]
