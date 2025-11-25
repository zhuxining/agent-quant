"""Trader Workflow 完整示例。

这个示例展示了如何使用 Trader Workflow 进行交易决策。
"""

import asyncio
from decimal import Decimal

from loguru import logger

from app.core.deps import get_db
from app.execution import run_trader_workflow
from app.models import PositionSide, PositionStatus, TradeAccount
from app.models.position import Position


async def setup_test_data(session):
	"""准备测试数据：创建账户和持仓。"""
	logger.info("准备测试数据...")

	# 创建测试账户
	account = TradeAccount(
		account_number="DEMO_ACCOUNT_001",
		name="演示交易账户",
		balance=Decimal("50000.00"),
		buying_power=Decimal("50000.00"),
		realized_pnl=Decimal("1250.50"),
		is_active=True,
		description="用于演示 Trader Workflow 的测试账户",
	)
	session.add(account)

	# 创建测试持仓（假设已经持有一些股票）
	position = Position(
		account_number="DEMO_ACCOUNT_001",
		symbol_exchange="AAPL.US",
		side=PositionSide.LONG,
		quantity=100,
		available_quantity=100,
		average_cost=Decimal("150.00"),
		market_price=Decimal("155.50"),
		market_value=Decimal("15550.00"),
		unrealized_pnl=Decimal("550.00"),
		realized_pnl=Decimal("0"),
		status=PositionStatus.OPEN,
		profit_target=Decimal("165.00"),
		stop_loss=Decimal("145.00"),
		notes="演示持仓",
	)
	session.add(position)

	await session.commit()
	logger.info("测试数据准备完成")


async def cleanup_test_data(session):
	"""清理测试数据。"""
	logger.info("清理测试数据...")
	from sqlmodel import select

	# 删除测试持仓
	positions = await session.execute(
		select(Position).where(Position.account_number == "DEMO_ACCOUNT_001")
	)
	for position in positions.scalars().all():
		await session.delete(position)

	# 删除测试账户
	accounts = await session.execute(
		select(TradeAccount).where(TradeAccount.account_number == "DEMO_ACCOUNT_001")
	)
	for account in accounts.scalars().all():
		await session.delete(account)

	await session.commit()
	logger.info("测试数据清理完成")


async def example_basic_usage():
	"""示例 1: 基础用法。"""
	logger.info("\n" + "=" * 60)
	logger.info("示例 1: 基础用法")
	logger.info("=" * 60)

	async for session in get_db():
		# 准备测试数据
		await setup_test_data(session)

		try:
			# 执行 Workflow
			result = await run_trader_workflow(
				session=session,
				symbols=["AAPL.US", "TSLA.US", "GOOGL.US"],
				account_number="DEMO_ACCOUNT_001",
			)

			# 打印结果
			logger.info("\n" + "=" * 60)
			logger.info("Workflow 执行结果:")
			logger.info("=" * 60)
			logger.info(f"标的列表: {result.symbols}")
			logger.info(f"账户号: {result.account_number}")
			logger.info(f"\n建议操作数: {len(result.agent_output.actions)}")
			logger.info(f"置信度: {result.agent_output.confidence}")
			logger.info(f"\n决策说明:\n{result.agent_output.explanation}")

			if result.agent_output.actions:
				logger.info("\n详细操作建议:")
				for i, action in enumerate(result.agent_output.actions, 1):
					logger.info(f"\n操作 {i}:")
					logger.info(f"  标的: {action.symbol}")
					logger.info(f"  动作: {action.action}")
					logger.info(f"  数量: {action.quantity}")
					logger.info(f"  权重: {action.weight}")

			# 打印生成的 Prompt（可选，用于调试）
			logger.info(f"\n生成的 Prompt 长度: {len(result.user_prompt)} 字符")
			logger.debug(f"完整 Prompt:\n{result.user_prompt}")

		finally:
			# 清理测试数据
			await cleanup_test_data(session)


async def example_custom_agent():
	"""示例 2: 使用自定义 Agent。"""
	logger.info("\n" + "=" * 60)
	logger.info("示例 2: 使用自定义 Agent")
	logger.info("=" * 60)

	from app.agent.trader_agent import trader_agent
	from app.execution import TraderWorkflow

	async for session in get_db():
		await setup_test_data(session)

		try:
			# 创建自定义 Agent（使用不同的模型）
			custom_agent = trader_agent(model_name="kimi", debug_mode=True)

			# 创建 Workflow 实例
			workflow = TraderWorkflow(
				session=session,
				agent=custom_agent,
			)

			# 执行
			result = await workflow.run(
				symbols=["AAPL.US"],
				account_number="DEMO_ACCOUNT_001",
			)

			logger.info("使用 Kimi 模型的决策结果:")
			logger.info(f"  操作数: {len(result.agent_output.actions)}")
			logger.info(f"  说明: {result.agent_output.explanation}")

		finally:
			await cleanup_test_data(session)


async def example_batch_processing():
	"""示例 3: 批量处理多个账户。"""
	logger.info("\n" + "=" * 60)
	logger.info("示例 3: 批量处理多个账户")
	logger.info("=" * 60)

	async for session in get_db():
		# 创建多个测试账户
		accounts = ["DEMO_ACC_001", "DEMO_ACC_002", "DEMO_ACC_003"]

		for account_number in accounts:
			account = TradeAccount(
				account_number=account_number,
				name=f"测试账户 {account_number}",
				balance=Decimal("10000.00"),
				buying_power=Decimal("10000.00"),
				realized_pnl=Decimal("0"),
				is_active=True,
			)
			session.add(account)

		await session.commit()

		try:
			# 并行执行多个账户的分析
			tasks = [
				run_trader_workflow(
					session=session,
					symbols=["AAPL.US", "TSLA.US"],
					account_number=account_number,
				)
				for account_number in accounts
			]

			results = await asyncio.gather(*tasks, return_exceptions=True)

			# 汇总结果
			logger.info("\n批量处理结果:")
			for account_number, result in zip(accounts, results, strict=False):
				if isinstance(result, Exception):
					logger.error(f"账户 {account_number} 处理失败: {result}")
				else:
					logger.info(f"\n账户 {account_number}:")
					logger.info(f"  操作数: {len(result.agent_output.actions)}")
					logger.info(f"  置信度: {result.agent_output.confidence}")

		finally:
			# 清理测试账户
			from sqlmodel import select

			for account_number in accounts:
				accounts_to_delete = await session.execute(
					select(TradeAccount).where(TradeAccount.account_number == account_number)
				)
				for account in accounts_to_delete.scalars().all():
					await session.delete(account)

			await session.commit()


async def example_error_handling():
	"""示例 4: 错误处理。"""
	logger.info("\n" + "=" * 60)
	logger.info("示例 4: 错误处理")
	logger.info("=" * 60)

	from app.trade.account import TradeAccountNotFoundError

	async for session in get_db():
		try:
			# 尝试使用不存在的账户
			await run_trader_workflow(
				session=session,
				symbols=["AAPL.US"],
				account_number="NONEXISTENT_ACCOUNT",
			)
		except TradeAccountNotFoundError as e:
			logger.warning(f"预期的错误: {e}")
		except Exception as e:
			logger.error(f"未预期的错误: {e}")


async def main():
	"""主函数：运行所有示例。"""
	logger.info("=" * 60)
	logger.info("Trader Workflow 示例程序")
	logger.info("=" * 60)

	# 运行各个示例
	await example_basic_usage()

	# 可选：取消注释以运行其他示例
	# await example_custom_agent()
	# await example_batch_processing()
	# await example_error_handling()

	logger.info("\n" + "=" * 60)
	logger.info("所有示例执行完成")
	logger.info("=" * 60)


if __name__ == "__main__":
	asyncio.run(main())
