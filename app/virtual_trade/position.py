"""持仓相关的通用操作。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import PositionSide, PositionStatus, VirtualTradePosition

ZERO = Decimal("0")


@dataclass(slots=True)
class PositionSummary:
    """面向 Prompt/Workflow 的持仓概要。"""

    symbol_exchange: str
    side: PositionSide
    quantity: int
    available_quantity: int
    average_cost: Decimal
    market_price: Decimal | None
    market_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    profit_target: Decimal | None
    stop_loss: Decimal | None
    notes: str | None


async def list_position_summaries(
    session: AsyncSession, account_number: str
) -> list[PositionSummary]:
    """查询账户当前持仓,转换为适合 Prompt 的结构。"""

    statement = (
        select(VirtualTradePosition)
        .where(VirtualTradePosition.account_number == account_number)
        .order_by(VirtualTradePosition.symbol_exchange)
    )
    result = await session.execute(statement)
    return [
        PositionSummary(
            symbol_exchange=position.symbol_exchange,
            side=position.side,
            quantity=position.quantity,
            available_quantity=position.available_quantity,
            average_cost=position.average_cost,
            market_price=position.market_price,
            market_value=position.market_value,
            unrealized_pnl=position.unrealized_pnl,
            realized_pnl=position.realized_pnl,
            profit_target=position.profit_target,
            stop_loss=position.stop_loss,
            notes=position.notes,
        )
        for position in result.scalars().all()
    ]


async def get_position_for_update(
    session: AsyncSession,
    *,
    account_number: str,
    symbol_exchange: str,
    side: PositionSide,
) -> VirtualTradePosition | None:
    """在事务中锁定指定股票的持仓记录。"""

    statement = (
        select(VirtualTradePosition)
        .where(
            VirtualTradePosition.account_number == account_number,
            VirtualTradePosition.symbol_exchange == symbol_exchange,
            VirtualTradePosition.side == side,
        )
        .with_for_update()
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def apply_buy_to_position(
    session: AsyncSession,
    position: VirtualTradePosition | None,
    *,
    account_number: str,
    symbol_exchange: str,
    quantity: int,
    price: Decimal,
) -> VirtualTradePosition:
    """根据买入成交结果创建或扩充持仓。"""

    total_cost = price * Decimal(quantity)
    if position is None:
        position = VirtualTradePosition(
            account_number=account_number,
            symbol_exchange=symbol_exchange,
            side=PositionSide.LONG,
            quantity=quantity,
            available_quantity=quantity,
            average_cost=price,
            market_price=price,
            market_value=total_cost,
            unrealized_pnl=ZERO,
            realized_pnl=ZERO,
            status=PositionStatus.OPEN,
        )
        session.add(position)
        return position
    total_quantity = position.quantity + quantity
    if total_quantity <= 0:
        raise ValueError("累计持仓数量必须大于 0")
    current_cost = position.average_cost * Decimal(position.quantity)
    position.quantity = total_quantity
    position.available_quantity += quantity
    position.average_cost = (current_cost + total_cost) / Decimal(total_quantity)
    position.market_price = price
    position.market_value = price * Decimal(position.quantity)
    position.unrealized_pnl = calculate_unrealized(position)
    position.status = PositionStatus.OPEN
    return position


def apply_sell_to_position(
    position: VirtualTradePosition,
    *,
    quantity: int,
    price: Decimal,
    realized_delta: Decimal,
) -> None:
    """根据卖出成交结果扣减持仓并维护状态。"""

    position.quantity -= quantity
    position.available_quantity -= quantity
    position.market_price = price
    position.market_value = price * Decimal(position.quantity)
    position.unrealized_pnl = calculate_unrealized(position) if position.quantity > 0 else ZERO
    position.realized_pnl += realized_delta
    if position.quantity <= 0:
        position.quantity = 0
        position.available_quantity = 0
        position.market_value = ZERO
        position.unrealized_pnl = ZERO
        position.status = PositionStatus.CLOSED
    else:
        position.status = PositionStatus.OPEN


def calculate_realized_pnl(
    side: PositionSide,
    average_cost: Decimal,
    execution_price: Decimal,
    quantity: int,
) -> Decimal:
    """计算本次交易产生的已实现盈亏。"""

    qty = Decimal(quantity)
    if side is PositionSide.SHORT:
        return (average_cost - execution_price) * qty
    return (execution_price - average_cost) * qty


def calculate_unrealized(position: VirtualTradePosition) -> Decimal:
    """根据最新价格计算浮动盈亏。"""

    if position.market_price is None or position.quantity <= 0:
        return ZERO
    qty = Decimal(position.quantity)
    if position.side is PositionSide.SHORT:
        return (position.average_cost - position.market_price) * qty
    return (position.market_price - position.average_cost) * qty
