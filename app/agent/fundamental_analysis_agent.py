from textwrap import dedent
from typing import Any

from agno.agent import Agent
from agno.db.postgres import AsyncPostgresDb
from agno.db.sqlite import AsyncSqliteDb
from pydantic import BaseModel

from app.agent.available_models import ModelName, get_available_model
from app.core.config import settings


class FundamentalAnalysisAgentInput(BaseModel):
    """基本面分析 Agent 输入结构。"""

    symbol: str
    financial_data: dict[str, Any]


class FundamentalAnalysisAgentOutput(BaseModel):
    """基本面分析 Agent 输出结构。"""

    fundamental_score: float
    valuation_level: str
    financial_health: str
    profitability: str
    growth_potential: str
    investment_rating: str
    analysis: str


def _get_agent_db() -> AsyncPostgresDb | AsyncSqliteDb:
    """根据配置返回 Agent 使用的数据库连接。"""
    if settings.DATABASE_TYPE == "postgresql":
        return AsyncPostgresDb(id="fundamental_analysis_agent_db", db_url=str(settings.postgre_url))
    return AsyncSqliteDb(id="fundamental_analysis_agent_db", db_file="tmp/local.db")


def _get_description() -> str:
    return "负责财报分析和基本面评估，输出基本面评分、估值判断、投资建议。"


def _get_instructions() -> str:
    return dedent("""\
        你是基本面分析专家，负责分析公司的财务状况和投资价值。

        **分析方法**:
        - 估值分析：使用 PE、PB 等估值指标评估当前估值水平
        - 财务健康度：分析负债率、现金流等财务健康指标
        - 盈利能力：使用 ROE、净利润率等指标评估盈利能力
        - 成长性：分析营收增长率、利润增长率等成长性指标

        **输出要求**:
        - 基本面评分：1-5 分，5 为优秀
        - 估值水平：低估/合理/高估
        - 财务健康度：优秀/良好/一般/较差
        - 盈利能力：优秀/良好/一般/较差
        - 成长潜力：高/中/低
        - 投资评级：强烈买入/买入/持有/卖出
        - 分析说明：简要说明基本面情况
        """)


def fundamental_analysis_agent(
    model_name: ModelName = "kimi",
    debug_mode: bool = False,
) -> Agent:
    """工厂函数：根据已注册的模型标识创建基本面分析 Agent 实例。

    Args:
        model_name: 模型标识，必须来自 `available_models` 中注册的键
        debug_mode: 调试模式，启用后会输出更多日志

    Returns:
        已配置的 Agent 实例
    """
    model = get_available_model(model_name)

    return Agent(
        name="fundamental_analysis_agent",
        model=model,
        db=_get_agent_db(),
        description=_get_description(),
        instructions=_get_instructions(),
        markdown=True,
        debug_mode=debug_mode,
        output_schema=FundamentalAnalysisAgentOutput,
        input_schema=FundamentalAnalysisAgentInput,
        use_json_mode=True,
    )


__all__ = [
    "FundamentalAnalysisAgentInput",
    "FundamentalAnalysisAgentOutput",
    "fundamental_analysis_agent",
]
