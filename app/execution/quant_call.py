"""Simple end-to-end runner that seeds data, builds prompts, calls the Agent, and trades."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from loguru import logger
from sqlalchemy import select

from app.agent.trader import deepseek_trader, kimi_trader
from app.core.config import settings
from app.core.db import async_session_maker, create_db_and_tables
from app.market.data_feed import DataFeed
from app.models import OrderType, Stock, TradeAccount
from app.prompting.builder import SystemPromptProvider, UserPromptProvider
from app.trade.order import (
	OrderExecutionResult,
	place_buy_order,
	place_sell_order,
)
from app.utils.logging import setup_logging

TraderFn = Callable[[str, str], str]


@dataclass(frozen=True, slots=True)
class StockSeed:
	symbol: str
	exchange: str
	name: str
	lot_size: int = 100

	@property
	def symbol_exchange(self) -> str:
		return f"{self.symbol}.{self.exchange}"


@dataclass(slots=True)
class TradeSignal:
	symbol: str
	action: str
	quantity: int | None = None
	reasoning: str | None = None
	price: Decimal | None = None

	@property
	def normalized_symbol(self) -> str:
		return self.symbol.replace(" ", "").upper()

	@property
	def normalized_action(self) -> str:
		return self.action.strip().lower()


ACCOUNT_NUMBER = "ACC-001"
ACCOUNT_NAME = "Demo Quant Account"
ACCOUNT_BALANCE = Decimal("1000000")

SEED_STOCKS: tuple[StockSeed, ...] = (
	StockSeed(symbol="AAPL", exchange="US", name="Apple Inc."),
	StockSeed(symbol="MSFT", exchange="US", name="Microsoft Corporation"),
	StockSeed(symbol="TSLA", exchange="US", name="Tesla Inc."),
)


async def main() -> None:
	setup_logging(settings)
	logger.info("启动 Quant Call Runner")
	await create_db_and_tables()
	async with async_session_maker() as session:
		account = await ensure_account(session)
		stocks = await ensure_stocks(session, SEED_STOCKS)
		symbols = [seed.symbol_exchange for seed in SEED_STOCKS]
		system_prompt = SystemPromptProvider().load()
		user_prompt = await UserPromptProvider().build(
			session,
			account_number=account.account_number,
			symbols=symbols,
		)
		trader_fn, trader_name = pick_trader()
		logger.info("使用 {} Trader 生成交易建议", trader_name)
		raw_response = await asyncio.to_thread(trader_fn, system_prompt, user_prompt)
		signals = parse_trade_signals(raw_response)
		logger.info("共解析到 {} 条交易信号", len(signals))
		if not signals:
			return
		data_feed = DataFeed()
		stock_index = build_stock_index(stocks)
		for signal in signals:
			await execute_signal(
				session,
				account_number=account.account_number,
				signal=signal,
				data_feed=data_feed,
				stocks=stock_index,
			)


async def ensure_account(session) -> TradeAccount:
	statement = select(TradeAccount).where(TradeAccount.account_number == ACCOUNT_NUMBER)
	result = await session.execute(statement)
	account = result.scalar_one_or_none()
	if account:
		logger.info("账户 {} 已存在，余额 {}", ACCOUNT_NUMBER, account.balance)
		return account
	account = TradeAccount(
		name=ACCOUNT_NAME,
		account_number=ACCOUNT_NUMBER,
		balance=ACCOUNT_BALANCE,
		buying_power=ACCOUNT_BALANCE,
		description="用于 Quant Runner 的演示账户",
	)
	session.add(account)
	await session.commit()
	await session.refresh(account)
	logger.info(
		"创建交易账户 {} | 余额={} | buying_power={}",
		account.account_number,
		account.balance,
		account.buying_power,
	)
	return account


async def ensure_stocks(session, seeds: Sequence[StockSeed]) -> list[Stock]:
	existing: dict[str, Stock] = {}
	for seed in seeds:
		statement = select(Stock).where(
			Stock.symbol == seed.symbol,
			Stock.exchange == seed.exchange,
		)
		result = await session.execute(statement)
		stock = result.scalar_one_or_none()
		if stock:
			existing[seed.symbol_exchange.upper()] = stock
			continue
		stock = Stock(
			symbol=seed.symbol,
			exchange=seed.exchange,
			name=seed.name,
			lot_size=seed.lot_size,
			is_active=True,
		)
		session.add(stock)
		await session.flush()
		await session.refresh(stock)
		logger.info("新增标的 {} ({})", stock.symbol, stock.exchange)
		existing[seed.symbol_exchange.upper()] = stock
	await session.commit()
	return list(existing.values())


def pick_trader() -> tuple[TraderFn, str]:
	if settings.KIMI_API_KEY and settings.KIMI_MODEL:
		return kimi_trader, "Kimi"
	if settings.DEEPSEEK_API_KEY and settings.DEEPSEEK_MODEL:
		return deepseek_trader, "DeepSeek"
	msg = "请配置 KIMI/DEEPSEEK 的 API_KEY 与 MODEL 后再运行"
	raise RuntimeError(msg)


def parse_trade_signals(raw: str) -> list[TradeSignal]:
	start = raw.find("[")
	end = raw.rfind("]")
	if start == -1 or end == -1 or end <= start:
		logger.warning("Agent 输出缺少 JSON 数组，原文: {}", raw)
		return []
	data = raw[start : end + 1]
	try:
		payload = json.loads(data)
	except json.JSONDecodeError:
		logger.exception("无法解析 Agent 输出为 JSON: {}", data)
		return []
	signals: list[TradeSignal] = []
	for entry in payload:
		if not isinstance(entry, dict):
			continue
		symbol = str(entry.get("symbol") or "").strip()
		action = str(entry.get("action") or "").strip()
		if not symbol or not action:
			continue
		quantity_value = entry.get("quantity")
		quantity = _safe_int(quantity_value)
		price = _safe_decimal(entry.get("price") or entry.get("target_price"))
		signal = TradeSignal(
			symbol=symbol,
			action=action,
			quantity=quantity,
			reasoning=entry.get("reasoning") or entry.get("reason"),
			price=price,
		)
		signals.append(signal)
	return signals


async def execute_signal(
	session,
	*,
	account_number: str,
	signal: TradeSignal,
	data_feed: DataFeed,
	stocks: dict[str, Stock],
) -> None:
	action = signal.normalized_action
	if action not in {"buy", "sell"}:
		logger.info("跳过动作 {} -> {}", signal.symbol, signal.action)
		return
	stock = resolve_stock(signal, stocks)
	if stock is None:
		logger.warning("信号中的标的 {} 未在本地登记，跳过", signal.symbol)
		return
	symbol_exchange = format_symbol_exchange(stock)
	price = signal.price or data_feed.get_latest_price(symbol_exchange)
	if price is None:
		logger.warning("无法获取 {} 的最新价格，跳过", symbol_exchange)
		return
	quantity = signal.quantity or stock.lot_size
	if quantity <= 0:
		logger.warning("无效的下单数量 {} -> {}", signal.symbol, signal.quantity)
		return
	logger.info(
		"执行信号 | symbol={} action={} qty={} price={} reason={}",
		symbol_exchange,
		action,
		quantity,
		price,
		signal.reasoning,
	)
	try:
		if action == "buy":
			result = await place_buy_order(
				session,
				account_number=account_number,
				symbol_exchange=symbol_exchange,
				quantity=quantity,
				price=price,
				order_type=OrderType.MARKET,
			)
		else:
			result = await place_sell_order(
				session,
				account_number=account_number,
				symbol_exchange=symbol_exchange,
				quantity=quantity,
				price=price,
				order_type=OrderType.MARKET,
			)
	except Exception:
		logger.exception("执行信号失败: {}", signal)
		return
	log_execution(result)


def log_execution(result: OrderExecutionResult) -> None:
	order = result.order
	position = result.position
	account = result.account
	logger.info(
		"订单已执行 | order_id={} side={} qty={} avg_price={} | 账户余额={} | 持仓数量={}",
		order.id,
		order.side,
		order.executed_quantity,
		order.average_price,
		account.balance,
		position.quantity,
	)


def resolve_stock(signal: TradeSignal, stocks: dict[str, Stock]) -> Stock | None:
	key = signal.normalized_symbol
	if key in stocks:
		return stocks[key]
	alt = key.replace(".", "")
	return stocks.get(alt)


def build_stock_index(stocks: Sequence[Stock]) -> dict[str, Stock]:
	index: dict[str, Stock] = {}
	for stock in stocks:
		index[stock.symbol.upper()] = stock
		index[format_symbol_exchange(stock).upper()] = stock
	return index


def format_symbol_exchange(stock: Stock) -> str:
	return f"{stock.symbol}.{stock.exchange}"


def _safe_int(value: Any) -> int | None:
	try:
		if value is None:
			return None
		return int(value)
	except (TypeError, ValueError):
		return None


def _safe_decimal(value: Any) -> Decimal | None:
	if value is None:
		return None
	try:
		return Decimal(str(value))
	except (InvalidOperation, ValueError, TypeError):
		return None


if __name__ == "__main__":
	asyncio.run(main())
