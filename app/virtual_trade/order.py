"""本地模拟交易的下单与结算工具。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    OrderSide,
    OrderStatus,
    OrderType,
    PositionSide,
    VirtualTradeOrder,
    VirtualTradePosition,
)
from app.virtual_trade.account import (
    AccountSnapshot,
    apply_order_settlement,
)
from app.virtual_trade.position import (
    apply_buy_to_position,
    apply_sell_to_position,
    calculate_realized_pnl,
    get_position_for_update,
)


class TradeOrderError(RuntimeError):
    """下单流程中的基础异常。"""


class PositionNotFoundError(TradeOrderError):
    """尝试操作的持仓不存在。"""


class InsufficientPositionQuantityError(TradeOrderError):
    """持仓数量不足,无法完成卖出。"""


@dataclass(slots=True)
class OrderExecutionResult:
    """下单完成后的聚合结果。"""

    order: VirtualTradeOrder
    position: VirtualTradePosition
    account: AccountSnapshot


async def place_buy_order(
    session: AsyncSession,
    *,
    account_number: str,
    symbol_exchange: str,
    quantity: int,
    price: Decimal,
    order_type: OrderType = OrderType.MARKET,
    auto_commit: bool = True,
) -> OrderExecutionResult:
    """在本地环境模拟买入一笔订单并更新账户/持仓。"""

    _validate_quantity(quantity)
    price = _validate_price(price)
    position = await get_position_for_update(
        session,
        account_number=account_number,
        symbol_exchange=symbol_exchange,
        side=PositionSide.LONG,
    )
    cash_amount = price * Decimal(quantity)
    account_snapshot = await apply_order_settlement(
        session,
        account_number=account_number,
        side=OrderSide.BUY,
        cash_amount=cash_amount,
        auto_commit=False,
    )
    position = await apply_buy_to_position(
        session,
        position,
        account_number=account_number,
        symbol_exchange=symbol_exchange,
        quantity=quantity,
        price=price,
    )
    order = VirtualTradeOrder(
        account_number=account_number,
        symbol_exchange=symbol_exchange,
        side=OrderSide.BUY,
        order_type=order_type,
        quantity=quantity,
        price=price,
        status=OrderStatus.FILLED,
        executed_quantity=quantity,
        average_price=price,
    )
    session.add(order)
    await _finalize(session, order, position, auto_commit)
    return OrderExecutionResult(order=order, position=position, account=account_snapshot)


async def place_sell_order(
    session: AsyncSession,
    *,
    account_number: str,
    symbol_exchange: str,
    quantity: int,
    price: Decimal,
    order_type: OrderType = OrderType.MARKET,
    auto_commit: bool = True,
) -> OrderExecutionResult:
    """模拟卖出,减少持仓并更新账户。"""

    _validate_quantity(quantity)
    price = _validate_price(price)
    position = await get_position_for_update(
        session,
        account_number=account_number,
        symbol_exchange=symbol_exchange,
        side=PositionSide.LONG,
    )
    if position is None or position.quantity <= 0:
        raise PositionNotFoundError(f"账户 {account_number} 没有 {symbol_exchange} 的持仓")
    if quantity > position.available_quantity:
        raise InsufficientPositionQuantityError(
            f"可交易数量不足: 可用 {position.available_quantity}, 请求 {quantity}"
        )
    realized_delta = calculate_realized_pnl(
        position.side,
        position.average_cost,
        price,
        quantity,
    )
    cash_amount = price * Decimal(quantity)
    account_snapshot = await apply_order_settlement(
        session,
        account_number=account_number,
        side=OrderSide.SELL,
        cash_amount=cash_amount,
        realized_pnl_delta=realized_delta,
        auto_commit=False,
    )
    apply_sell_to_position(
        position,
        quantity=quantity,
        price=price,
        realized_delta=realized_delta,
    )
    order = VirtualTradeOrder(
        account_number=account_number,
        symbol_exchange=symbol_exchange,
        side=OrderSide.SELL,
        order_type=order_type,
        quantity=quantity,
        price=price,
        status=OrderStatus.FILLED,
        executed_quantity=quantity,
        average_price=price,
    )
    session.add(order)
    await _finalize(session, order, position, auto_commit)
    return OrderExecutionResult(order=order, position=position, account=account_snapshot)


def _validate_quantity(quantity: int) -> None:
    if quantity <= 0:
        raise ValueError("quantity 必须为正整数")


def _validate_price(price: Decimal | float | str) -> Decimal:
    value = Decimal(price)
    if value <= 0:
        raise ValueError("price 必须大于 0")
    return value


async def _finalize(
    session: AsyncSession,
    order: VirtualTradeOrder,
    position: VirtualTradePosition,
    auto_commit: bool,
) -> None:
    await session.flush()
    if auto_commit:
        await session.commit()
        await session.refresh(order)
        await session.refresh(position)


__all__ = [
    "InsufficientPositionQuantityError",
    "OrderExecutionResult",
    "PositionNotFoundError",
    "TradeOrderError",
    "place_buy_order",
    "place_sell_order",
]
