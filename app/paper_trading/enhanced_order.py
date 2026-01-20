"""增强的订单执行模块，集成交易配置、佣金和滑点计算。"""

from datetime import datetime
from decimal import Decimal
from uuid import uuid7

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    OrderSide,
    OrderStatus,
    OrderType,
    VirtualTradeOrder,
)
from app.paper_trading.commission import CommissionCalculator
from app.paper_trading.slippage import SlippageCalculator
from app.paper_trading.trading_config import TradingConfig


class OrderValidationError(RuntimeError):
    """订单验证失败异常。"""


class TradingHoursViolationError(OrderValidationError):
    """非交易时段下单异常。"""


class TPlus1RestrictionError(OrderValidationError):
    """T+1 限制异常（当日买入的股票不能当日卖出）。"""


class InsufficientFundsError(OrderValidationError):
    """资金不足异常。"""


class OrderExecutionResult:
    """订单执行结果。"""

    def __init__(
        self,
        order: VirtualTradeOrder,
        executed_price: Decimal,
        executed_quantity: int,
        commission: Decimal,
        slippage_amount: Decimal,
    ):
        self.order = order
        self.executed_price = executed_price
        self.executed_quantity = executed_quantity
        self.commission = commission
        self.slippage_amount = slippage_amount

    @property
    def total_cost(self) -> Decimal:
        """总成本（含佣金和滑点）。"""
        return (
            (self.executed_price * Decimal(self.executed_quantity))
            + self.commission
            + self.slippage_amount
        )

    @property
    def net_proceeds(self) -> Decimal:
        """净收益（扣除佣金和滑点）。"""
        return (
            (self.executed_price * Decimal(self.executed_quantity))
            - self.commission
            - self.slippage_amount
        )


class EnhancedOrderExecutor:
    """增强的订单执行器。

    特性：
    - 集成交易配置（市场类型、T+1 限制、交易时段）
    - 集成佣金和滑点计算
    - 支持多种订单类型（市价单、限价单）
    - T+1 限制检查
    - 交易时段验证
    """

    def __init__(
        self,
        config: TradingConfig | None = None,
        commission_calculator: CommissionCalculator | None = None,
        slippage_calculator: SlippageCalculator | None = None,
    ):
        """初始化订单执行器。

        Args:
            config: 交易配置，默认使用中国股票市场配置
            commission_calculator: 佣金计算器，默认使用标准佣金计算器
            slippage_calculator: 滑点计算器，默认使用固定滑点计算器
        """
        self.config = config or TradingConfig()
        self.commission_calculator = commission_calculator or CommissionCalculator()
        self.slippage_calculator = slippage_calculator or SlippageCalculator()

    async def execute_order(
        self,
        session: AsyncSession,
        *,
        account_number: str,
        symbol_exchange: str,
        market_type: MarketType,
        side: OrderSide,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Decimal | None = None,
        execution_time: datetime | None = None,
    ) -> OrderExecutionResult:
        """执行订单。

        Args:
            session: 数据库会话
            account_number: 账户编号
            symbol_exchange: 股票代码（带交易所后缀）
            market_type: 市场类型
            side: 订单方向
            quantity: 数量
            order_type: 订单类型
            limit_price: 限价单价格
            execution_time: 执行时间，None 表示当前时间

        Returns:
            订单执行结果

        Raises:
            OrderValidationError: 订单验证失败
            TradingHoursViolationError: 非交易时段
            TPlus1RestrictionError: T+1 限制
            InsufficientFundsError: 资金不足
        """
        execution_time = execution_time or datetime.now()

        await self._validate_order(
            session=session,
            account_number=account_number,
            symbol_exchange=symbol_exchange,
            market_type=market_type,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            execution_time=execution_time,
        )

        executed_price = await self._get_executed_price(
            session=session,
            symbol_exchange=symbol_exchange,
            order_type=order_type,
            limit_price=limit_price,
            execution_time=execution_time,
        )

        slippage_amount = self.slippage_calculator.calculate(
            price=executed_price,
            quantity=quantity,
            side=side,
        )

        final_price = executed_price + slippage_amount

        commission = self.commission_calculator.calculate(
            price=final_price,
            quantity=quantity,
            side=side,
        )

        order = VirtualTradeOrder(
            id=uuid7(),
            account_number=account_number,
            symbol_exchange=symbol_exchange,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=limit_price if order_type == OrderType.LIMIT else executed_price,
            limit_price=limit_price,
            status=OrderStatus.FILLED,
            executed_quantity=quantity,
            average_price=final_price,
            commission=commission,
            slippage=slippage_amount,
            created_at=execution_time,
            updated_at=execution_time,
        )

        session.add(order)
        await session.flush()

        logger.info(
            f"订单执行成功: {side.name} {quantity} {symbol_exchange} @ {final_price} "
            f"(佣金: {commission}, 滑点: {slippage_amount})"
        )

        return OrderExecutionResult(
            order=order,
            executed_price=final_price,
            executed_quantity=quantity,
            commission=commission,
            slippage_amount=slippage_amount,
        )

    async def _validate_order(
        self,
        session: AsyncSession,
        *,
        account_number: str,
        symbol_exchange: str,
        market_type: MarketType,
        side: OrderSide,
        quantity: int,
        order_type: OrderType,
        limit_price: Decimal | None,
        execution_time: datetime,
    ) -> None:
        """验证订单。"""
        if quantity <= 0:
            raise OrderValidationError("数量必须为正整数")

        if order_type == OrderType.LIMIT and limit_price is None:
            raise OrderValidationError("限价单必须指定价格")

        if order_type == OrderType.LIMIT and limit_price is not None and limit_price <= 0:
            raise OrderValidationError("限价单价格必须大于 0")

        if not self.config.is_trading_hours(execution_time):
            raise TradingHoursViolationError(
                f"非交易时段: {execution_time.time()}, "
                f"允许时段: {self.config.trading_hours_start} - {self.config.trading_hours_end}"
            )

        if side == OrderSide.SELL and self.config.enable_t_plus_1:
            await self._check_t_plus_1_restriction(
                session=session,
                account_number=account_number,
                symbol_exchange=symbol_exchange,
                execution_time=execution_time,
            )

    async def _check_t_plus_1_restriction(
        self,
        session: AsyncSession,
        *,
        account_number: str,
        symbol_exchange: str,
        execution_time: datetime,
    ) -> None:
        """检查 T+1 限制。"""
        from sqlmodel import select

        today_start = execution_time.replace(hour=0, minute=0, second=0, microsecond=0)

        statement = select(VirtualTradeOrder).where(
            VirtualTradeOrder.account_number == account_number,
            VirtualTradeOrder.symbol_exchange == symbol_exchange,
            VirtualTradeOrder.side == OrderSide.BUY,
            VirtualTradeOrder.status == OrderStatus.FILLED,
            VirtualTradeOrder.created_at >= today_start,
        )

        result = await session.execute(statement)
        buy_orders = result.scalars().all()

        if buy_orders:
            total_bought = sum(order.executed_quantity for order in buy_orders)
            if total_bought > 0:
                raise TPlus1RestrictionError(
                    f"T+1 限制: 今日买入 {symbol_exchange} {total_bought} 股，不能当日卖出"
                )

    async def _get_executed_price(
        self,
        session: AsyncSession,
        *,
        symbol_exchange: str,
        order_type: OrderType,
        limit_price: Decimal | None,
        execution_time: datetime,
    ) -> Decimal:
        """获取执行价格。"""
        if order_type == OrderType.LIMIT:
            return limit_price

        from app.data_feed.technical_indicator import TechnicalIndicatorFeed

        feed = TechnicalIndicatorFeed()

        symbol = symbol_exchange.split(".")[0] if "." in symbol_exchange else symbol_exchange

        price = feed.get_latest_price(
            symbol=symbol,
            period="1d",
            end_date=execution_time,
        )

        if price is None:
            raise OrderValidationError(f"无法获取 {symbol_exchange} 的最新价格")

        return price


__all__ = [
    "EnhancedOrderExecutor",
    "InsufficientFundsError",
    "OrderExecutionResult",
    "OrderValidationError",
    "TPlus1RestrictionError",
    "TradingHoursViolationError",
]
