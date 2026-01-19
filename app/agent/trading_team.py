from textwrap import dedent

from agno.team import Team

from app.agent.available_models import ModelName
from app.agent.decision_synthesis_agent import decision_synthesis_agent
from app.agent.fundamental_analysis_agent import fundamental_analysis_agent
from app.agent.news_sentiment_agent import news_sentiment_agent
from app.agent.risk_control_agent import risk_control_agent
from app.agent.technical_analysis_agent import technical_analysis_agent
from app.core.config import settings


def _get_team_db() -> object:
    """根据配置返回 Team 使用的数据库连接。"""
    from agno.db.postgres import AsyncPostgresDb
    from agno.db.sqlite import AsyncSqliteDb

    if settings.DATABASE_TYPE == "postgresql":
        return AsyncPostgresDb(id="trading_team_db", db_url=str(settings.postgre_url))
    return AsyncSqliteDb(id="trading_team_db", db_file="tmp/local.db")


def _get_team_description() -> str:
    return dedent("""\
        你是 Trading Team 的 Team Leader，负责协调 4 个专业 Agent 进行多维度交易分析：

        **Team 成员**:
        - **新闻情绪 Agent**: 分析新闻和舆情情绪
        - **技术分析 Agent**: 分析技术指标和价格走势
        - **基本面分析 Agent**: 分析财务状况和投资价值
        - **风控 Agent**: 验证交易决策的风险

        **工作流程**:
        1. 分配任务给 3 个分析 Agent（新闻、技术、基本面）
        2. 汇总 3 个 Agent 的分析结果
        3. 综合分析，生成初步交易决策
        4. 将初步决策传递给风控 Agent 验证
        5. 汇总风控检查结果，输出最终交易决策

        **协调要求**:
        - 根据市场环境合理分配各维度权重
        - 过滤低质量或矛盾的信号
        - 确保决策符合风控规则
        - 输出清晰的交易建议和风险提示
        """)


def _get_team_instructions() -> str:
    return dedent("""\
        作为 Team Leader，你的核心职责是协调多个专业 Agent，而不是直接调用它们。

        **执行步骤**:
        1. 理解输入数据：标的列表、新闻数据、技术指标、基本面数据、账户信息
        2. 逐步委托任务给相应的 Agent：
           - 新闻情绪 Agent：输入新闻数据，获取情绪评分
           - 技术分析 Agent：输入技术指标，获取趋势判断
           - 基本面分析 Agent：输入财务数据，获取基本面评分
        3. 综合各 Agent 的分析结果：
           - 评估各维度的一致性和重要性
           - 根据市场环境分配权重
           - 识别主要机会和风险点
        4. 生成初步交易决策：
           - 给出明确的交易建议
           - 指定标的代码、数量或权重
        5. 委托风控 Agent 验证：
           - 输入初步决策和账户信息
           - 获取风控检查结果
        6. 输出最终交易决策：
           - 如通过风控：输出调整后的交易决策
           - 如未通过风控：说明拒绝原因

        **输出格式**:
        请遵循 AgentOutput 的输出格式，包含 actions, explanation, confidence 字段。
        """)


def create_trading_team(
    model_name: ModelName = "kimi",
    debug_mode: bool = False,
) -> Team:
    """工厂函数：创建 Trading Team 实例。

    Args:
        model_name: 模型标识，必须来自 `available_models` 中注册的键
        debug_mode: 调试模式，启用后会输出更多日志

    Returns:
        已配置的 Team 实例
    """
    model = get_available_model(model_name)

    agents = [
        decision_synthesis_agent(model_name=model_name, debug_mode=debug_mode),
        news_sentiment_agent(model_name=model_name, debug_mode=debug_mode),
        technical_analysis_agent(model_name=model_name, debug_mode=debug_mode),
        fundamental_analysis_agent(model_name=model_name, debug_mode=debug_mode),
        risk_control_agent(model_name=model_name, debug_mode=debug_mode),
    ]

    return Team(
        name="trading-team",
        agents=agents,
        db=_get_team_db(),
        description=_get_team_description(),
        instructions=_get_team_instructions(),
        markdown=True,
        debug_mode=debug_mode,
    )


__all__ = [
    "create_trading_team",
]
