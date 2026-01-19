from textwrap import dedent
from typing import Any

from agno.agent import Agent
from agno.db.postgres import AsyncPostgresDb
from agno.db.sqlite import AsyncSqliteDb
from pydantic import BaseModel

from app.agent.available_models import ModelName, get_available_model
from app.agent.trader_agent import AgentOutput, TradeAction
from app.core.config import settings


class DecisionSynthesisAgentInput(BaseModel):
    """决策综合 Agent 输入结构。"""

    news_result: str
    technical_result: str
    fundamental_result: str
    account_info: str


def _get_agent_db() -> AsyncPostgresDb | AsyncSqliteDb:
    """根据配置返回 Agent 使用的数据库连接。"""
    if settings.DATABASE_TYPE == "postgresql":
        return AsyncPostgresDb(id="decision_synthesis_agent_db", db_url=str(settings.postgre_url))
    return AsyncSqliteDb(id="decision_synthesis_agent_db", db_file="tmp/local.db")


def _get_description() -> str:
    return "Team Leader，汇总新闻情绪、技术分析、基本面的结论，输出最终交易决策。"


def _get_instructions() -> str:
    return dedent("""\
        你是 Team Leader，负责汇总新闻情绪、技术面、基本面的分析结论，结合账户信息，给出最终交易决策。

        **分析方法**:
        - 综合分析：综合考虑三个维度的分析结果
        - 权重分配：根据市场环境和风险偏好分配各维度权重
        - 信号过滤：过滤掉低质量或矛盾的信号
        - 风险评估：考虑账户当前仓位和风险敞口

        **输出要求**:
        - 明确的交易建议：buy/sell/hold/wait
        - 对于 buy 建议，指定标的代码、建议数量或权重
        - 对于 sell 建议，指定标的代码和数量
        - 说明决策逻辑和权重分配
        - 评估决策的置信度（0-1）
        - 识别主要风险点
        """)


def decision_synthesis_agent(
    model_name: ModelName = "kimi",
    debug_mode: bool = False,
) -> Agent:
    """工厂函数：根据已注册的模型标识创建决策综合 Agent 实例。

    Args:
        model_name: 模型标识，必须来自 `available_models` 中注册的键
        debug_mode: 调试模式，启用后会输出更多日志

    Returns:
        已配置的 Agent 实例
    """
    model = get_available_model(model_name)

    return Agent(
        name="decision_synthesis_agent",
        model=model,
        db=_get_agent_db(),
        description=_get_description(),
        instructions=_get_instructions(),
        markdown=True,
        debug_mode=debug_mode,
        output_schema=AgentOutput,
        input_schema=DecisionSynthesisAgentInput,
        use_json_mode=True,
    )


__all__ = [
    "DecisionSynthesisAgentInput",
    "decision_synthesis_agent",
]
