"""Paper Trading 交易配置。"""

from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from app.core.config import settings


class TradingConfig(BaseModel):
    """Paper Trading 交易配置。"""

    # ==================== 手续费配置 ==================== #

    commission_rate: Decimal = Field(
        default=Decimal("0.0003"),
        ge=Decimal("0"),
        le=Decimal("0.0005"),
        description="万三手续费率（每成交金额的 0.03%）",
    )

    # ==================== 滑点配置 ==================== #

    slippage_pct: Decimal = Field(
        default=Decimal("0.001"),
        ge=Decimal("0"),
        description="滑点率（百分比，默认 0.1%）",
    )

    slippage_mode: str = Field(
        default="percentage",
        description="滑点模式：percentage（百分比）或 ticks（按价格跳动）",
    )

    # ==================== T+1 交易规则 ==================== #

    t_plus_1_enabled: bool = Field(
        default=False,
        description="是否启用 T+1 交易规则（成交优先）",
    )

    t_plus_1_delay_seconds: int = Field(
        default=0,
        ge=0,
        description="T+1 交易延迟秒数",
    )

    # ==================== 等级订单类型 ==================== #

    iceberg_orders_enabled: bool = Field(
        default=False,
        description="是否启用冰山订单（大额分批成交）",
    )

    conditional_orders_enabled: bool = Field(
        default=False,
        description="是否启用条件单（止盈触发）",
    )

    # ==================== 持金使用限制 ==================== #

    position_limit_pct: Decimal = Field(
        default=Decimal("0.2"),
        ge=Decimal("0"),
        description="单个标的最大持仓比例（20%）",
    )

    max_positions: int = Field(
        default=3,
        ge=1,
        description="同时最大持仓标的数",
    )

    # ==================== 止损止盈 ==================== #

    default_stop_loss_pct: Decimal = Field(
        default=Decimal("0.02"),
        ge=Decimal("0"),
        description="默认止损比例（2%）",
    )

    default_take_profit_pct: Decimal = Decimal("0.05"),
        ge=Decimal("0"),
        description="默认止盈比例（5%）",
    )

    min_trade_amount: Decimal = Field(
        default=Decimal("100"),
        ge=Decimal("100"),
        description="最小交易金额",
    )


class TradingConfigFactory:
    """TradingConfig 工厂函数。"""

    @staticmethod
    def get_default_config() -> TradingConfig:
        """获取默认配置。"""
        return TradingConfig()

    @staticmethod
    def get_from_dict(config_dict: dict) -> TradingConfig:
        """从字典创建配置对象。"""
        return TradingConfig(**config_dict)

    @staticmethod
    def get_from_env() -> TradingConfig:
        """从环境变量或 settings 获取配置。"""
        # 可以从环境变量读取（扩展性）
        return TradingConfig()


def get_trading_config() -> TradingConfig:
    """获取当前交易配置。"""
    return TradingConfigFactory.get_from_env()


__all__ = [
    "TradingConfig",
    "TradingConfigFactory",
    "get_trading_config",
    "get_default_config",
    "get_from_dict",
    "get_from_env",
]
