"""Step: 获取 A 股市场数据（使用 AkShare）。"""

from agno.workflow.step import Step
from agno.workflow.types import StepInput, StepOutput
from loguru import logger

from app.data_source.akshare_source import AkShareSource
from app.workflow.steps.utils import parse_step_input


async def _fetch_akshare_data(step_input: StepInput) -> StepOutput:
    """获取 A 股市场数据。

    从 step_input.input 中读取 symbols 列表,
    调用 AkShareSource 获取实时行情、新闻、基本面数据。
    """
    input_data = parse_step_input(step_input.input)

    symbols: list[str] = input_data.get("symbols", [])

    if not symbols:
        logger.warning("未提供 symbols, 跳过 A 股数据获取")
        return StepOutput(
            content={
                "market_data": [],
                "news_data": [],
                "fundamental_data": {},
            },
        )

    try:
        source = AkShareSource()

        market_data = source.get_spot_quotes(symbols)
        logger.info(f"获取 {len(market_data)} 个标的的实时行情")

        news_data = []
        for symbol in symbols:
            try:
                news = source.get_news(symbol, limit=5)
                news_data.extend(news)
            except Exception as e:
                logger.warning(f"获取 {symbol} 的新闻失败: {e}")

        logger.info(f"获取 {len(news_data)} 条新闻数据")

        fundamental_data = {}
        for symbol in symbols:
            try:
                fundamental = source.get_fundamental(symbol)
                fundamental_data[symbol] = fundamental
            except Exception as e:
                logger.warning(f"获取 {symbol} 的基本面数据失败: {e}")

        logger.info(f"获取 {len(fundamental_data)} 个标的基本面数据")

        return StepOutput(
            content={
                "market_data": market_data,
                "news_data": news_data,
                "fundamental_data": fundamental_data,
            },
        )
    except Exception as e:
        logger.error(f"获取 A 股数据失败: {e}")
        return StepOutput(
            content={
                "error": str(e),
                "market_data": [],
                "news_data": [],
                "fundamental_data": {},
            },
        )


fetch_akshare_data_step = Step(
    name="Fetch AkShare Data",
    executor=_fetch_akshare_data,
    description="获取 A 股实时行情、新闻、基本面数据",
    max_retries=2,
    timeout_seconds=60,
)

__all__ = ["fetch_akshare_data_step"]
