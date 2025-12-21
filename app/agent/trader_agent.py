from textwrap import dedent

from agno.agent import Agent
from agno.db.postgres import AsyncPostgresDb
from agno.db.sqlite import AsyncSqliteDb
from pydantic import BaseModel

from app.agent.available_models import ModelName, get_available_model
from app.core.config import settings

# ------------------- System Prompt 定义 ----------------- #


def _get_description() -> str:
    return "你是一个量化交易助理,负责基于提供的账户信息、仓位和市场数据,给出清晰的操作建议。"


def _get_instructions() -> str:
    return dedent("""\
        - **核心含义**:通过高胜率、大盈亏比交易提升收益,同时控制回撤和波动;避免频繁交易和过度操作,这些会增加手续费侵蚀和不确定性。
        - **关键行动**:仅在高质量机会时开仓,下单金额不能超过可用资金;。

        ## 交易哲学与原则
        - **顺势而为**:尊重市场主要趋势,不逆势操作。
        - **风险控制**:每笔交易必须设定明确止损,单笔风险≤账户1%。
        - **情绪管理**:避免复仇式交易或FOMO(错失恐惧);连续盈利后不冒进,亏损后不报复。

        ## 数据说明
        下面,我们将为您提供各种状态数据、价格数据和预测信号,以便您可以发现alpha。
        ⚠️ **关键:以下所有价格或信号数据顺序为:最老→最新**
        """)


# ------------------- Agent 输入输出结构定义 ----------------- #


class AgentInput(BaseModel):
    """Agent 输入结构。

    - candidate: 候选交易标的的技术面数据和市场信息
    - account: 账户信息与持仓详情(合并)
    """

    candidate: str
    account: str


class TradeAction(BaseModel):
    """单个交易操作建议。"""

    symbol: str
    action: str  # buy/sell/hold/wait
    quantity: int | None = None
    weight: float | None = None


class AgentOutput(BaseModel):
    """Agent 输出结构。

    - actions: 建议的操作列表
    - explanation: 文本说明
    - confidence: 置信度(0-1)
    """

    actions: list[TradeAction]
    explanation: str
    confidence: float | None = None


# ------------------- 数据库连接 ----------------- #


def _get_agent_db() -> AsyncPostgresDb | AsyncSqliteDb:
    """根据配置返回 Agent 使用的数据库连接。"""
    if settings.DATABASE_TYPE == "postgresql":
        return AsyncPostgresDb(id="trader_agent_db", db_url=str(settings.postgre_url))
    return AsyncSqliteDb(id="trader_agent_db", db_file="tmp/local.db")


# ------------------- 创建 agno.Agent 实例 ----------------- #


def trader_agent(
    model_name: ModelName = "kimi",
    debug_mode: bool = False,
) -> Agent:
    """工厂函数:根据已注册的模型标识创建 agno.Agent 实例。

    Args:
        model_name: 模型标识, 必须来自 `available_models` 中注册的键
        debug_mode: 调试模式, 启用后会输出更多日志

    Returns:
        已配置的 Agent 实例
    """
    model = get_available_model(model_name)

    return Agent(
        name="trader_agent",
        model=model,
        db=_get_agent_db(),
        description=_get_description(),
        instructions=_get_instructions(),
        markdown=True,
        debug_mode=debug_mode,
        output_schema=AgentOutput,
        input_schema=AgentInput,
        # 使用 JSON 模式确保 response_format 可序列化, 避免缓存键生成失败
        use_json_mode=True,
    )


__all__ = [
    "AgentInput",
    "AgentOutput",
    "TradeAction",
    "trader_agent",
]
