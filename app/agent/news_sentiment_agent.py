from textwrap import dedent
from typing import Any

from agno.agent import Agent
from agno.db.postgres import AsyncPostgresDb
from agno.db.sqlite import AsyncSqliteDb
from pydantic import BaseModel

from app.agent.available_models import ModelName, get_available_model
from app.core.config import settings


class NewsSentimentAgentInput(BaseModel):
    """新闻情绪 Agent 输入结构。"""

    symbol: str
    news_data: list[dict[str, Any]]


class SentimentResult(BaseModel):
    """情绪分析结果。"""

    sentiment_score: float
    sentiment_label: str
    keywords: list[str]
    risk_factors: list[str]


class NewsSentimentAgentOutput(BaseModel):
    """新闻情绪 Agent 输出结构。"""

    results: list[SentimentResult]
    summary: str
    overall_sentiment: str


def _get_agent_db() -> AsyncPostgresDb | AsyncSqliteDb:
    """根据配置返回 Agent 使用的数据库连接。"""
    if settings.DATABASE_TYPE == "postgresql":
        return AsyncPostgresDb(id="news_sentiment_agent_db", db_url=str(settings.postgre_url))
    return AsyncSqliteDb(id="news_sentiment_agent_db", db_file="tmp/local.db")


def _get_description() -> str:
    return "负责分析股票新闻和舆情情绪，输出情绪评分、关键词摘要、风险提示。"


def _get_instructions() -> str:
    return dedent("""\
        你是新闻情绪分析专家，负责分析股票相关新闻和市场舆情。

        **分析方法**:
        - 情感分析：识别每条新闻的情绪倾向（正面/负面/中性）
        - 关键词提取：提取新闻中的关键词和主要话题
        - 风险识别：识别潜在的利好或利空因素
        - 影响评估：评估新闻对股价的短期影响

        **输出要求**:
        - 情绪评分：-1 到 1，-1 极度负面，0 中性，1 极度正面
        - 情绪标签：极度负面/负面/中性/正面/极度正面
        - 关键词：提取新闻中的主要关键词
        - 风险因素：识别潜在的风险点
        """)


def news_sentiment_agent(
    model_name: ModelName = "kimi",
    debug_mode: bool = False,
) -> Agent:
    """工厂函数：根据已注册的模型标识创建新闻情绪分析 Agent 实例。

    Args:
        model_name: 模型标识，必须来自 `available_models` 中注册的键
        debug_mode: 调试模式，启用后会输出更多日志

    Returns:
        已配置的 Agent 实例
    """
    model = get_available_model(model_name)

    return Agent(
        name="news_sentiment_agent",
        model=model,
        db=_get_agent_db(),
        description=_get_description(),
        instructions=_get_instructions(),
        markdown=True,
        debug_mode=debug_mode,
        output_schema=NewsSentimentAgentOutput,
        input_schema=NewsSentimentAgentInput,
        use_json_mode=True,
    )


__all__ = [
    "NewsSentimentAgentInput",
    "NewsSentimentAgentOutput",
    "SentimentResult",
    "news_sentiment_agent",
]
