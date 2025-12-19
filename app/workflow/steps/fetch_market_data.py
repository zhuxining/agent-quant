"""Step 1: 获取市场行情数据。"""

from datetime import datetime

from agno.workflow.step import Step
from agno.workflow.types import StepInput, StepOutput
from loguru import logger

from app.data_feed.technical_indicator import TechnicalIndicatorFeed, TechnicalSnapshot
from app.workflow.steps.utils import parse_step_input


async def _fetch_market_data(step_input: StepInput) -> StepOutput:
    """获取技术指标快照。

    从 step_input.input 中读取 symbols 列表和 end_date,
    调用 TechnicalIndicatorFeed 获取行情数据。
    """
    input_data = parse_step_input(step_input.input)

    symbols: list[str] = input_data.get("symbols", [])
    end_date: datetime | None = input_data.get("end_date")

    if not symbols:
        logger.warning("未提供 symbols, 跳过行情获取")
        return StepOutput(content={"snapshots": [], "symbols": []})

    try:
        feed = TechnicalIndicatorFeed()
        snapshots: list[TechnicalSnapshot] = feed.build_snapshots(symbols, end_date=end_date)

        if end_date:
            logger.info(f"获取 {len(snapshots)} 个标的的历史数据 (截止: {end_date})")
        else:
            logger.info(f"获取 {len(snapshots)} 个标的的实时数据")

        return StepOutput(
            content={"snapshots": snapshots, "symbols": symbols},
        )
    except Exception as e:
        logger.error(f"获取行情数据失败: {e}")
        return StepOutput(
            content={"error": str(e), "snapshots": []},
        )


fetch_market_data_step = Step(
    name="Fetch Market Data",
    executor=_fetch_market_data,
    description="获取技术指标快照数据",
    max_retries=2,
    timeout_seconds=60,
)

__all__ = ["fetch_market_data_step"]
