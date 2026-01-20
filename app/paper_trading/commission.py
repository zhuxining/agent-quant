"""Paper Trading 手续费计算。"""

from decimal import Decimal

from pydantic import BaseModel, Field

from app.paper_trading.trading_config import TradingConfig


class CommissionCalculator(BaseModel):
    """手续费计算器。"""

    def calculate_by_amount(
        self,
        amount: Decimal,
        config: TradingConfig,
    ) -> Decimal:
        """按成交金额计算手续费。

        Args:
            amount: 成交金额
            config: 交易配置

        Returns:
            手续费金额
        """
        return amount * config.commission_rate

    def calculate_by_shares(
        self,
        shares: int,
        price: Decimal,
        config: TradingConfig,
    ) -> Decimal:
        """按成交股数和价格计算手续费。

        Args:
            shares: 成交股数
            price: 成交价
            config: 交易配置

        Returns:
            手续费金额
        """
        return Decimal(shares) * price * config.commission_rate / 10000

    def calculate_min_commission(
        self,
        amount: Decimal,
        config: TradingConfig,
    ) -> Decimal:
        """计算最小手续费（根据最低收费门槛）。

        Args:
            amount: 成交金额
            config: 交易配置

        Returns:
            最小手续费
        """
        min_commission = amount * config.commission_rate

        if config.commission_min is not None:
            min_amount = max(min_commission, config.commission_min)
        else:
            min_amount = amount * config.commission_rate

        return max(min_commission, min_amount)


def calculate_commission(
    trade_amount: Decimal | float | Decimal,
    config: TradingConfig | None = None,
) -> dict:
    """计算手续费（支持单笔和批量）。

    Args:
        trade_amount: 交易金额或股数
        config: 交易配置

    Returns:
            {
                "commission": 手续费金额,
                "min_commission": 最小手续费,
            }
    """
    if config is None:
        config = get_default_config()

    if isinstance(trade_amount, (int | float)):
        if trade_amount <= 0:
            raise ValueError("交易金额必须大于0")

        amount = Decimal(strade_amount)

    commission = amount * config.commission_rate
    min_commission = calculate_min_commission(amount, config)

    min_amount = config.commission_min
    if min_amount is not None:
        min_amount = max(commission, min_amount)

    return {
        "commission": commission,
        "min_commission": min_commission,
    }


__all__ = [
    "calculate_commission",
    "CommissionCalculator",
]
