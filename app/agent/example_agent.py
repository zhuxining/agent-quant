from textwrap import dedent

from agno.agent import Agent
from agno.db.postgres import AsyncPostgresDb
from agno.db.sqlite import AsyncSqliteDb
from pydantic import BaseModel

from app.agent.available_models import ModelName, get_available_model
from app.core.config import settings

# ------------------- System Prompt 定义 ----------------- #


def _get_description() -> str:
    return "你是一个问答机器人"


def _get_instructions() -> str:
    return dedent("""\
        请回复10个字以内的答案
        """)


# ------------------- Agent 输入输出结构定义 ----------------- #


class AgentOutput(BaseModel):
    """示例 Agent 输出结构。"""

    answer: str


class AgentInput(BaseModel):
    """示例 Agent 输入结构。"""

    question: str


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
        use_json_mode=True,  # 使用 JSON 模式避免 response_format 中包含不可序列化的 Pydantic 元类
        output_schema=AgentOutput,
        input_schema=AgentInput,
    )


# ------------------- 调试入口 ----------------- #


async def _main():
    await example_agent(debug_mode=True).acli_app()


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())
