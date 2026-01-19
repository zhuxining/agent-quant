from textwrap import dedent
from typing import Any

from agno.agent import Agent
from agno.db.postgres import AsyncPostgresDb
from agno.db.sqlite import AsyncSqliteDb
from pydantic import BaseModel

from app.agent.available_models import ModelName, get_available_model
from app.core.config import settings


class TechnicalAnalysisAgentInput(BaseModel):
    """技术分析 Agent 输入结构。"""

    symbol: str
    technical_data: dict[str, Any]


class TechnicalAnalysisAgentOutput(BaseModel):
    """技术分析 Agent 输出结构。"""

    trend: str
    key_levels: list[dict[str, Any]]
    technical_score: float
    analysis: str


def _get_agent_db() -> AsyncPostgresDb | AsyncSqliteDb:
    """根据配置返回 Agent 使用的数据库连接。"""
    if settings.DATABASE_TYPE == "postgresql":
        return AsyncPostgresDb(id="technical_analysis_agent_db", db_url=str(settings.postgre_url))
    return AsyncSqliteDb(id="technical_analysis_agent_db", db_file="tmp/local.db")


def _get_description() -> str:
    return "负责技术指标分析，生成趋势判断、关键点位、技术面评分。"


def _get_instructions() -> str:
    return dedent("""\
        你是技术分析专家，负责分析股票的技术指标和价格走势。

        **分析方法**:
        - 趋势判断：使用 EMA、MACD、ADX 等指标判断趋势方向
        - 支撑阻力：识别关键的支撑位和阻力位
        - 形态识别：识别常见的价格形态（如头肩顶/底、双顶/底等）
        - 动量分析：使用 RSI、CCI 等指标评估超买超卖状态

        **输出要求**:
        - 趋势方向：上升/下降/横盘
        - 关键点位：支撑位、阻力位
        - 技术面评分：1-5 分，5 为强烈看涨
        - 分析说明：简要说明技术面情况
        """)


def technical_analysis_agent(
    model_name: ModelName = "kimi",
    debug_mode: bool = False,
) -> Agent:
    """工厂函数：根据已注册的模型标识创建技术分析 Agent 实例。

    Args:
        model_name: 模型标识，必须来自 `available_models` 中注册的键
        debug_mode: 调试模式，启用后会输出更多日志

    Returns:
        已配置的 Agent 实例
    """
    model = get_available_model(model_name)

    return Agent(
        name="technical_analysis_agent",
        model=model,
        db=_get_agent_db(),
        description=_get_description(),
        instructions=_get_instructions(),
        markdown=True,
        debug_mode=debug_mode,
        output_schema=TechnicalAnalysisAgentOutput,
        input_schema=TechnicalAnalysisAgentInput,
        use_json_mode=True,
    )


__all__ = [
    "TechnicalAnalysisAgentInput",
    "TechnicalAnalysisAgentOutput",
    "technical_analysis_agent",
]
