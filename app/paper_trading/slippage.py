"""滑点计算器 - 模拟交易时的价格滑点。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.models import OrderSide


class SlippageType(Enum):
    """滑点类型。"""

    NONE = "none"
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    FIXED_TICKS = "fixed_ticks"


class SlippageCalculator(ABC):
    """滑点计算器抽象基类。"""

    @abstractmethod
    def calculate(
        self,
        price: Decimal,
        quantity: int,
        side: OrderSide,
    ) -> Decimal:
        """计算滑点金额。

        Args:
            price: 基准价格
            quantity: 数量
            side: 订单方向

        Returns:
            滑点金额（正数表示成本增加，负数表示成本减少）
        """
        pass


class NoSlippageCalculator(SlippageCalculator):
    """无滑点计算器。"""

    def calculate(
        self,
        price: Decimal,
        quantity: int,
        side: OrderSide,
    ) -> Decimal:
        return Decimal("0")


class FixedSlippageCalculator(SlippageCalculator):
    """固定滑点计算器。"""

    def __init__(self, slippage_per_share: Decimal):
        """初始化固定滑点计算器。

        Args:
            slippage_per_share: 每股滑点金额
        """
        self.slippage_per_share = slippage_per_share

    def calculate(
        self,
        price: Decimal,
        quantity: int,
        side: OrderSide,
    ) -> Decimal:
        slippage = self.slippage_per_share * quantity
        return slippage if side == OrderSide.BUY else -slippage


class PercentageSlippageCalculator(SlippageCalculator):
    """百分比滑点计算器。"""

    def __init__(self, slippage_rate: Decimal):
        """初始化百分比滑点计算器。

        Args:
            slippage_rate: 滑点百分比（例如 0.001 表示 0.1%）
        """
        self.slippage_rate = slippage_rate

    def calculate(
        self,
        price: Decimal,
        quantity: int,
        side: OrderSide,
    ) -> Decimal:
        total_value = price * quantity
        slippage = total_value * self.slippage_rate
        return slippage if side == OrderSide.BUY else -slippage


class FixedTicksSlippageCalculator(SlippageCalculator):
    """固定 tick 滑点计算器。

    滑点按最小价格变动单位（tick）计算。
    """

    def __init__(self, tick_size: Decimal, ticks: int = 1):
        """初始化固定 tick 滑点计算器。

        Args:
            tick_size: 最小价格变动单位
            ticks: 滑动的 tick 数量，默认 1
        """
        self.tick_size = tick_size
        self.ticks = ticks

    def calculate(
        self,
        price: Decimal,
        quantity: int,
        side: OrderSide,
    ) -> Decimal:
        slippage_per_share = self.tick_size * self.ticks
        total_slippage = slippage_per_share * quantity
        return total_slippage if side == OrderSide.BUY else -total_slippage


@dataclass
class AdaptiveSlippageConfig:
    """自适应滑点配置。"""

    base_rate: Decimal = Decimal("0.001")
    volume_factor: Decimal = Decimal("0.0001")
    min_slippage: Decimal = Decimal("0.0005")
    max_slippage: Decimal = Decimal("0.003")


class AdaptiveSlippageCalculator(SlippageCalculator):
    """自适应滑点计算器。

    根据交易量动态调整滑点大小。
    """

    def __init__(self, config: AdaptiveSlippageConfig | None = None):
        """初始化自适应滑点计算器。

        Args:
            config: 滑点配置，默认使用标准配置
        """
        self.config = config or AdaptiveSlippageConfig()

    def calculate(
        self,
        price: Decimal,
        quantity: int,
        side: OrderSide,
    ) -> Decimal:
        total_value = price * quantity

        slippage_rate = self._calculate_rate(total_value)
        slippage = total_value * slippage_rate

        return slippage if side == OrderSide.BUY else -slippage

    def _calculate_rate(self, total_value: Decimal) -> Decimal:
        """根据交易量计算滑点率。"""
        base_rate = self.config.base_rate

        volume_factor = (total_value / Decimal("100000")) * self.config.volume_factor

        rate = base_rate + volume_factor

        rate = max(rate, self.config.min_slippage)
        rate = min(rate, self.config.max_slippage)

        return rate


__all__ = [
    "AdaptiveSlippageCalculator",
    "AdaptiveSlippageConfig",
    "FixedSlippageCalculator",
    "FixedTicksSlippageCalculator",
    "NoSlippageCalculator",
    "PercentageSlippageCalculator",
    "SlippageCalculator",
    "SlippageType",
]
