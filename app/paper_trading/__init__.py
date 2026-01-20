"""虚拟交易业务模块。

提供账户、订单、持仓的业务逻辑处理。
"""

from .account import (
    AccountOverview,
    AccountSnapshot,
    InsufficientBuyingPowerError,
    TradeAccountError,
    TradeAccountNotFoundError,
    apply_order_settlement,
    build_account_overview,
    get_account_snapshot,
)
from .commission import CommissionCalculator
from .enhanced_order import (
    EnhancedOrderExecutor,
    InsufficientFundsError,
    OrderExecutionResult,
    OrderValidationError,
    TPlus1RestrictionError,
    TradingHoursViolationError,
)
from .order import (
    InsufficientPositionQuantityError,
    PositionNotFoundError,
    TradeOrderError,
    place_buy_order,
    place_sell_order,
)
from .position import (
    PositionOverview,
    apply_buy_to_position,
    apply_sell_to_position,
    calculate_realized_pnl,
    calculate_unrealized,
    get_position_for_update,
    list_position_overviews,
)
from .slippage import (
    AdaptiveSlippageCalculator,
    AdaptiveSlippageConfig,
    FixedSlippageCalculator,
    FixedTicksSlippageCalculator,
    NoSlippageCalculator,
    PercentageSlippageCalculator,
    SlippageCalculator,
    SlippageType,
)
from .trading_config import TradingConfig, TradingConfigFactory

__all__ = [
    # account
    "AccountOverview",
    "AccountSnapshot",
    # slippage
    "AdaptiveSlippageCalculator",
    "AdaptiveSlippageConfig",
    # commission
    "CommissionCalculator",
    # enhanced order
    "EnhancedOrderExecutor",
    "FixedSlippageCalculator",
    "FixedTicksSlippageCalculator",
    "InsufficientBuyingPowerError",
    "InsufficientFundsError",
    # order
    "InsufficientPositionQuantityError",
    "NoSlippageCalculator",
    "OrderExecutionResult",
    "OrderValidationError",
    "PercentageSlippageCalculator",
    "PositionNotFoundError",
    # position
    "PositionOverview",
    "SlippageCalculator",
    "SlippageType",
    "TPlus1RestrictionError",
    "TradeAccountError",
    "TradeAccountNotFoundError",
    "TradeOrderError",
    # trading config
    "TradingConfig",
    "TradingConfigFactory",
    "TradingHoursViolationError",
    "apply_buy_to_position",
    "apply_order_settlement",
    "apply_sell_to_position",
    "build_account_overview",
    "calculate_realized_pnl",
    "calculate_unrealized",
    "get_account_snapshot",
    "get_position_for_update",
    "list_position_overviews",
    "place_buy_order",
    "place_sell_order",
]
