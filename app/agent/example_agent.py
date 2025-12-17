from textwrap import dedent
from typing import Literal

from agno.agent import Agent
from agno.db.postgres import AsyncPostgresDb
from agno.db.sqlite import AsyncSqliteDb
from pydantic import BaseModel, Field

from app.agent.available_models import ModelName, get_available_model
from app.core.config import settings

# ------------------- System Prompt 定义 ----------------- #


def _get_description() -> str:
    return "你是一个量化交易助理,负责基于提供的账户信息、仓位和市场数据,给出清晰的操作建议。"


def _get_instructions() -> str:
    return dedent("""\
        请基于用户提供的信息,严格按照以下要求输出建议:
        1) 输出须包含明确的操作(如:buy/sell/hold、symbol、quantity 或 weight)
        2) 给出简洁的理由与置信度估计(0-1)
        3) 若需要更多数据或无法判断,说明缺失的信息。
        """)


# ------------------- Agent 输入输出结构定义 ----------------- #


class AgentOutput(BaseModel):
    """示例 Agent 输出结构。"""

    symbol: str
    action: Literal["buy", "sell", "hold"]
    quantity: int = Field(..., ge=0, le=100)
    reasoning: str


class AgentInput(BaseModel):
    """示例 Agent 输入结构。"""

    user_prompt: str


# ------------------- 数据库连接 ----------------- #


def _get_agent_db() -> AsyncPostgresDb | AsyncSqliteDb:
    """根据配置返回 Agent 使用的数据库连接。"""
    if settings.DATABASE_TYPE == "postgresql":
        return AsyncPostgresDb(id="example_agent_db", db_url=str(settings.postgre_url))
    return AsyncSqliteDb(id="example_agent_db", db_file="tmp/local.db")


# ------------------- 创建 agno.Agent 实例 ----------------- #


def example_agent(
    model_name: ModelName = "kimi",
    debug_mode: bool = False,
) -> Agent:
    """工厂函数:根据已注册的模型标识创建示例 agno.Agent 实例。

    Args:
        model_name: 模型标识, 必须来自 `available_models` 中注册的键
        debug_mode: 调试模式, 启用后会输出更多日志

    Returns:
        已配置的 Agent 实例
    """
    model = get_available_model(model_name)

    return Agent(
        name="example_agent",
        model=model,
        db=_get_agent_db(),
        description=_get_description(),
        instructions=_get_instructions(),
        markdown=True,
        debug_mode=debug_mode,
        output_schema=AgentOutput,
        input_schema=AgentInput,
    )


# ------------------- 调试入口 ----------------- #


async def _main():
    await example_agent(debug_mode=True).acli_app()


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
