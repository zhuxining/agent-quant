from agno.agent import Agent
from agno.db.postgres import AsyncPostgresDb
from agno.db.sqlite import AsyncSqliteDb
from pydantic import BaseModel

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


class AgentInput(BaseModel):
	"""Agent 输入结构。

	- account_number: 账户标识
	- symbols: 关注的标的列表（符号形式，例如 AAPL）
	- timeframe: 文本描述的时间粒度（如 1h、1d）
	- extra: 可选的额外上下文
	"""

	account_number: str
	symbols: list[str]
	timeframe: str = "1d"
	extra: str | None = None


class TradeAction(BaseModel):
	symbol: str
	action: str  # buy/sell/hold
	quantity: int | None = None
	weight: float | None = None


class AgentOutput(BaseModel):
	"""Agent 输出结构。

	- actions: 建议的操作列表
	- explanation: 文本说明
	- confidence: 置信度（0-1）
	- raw: 原始模型返回以便调试
	"""

	actions: list[TradeAction]
	explanation: str
	confidence: float | None = None


# ------------------- 创建 agno.Agent 实例 ----------------- #


def trader_agent(
	model_name: ModelName = "deepseek",
	debug_mode: bool = False,
) -> Agent:
	"""工厂函数：根据已注册的模型标识创建 agno.Agent 实例。

	model_name 必须来自 `app.agent.llm_models` 中注册的键（例如 "kimi"、"deepseek"）。

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


__all__ = [
	"AgentDefinition",
	"TradeAction",
]
