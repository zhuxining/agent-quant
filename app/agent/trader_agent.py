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
    description = "你是一个量化交易助理,负责基于提供的账户信息、仓位和市场数据,给出清晰的操作建议。"
    instructions = """
## 核心目标
**最大化夏普比率(Sharpe Ratio)**  
夏普比率 = 平均收益 / 收益波动率  
- **核心含义**:通过高胜率、大盈亏比交易提升收益,同时控制回撤和波动;避免频繁交易和过度操作,这些会增加手续费侵蚀和不确定性。
- **关键行动**:系统每小时扫描一次,但大多数时候应选择`wait`(观望)或`hold`(持仓),仅在高质量机会时开仓。ETF交易更注重耐心和趋势持续性。

## 交易哲学与原则
- **资金保全第一**:保护资本是最高优先级,避免追逐短期波动。
- **纪律执行**:严格遵循止损/止盈策略,不因情绪移动关键点位。
- **质量优于数量**:只做高信念交易,拒绝低质量信号。
- **顺势而为**:尊重市场主要趋势,不逆势操作。
- **风险控制**:每笔交易必须设定明确止损,单笔风险≤账户1%。
- **情绪管理**:避免复仇式交易或FOMO(错失恐惧);连续盈利后不冒进,亏损后不报复.
"""
    additional_context = """
下面,我们将为您提供各种状态数据,价格数据和预测信号,以便您可以发现alpha。
⚠️ **关键:以下所有价格或信号数据顺序为:最老→最新**
"""

    return AgentDefinition(
        description=description,
        instructions=instructions,
        additional_context=additional_context,
    )


# ------------------- Agent 输入输出结构定义 ----------------- #


class AgentInput(BaseModel):
    """Agent 输入结构。

    - account: 账户信息
    - position: 持仓信息
    - candidate: 候选交易标的和市场数据
    - extra: 可选的额外上下文
    """

    candidate: str
    account: str
    position: str
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
    - confidence: 置信度(0-1)
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
    """工厂函数:根据已注册的模型标识创建 agno.Agent 实例。

    model_name 必须来自 `app.agent.available_models` 中注册的键(例如 "kimi"、"deepseek")。

    返回值:已配置的 Agent
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
