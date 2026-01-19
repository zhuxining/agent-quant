from textwrap import dedent

from agno.agent import Agent
from agno.db.postgres import AsyncPostgresDb
from agno.db.sqlite import AsyncSqliteDb
from pydantic import BaseModel

from app.agent.available_models import ModelName, get_available_model
from app.agent.trader_agent import TradeAction
from app.core.config import settings


class RiskControlAgentInput(BaseModel):
    """风控 Agent 输入结构。"""

    decision: str
    account_info: str


class RiskControlAgentOutput(BaseModel):
    """风控 Agent 输出结构。"""

    passed: bool
    reason: str
    adjusted_actions: list[TradeAction]


def _get_agent_db() -> AsyncPostgresDb | AsyncSqliteDb:
    """根据配置返回 Agent 使用的数据库连接。"""
    if settings.DATABASE_TYPE == "postgresql":
        return AsyncPostgresDb(id="risk_control_agent_db", db_url=str(settings.postgre_url))
    return AsyncSqliteDb(id="risk_control_agent_db", db_file="tmp/local.db")


def _get_description() -> str:
    return "负责风险控制检查，验证交易决策的风险敞口、仓位限制、止损止盈。"


def _get_instructions() -> str:
    return dedent("""\
        你是风控专家，负责验证交易决策的风险敞口、仓位限制、止损止盈规则。

        **风控规则**:
        - 单笔交易风险 ≤ 账户总资产的 1%
        - 总仓位 ≤ 账户可用资金的 80%
        - 每个标的的持仓比例 ≤ 账户总资产的 20%
        - 必须设置止损位（建议使用 ATR 的 1-2 倍）
        - 必须设置止盈位（建议盈亏比 ≥ 2:1）
        - 连续 3 笔亏损后暂停交易，进行复盘

        **验证要求**:
        - 检查每笔交易的风险敞口
        - 验证总仓位是否超限
        - 检查止损止盈设置是否合理
        - 识别潜在的风险点
        - 如违反风控规则，拒绝交易决策并说明原因
        - 如符合风控规则，输出调整后的交易决策

        **输出要求**:
        - 是否通过风控检查（true/false）
        - 风控检查结果说明
        - 调整后的交易决策（包含止损和止盈设置）
        """)


def risk_control_agent(
    model_name: ModelName = "kimi",
    debug_mode: bool = False,
) -> Agent:
    """工厂函数：根据已注册的模型标识创建风控 Agent 实例。

    Args:
        model_name: 模型标识，必须来自 `available_models` 中注册的键
        debug_mode: 调试模式，启用后会输出更多日志

    Returns:
        已配置的 Agent 实例
    """
    model = get_available_model(model_name)

    return Agent(
        name="risk_control_agent",
        model=model,
        db=_get_agent_db(),
        description=_get_description(),
        instructions=_get_instructions(),
        markdown=True,
        debug_mode=debug_mode,
        output_schema=RiskControlAgentOutput,
        input_schema=RiskControlAgentInput,
        use_json_mode=True,
    )


__all__ = [
    "RiskControlAgentInput",
    "RiskControlAgentOutput",
    "risk_control_agent",
]
