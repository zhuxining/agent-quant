"""Trader Workflow 的各个步骤定义。"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.execution.prompt_composer import PromptComposer
from app.market.data_feed import DataFeed, MarketSnapshot
from app.trade.account import AccountOverview, build_account_overview
from app.trade.position import PositionSummary, list_position_summaries

# ------------------- 中间数据结构 ----------------- #


@dataclass(slots=True)
class ParallelDataOutput:
	"""并行数据查询的输出结果。"""

	market_snapshots: list[MarketSnapshot]
	position_summaries: list[PositionSummary]
	account_overview: AccountOverview


class ComposedPromptOutput(BaseModel):
	"""Prompt 组装步骤的输出。"""

	user_prompt: str
	market_snapshots: list[MarketSnapshot]
	position_summaries: list[PositionSummary]
	account_overview: AccountOverview


# ------------------- Step Functions ----------------- #


async def parallel_data_fetch_step(
	session: AsyncSession,
	symbols: list[str],
	account_number: str,
	data_feed: DataFeed | None = None,
) -> ParallelDataOutput:
	"""并行查询市场数据、持仓信息和账户信息。

	Args:
	    session: 数据库会话
	    symbols: 标的列表
	    account_number: 账户号
	    data_feed: 市场数据源（可选，用于依赖注入）

	Returns:
	    ParallelDataOutput: 包含三类数据的输出
	"""
	if data_feed is None:
		data_feed = DataFeed()

	# 并行执行三个查询
	market_task = asyncio.create_task(_fetch_market_data(data_feed, symbols))
	position_task = asyncio.create_task(_fetch_position_data(session, account_number))
	account_task = asyncio.create_task(_fetch_account_data(session, account_number))

	market_snapshots, position_summaries, account_overview = await asyncio.gather(
		market_task, position_task, account_task
	)

	return ParallelDataOutput(
		market_snapshots=market_snapshots,
		position_summaries=position_summaries,
		account_overview=account_overview,
	)


async def compose_prompt_step(data: ParallelDataOutput) -> ComposedPromptOutput:
	"""将并行查询的数据组装成 Trader Agent 的输入 Prompt。

	Args:
	    data: 并行数据查询的输出

	Returns:
	    ComposedPromptOutput: 包含完整 Prompt 的输出
	"""
	user_prompt = PromptComposer.compose_full_prompt(
		market_snapshots=data.market_snapshots,
		account_overview=data.account_overview,
		position_summaries=data.position_summaries,
	)

	return ComposedPromptOutput(
		user_prompt=user_prompt,
		market_snapshots=data.market_snapshots,
		position_summaries=data.position_summaries,
		account_overview=data.account_overview,
	)


# ------------------- 内部辅助函数 ----------------- #


async def _fetch_market_data(
	data_feed: DataFeed,
	symbols: list[str],
) -> list[MarketSnapshot]:
	"""查询市场数据。"""
	if not symbols:
		return []

	# DataFeed.build_snapshots 是同步方法，需要在 executor 中运行
	loop = asyncio.get_event_loop()
	return await loop.run_in_executor(None, data_feed.build_snapshots, symbols)


async def _fetch_position_data(
	session: AsyncSession,
	account_number: str,
) -> list[PositionSummary]:
	"""查询持仓信息。"""
	return await list_position_summaries(session, account_number)


async def _fetch_account_data(
	session: AsyncSession,
	account_number: str,
) -> AccountOverview:
	"""查询账户信息。"""
	return await build_account_overview(session, account_number)


__all__ = [
	"ParallelDataOutput",
	"ComposedPromptOutput",
	"parallel_data_fetch_step",
	"compose_prompt_step",
]
