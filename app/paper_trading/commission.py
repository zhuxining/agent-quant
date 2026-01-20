"""Paper Trading 手续费计算。"""

from decimal import Decimal

from pydantic import BaseModel

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
        # 中国A股最低收费 5 元
        commission_min = Decimal("5")
        min_commission = amount * config.commission_rate
        return max(min_commission, commission_min)


def calculate_commission(
    trade_amount: Decimal | float | int,
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
    from app.paper_trading.trading_config import TradingConfigFactory

    if config is None:
        config = TradingConfigFactory.get_default_config()

    if isinstance(trade_amount, (int | float)):
        if trade_amount <= 0:
            raise ValueError("交易金额必须大于0")

        amount = Decimal(str(trade_amount))
    else:
        amount = trade_amount

    commission = amount * config.commission_rate
    min_commission = commission

    return {
        "commission": commission,
        "min_commission": min_commission,
    }


__all__ = [
    "CommissionCalculator",
    "calculate_commission",
]
