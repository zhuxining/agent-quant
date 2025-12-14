"""NOF1 工作流: 组装市场与账户快照, 调用交易 Agent 给出决策。"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from agno.db.sqlite import AsyncSqliteDb
from agno.workflow.step import Step
from agno.workflow.types import StepInput, StepOutput
from agno.workflow.workflow import Workflow

from app.agent.trader_agent import trader_agent
from app.prompt_build.account_snapshot import build_account_snapshot
from app.prompt_build.technical_snapshot import build_technical_snapshots


def _as_dict(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {}


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return "\n".join(f"{k}: {v}" for k, v in value.items())
    return str(value)


# 默认配置: 监控标的与账户
DEFAULT_SYMBOLS = ["159300.SZ", "159500.SZ", "680536.SH", "159937.SZ"]
DEFAULT_ACCOUNT_NUMBERS = ["ACC123456"]


def get_technical_snapshot_prompt(step_input: StepInput) -> StepOutput:
    """生成技术面快照 Markdown 片段。"""

    raw_input = _as_dict(step_input.input)
    technical_snapshots = raw_input.get("technical_snapshots", []) or []
    snapshots = build_technical_snapshots(list(technical_snapshots))
    return StepOutput(content=snapshots)


def get_account_snapshot_prompt(step_input: StepInput) -> StepOutput:
    """生成账户与持仓快照 Markdown 片段。"""

    raw_input = _as_dict(step_input.input)
    account_info = _as_dict(raw_input.get("account_info", {}))
    positions = raw_input.get("positions", []) or []

    snapshot_prompt = build_account_snapshot(
        return_pct=account_info.get("return_pct"),
        sharpe_ratio=account_info.get("sharpe_ratio"),
        cash_available=account_info.get("cash_available"),
        positions=positions,
        total_market_value=account_info.get("total_market_value"),
        total_unrealized_pnl=account_info.get("total_unrealized_pnl"),
    )

    return StepOutput(content=snapshot_prompt)


def run_trader_agent(step_input: StepInput) -> StepOutput:
    """调用交易 Agent, 输入为技术+账户快照拼接后的提示。"""

    technical_prompt: str = _stringify(step_input.get_step_content("Technical Snapshot"))
    account_prompt: str = _stringify(step_input.get_step_content("Account Snapshot"))

    prompt = f"{account_prompt}\n\n{technical_prompt}"

    agent = trader_agent()
    response = agent.run(prompt)

    content = getattr(response, "content", response)
    return StepOutput(content=content)


# Steps
technical_snapshot_step = Step(
    name="Technical Snapshot",
    executor=get_technical_snapshot_prompt,
    description="获取技术指标快照片段",
)

account_snapshot_step = Step(
    name="Account Snapshot",
    executor=get_account_snapshot_prompt,
    description="获取账户/持仓快照片段",
)

trader_step = Step(
    name="Trader Agent Step",
    executor=run_trader_agent,
    description="基于快照调用交易 Agent 并给出决策",
)


# Create the workflow
nof1_workflow = Workflow(
    name="nof1-workflow",
    description="生成技术与账户快照, 送入交易 Agent 输出决策",
    db=AsyncSqliteDb(id="test_agent_db", db_file="tmp/local.db"),
    steps=[
        technical_snapshot_step,
        account_snapshot_step,
        trader_step,
    ],
)


def prepare_workflow_input(
    symbols: list[str] | None = None,
    account_number: str | None = None,
) -> dict[str, Any]:
    """准备工作流输入数据。

    根据 symbols 和 account_number 获取技术快照与账户信息,
    返回符合 nof1_workflow 输入格式的字典。

    实际使用时需要:
    1. 从数据源获取技术指标快照(调用 TechnicalIndicatorFeed)
    2. 从虚拟交易系统获取账户信息与持仓

    此处为示例,返回空数据结构。
    """
    from app.data_feed.technical_indicator import TechnicalSnapshot

    symbols = symbols or DEFAULT_SYMBOLS
    account_number = account_number or DEFAULT_ACCOUNT_NUMBERS[0]

    # TODO: 实际实现时应调用数据源获取真实快照
    # 例如:
    # from app.data_feed.technical_indicator import TechnicalIndicatorFeed
    # feed = TechnicalIndicatorFeed()
    # technical_snapshots = feed.build_snapshots(symbols, ...)
    technical_snapshots: list[TechnicalSnapshot] = []

    # TODO: 实际实现时应从虚拟交易系统获取账户信息
    # 例如:
    # from app.virtual_trade.account import get_account_overview
    # account_info = get_account_overview(session, account_number)
    account_info = {
        "return_pct": 0.0,
        "sharpe_ratio": 0.0,
        "cash_available": 100000.0,
        "total_market_value": 100000.0,
        "total_unrealized_pnl": 0.0,
    }

    # TODO: 实际实现时应从虚拟交易系统获取持仓列表
    positions: list[dict[str, Any]] = []

    return {
        "technical_snapshots": technical_snapshots,
        "account_info": account_info,
        "positions": positions,
    }


__all__ = ["nof1_workflow", "prepare_workflow_input"]
