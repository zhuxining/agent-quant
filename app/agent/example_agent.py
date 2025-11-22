from typing import Literal

from agno.agent import Agent
from agno.db.postgres import AsyncPostgresDb
from agno.db.sqlite import AsyncSqliteDb
from pydantic import BaseModel, Field

from app.agent.available_models import ModelName, get_available_model
from app.core.config import settings


# ------------------- Agent 定义 ----------------- #
class AgentDefinition(BaseModel):
	"""Agent 的上下文信息,等同于 System Prompt。"""

	description: str
	instructions: str
	additional_context: str
	markdown: bool = True
	add_datetime_to_context: bool = True
	timezone_identifier: str = "Asia/Shanghai"


def get_system_prompt() -> AgentDefinition:
	"""返回上下文描述与指令（中文）。"""

	description = (
		"你是一个量化交易助理，负责基于提供的账户信息、仓位和市场数据，给出清晰的操作建议。"
	)
	instructions = (
		"1) 输出须包含明确的操作（如：buy/sell/hold、symbol、quantity 或 weight）\n"
		"2) 给出简洁的理由与置信度估计（0-1）\n"
		"3) 若需要更多数据或无法判断，说明缺失的信息。"
	)
	additional_context = ""
	return AgentDefinition(
		description=description,
		instructions=instructions,
		additional_context=additional_context,
	)


# ------------------- Agent 输入输出结构定义 ----------------- #
class AgentOutput(BaseModel):
	symbol: str
	action: Literal["buy", "sell", "hold"]
	quantity: int = Field(..., ge=0, le=100)
	reasoning: str


class AgentInput(BaseModel):
	user_promot: str


# ------------------- 创建 agno.Agent 实例 ----------------- #
def example_agent(
	model_name: ModelName = "kimi",
	debug_mode: bool = True,
) -> Agent:
	"""工厂函数：根据已注册的模型标识创建 agno.Agent 实例。

	model_name 必须来自 `app.agent.available_models` 中注册的键（例如 "kimi"、"deepseek"）。

	返回值：已配置的 Agent
	"""

	model = get_available_model(model_name)

	if settings.DATABASE_TYPE == "postgresql":
		db = AsyncPostgresDb(id="test_agent_db", db_url=str(settings.postgre_url))
	else:
		db = AsyncSqliteDb(id="test_agent_db", db_file="tmp/local.db")

	agent = Agent(
		name="example_agent",
		model=model,
		db=db,
		description=get_system_prompt().description,
		instructions=get_system_prompt().instructions,
		markdown=get_system_prompt().markdown,
		output_schema=AgentOutput,
		input_schema=AgentInput,
	)
	return agent


# ------------------- 调试 ----------------- #


async def _main():
	await example_agent().acli_app()


if __name__ == "__main__":
	import asyncio

	from app.core.config import settings

	asyncio.run(_main())
