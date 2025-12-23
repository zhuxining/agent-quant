"""Step 7: 日志记录与通知。"""

from dataclasses import dataclass
from datetime import datetime

from agno.workflow.step import Step
from agno.workflow.types import StepInput, StepOutput
from loguru import logger

from app.workflow.steps.utils import parse_step_input


@dataclass
class WorkflowSummary:
    """工作流执行汇总。"""

    timestamp: str
    symbols: list[str]
    account_number: str
    agent_actions_count: int
    approved_actions_count: int
    executed_count: int
    failed_count: int
    errors: list[str]
    success: bool


async def _notification(step_input: StepInput) -> StepOutput:
    """记录工作流执行日志并发送通知。"""
    previous_outputs = step_input.previous_step_outputs or {}
    input_data = parse_step_input(step_input.input)

    symbols = input_data.get("symbols", [])
    account_number = input_data.get("account_number", "")

    # 收集各步骤信息
    agent_actions_count = 0
    agent_output = previous_outputs.get("Agent Decision")
    if agent_output and agent_output.content:
        content = agent_output.content
        if isinstance(content, dict):
            agent_actions_count = len(content.get("actions", []))
        elif hasattr(content, "actions"):
            agent_actions_count = len(getattr(content, "actions", []))

    approved_actions_count = 0
    risk_output = previous_outputs.get("Risk Check")
    if risk_output and risk_output.content and isinstance(risk_output.content, dict):
        approved_actions_count = len(risk_output.content.get("approved_actions", []))

    executed_count = 0
    failed_count = 0
    errors: list[str] = []
    trade_output = previous_outputs.get("Execute Trades")
    if trade_output and trade_output.content and isinstance(trade_output.content, dict):
        executed_count = trade_output.content.get("executed_count", 0)
        failed_count = trade_output.content.get("failed_count", 0)
        summary = trade_output.content.get("execution_summary")
        if summary and hasattr(summary, "errors"):
            errors = summary.errors

    # 构建汇总
    workflow_summary = WorkflowSummary(
        timestamp=datetime.now().isoformat(),
        symbols=symbols,
        account_number=account_number,
        agent_actions_count=agent_actions_count,
        approved_actions_count=approved_actions_count,
        executed_count=executed_count,
        failed_count=failed_count,
        errors=errors,
        success=failed_count == 0 and len(errors) == 0,
    )

    # 记录日志
    log_message = (
        f"[NOF1 Workflow 完成] "
        f"时间={workflow_summary.timestamp} "
        f"标的数={len(symbols)} "
        f"Agent建议={agent_actions_count} "
        f"风控通过={approved_actions_count} "
        f"执行成功={executed_count} "
        f"执行失败={failed_count}"
    )

    if workflow_summary.success:
        logger.success(log_message)
    else:
        logger.warning(f"{log_message} 错误={errors}")

    # TODO: 这里可以添加通知逻辑
    # - 发送邮件
    # - 发送微信/钉钉消息
    # - 写入数据库日志表

    return StepOutput(
        content={"workflow_summary": workflow_summary},
    )


notification_step = Step(
    name="Notification",
    executor=_notification,
    description="记录日志并发送通知",
    max_retries=1,
    timeout_seconds=30,
    skip_on_failure=True,
)

__all__ = ["WorkflowSummary", "notification_step"]
