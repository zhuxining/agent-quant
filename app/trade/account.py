"""交易账户相关的核心操作。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import OrderSide, TradeAccount


class TradeAccountError(RuntimeError):
	"""账户操作的基础异常。"""


class TradeAccountNotFoundError(TradeAccountError):
	"""指定账户不存在。"""


class InsufficientBuyingPowerError(TradeAccountError):
	"""账户可用资金不足，无法完成操作。"""


@dataclass(slots=True)
class AccountSnapshot:
	"""账户当前状态快照。"""

	id: uuid.UUID
	account_number: str
	name: str
	balance: Decimal
	buying_power: Decimal
	realized_pnl: Decimal
	is_active: bool
	description: str | None


@dataclass(slots=True)
class AccountOverview:
	"""面向 Prompt/Workflow 的账户概览。"""

	account_number: str
	name: str
	cash_available: Decimal
	buying_power: Decimal
	realized_pnl: Decimal
	return_pct: float | None
	sharpe_ratio: float | None
	description: str | None = None


def _calculate_return_pct(snapshot: AccountSnapshot) -> float | None:
	base = snapshot.balance
	if base == 0:
		return None
	return float((snapshot.realized_pnl / base) * Decimal("100"))


async def build_account_overview(session: AsyncSession, account_number: str) -> AccountOverview:
	"""查询账户并计算基础绩效指标，供 agent prompt 使用。"""

	snapshot = await get_account_snapshot(session, account_number)
	return AccountOverview(
		account_number=snapshot.account_number,
		name=snapshot.name,
		cash_available=snapshot.balance,
		buying_power=snapshot.buying_power,
		realized_pnl=snapshot.realized_pnl,
		return_pct=_calculate_return_pct(snapshot),
		sharpe_ratio=None,
		description=snapshot.description,
	)


async def get_account_snapshot(session: AsyncSession, account_number: str) -> AccountSnapshot:
	"""查询指定账户最新状态。"""

	statement = select(TradeAccount).where(TradeAccount.account_number == account_number)
	result = await session.execute(statement)
	account = result.scalar_one_or_none()
	if account is None:
		raise TradeAccountNotFoundError(f"账户 {account_number} 不存在")
	return _to_snapshot(account)


async def apply_order_settlement(
	session: AsyncSession,
	*,
	account_number: str,
	side: OrderSide,
	cash_amount: Decimal,
	realized_pnl_delta: Decimal = Decimal("0"),
	auto_commit: bool = True,
) -> AccountSnapshot:
	"""根据订单成交结果更新账户资金。"""

	if cash_amount <= 0:
		raise ValueError("cash_amount 必须为正数")
	statement = (
		select(TradeAccount).where(TradeAccount.account_number == account_number).with_for_update()
	)
	result = await session.execute(statement)
	account = result.scalar_one_or_none()
	if account is None:
		raise TradeAccountNotFoundError(f"账户 {account_number} 不存在")
	if side is OrderSide.BUY:
		if account.balance < cash_amount or account.buying_power < cash_amount:
			raise InsufficientBuyingPowerError("账户余额或购买力不足，无法完成买单")
		account.balance -= cash_amount
		account.buying_power -= cash_amount
	else:
		account.balance += cash_amount
		account.buying_power += cash_amount
		account.realized_pnl += realized_pnl_delta
	session.add(account)
	if auto_commit:
		await session.commit()
		await session.refresh(account)
	else:
		await session.flush()
	return _to_snapshot(account)


def _to_snapshot(account: TradeAccount) -> AccountSnapshot:
	return AccountSnapshot(
		id=account.id,
		account_number=account.account_number,
		name=account.name,
		balance=account.balance,
		buying_power=account.buying_power,
		realized_pnl=account.realized_pnl,
		is_active=account.is_active,
		description=account.description,
	)
