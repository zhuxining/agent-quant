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
from .order import (
    InsufficientPositionQuantityError,
    OrderExecutionResult,
    PositionNotFoundError,
    TradeOrderError,
    place_buy_order,
    place_sell_order,
)
from .position import (
    PositionSummary,
    apply_buy_to_position,
    apply_sell_to_position,
    calculate_realized_pnl,
    calculate_unrealized,
    get_position_for_update,
    list_position_summaries,
)

__all__ = [
    # account
    "AccountOverview",
    "AccountSnapshot",
    "InsufficientBuyingPowerError",
    # order
    "InsufficientPositionQuantityError",
    "OrderExecutionResult",
    "PositionNotFoundError",
    # position
    "PositionSummary",
    "TradeAccountError",
    "TradeAccountNotFoundError",
    "TradeOrderError",
    "apply_buy_to_position",
    "apply_order_settlement",
    "apply_sell_to_position",
    "build_account_overview",
    "calculate_realized_pnl",
    "calculate_unrealized",
    "get_account_snapshot",
    "get_position_for_update",
    "list_position_summaries",
    "place_buy_order",
    "place_sell_order",
]
