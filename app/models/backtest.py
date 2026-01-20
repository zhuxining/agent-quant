"""回测相关模型。"""

from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid7

from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField, SQLModel


class BacktestMode(str, Enum):
    """回测模式。"""

    VIRTUAL = "virtual"
    VECTORIZED = "vectorized"
    BACKTRADER = "backtrader"


class VectorizedBacktestRun(SQLModel, table=True):
    """向量化回测运行记录。"""

    __tablename__ = "vectorized_backtest_run"

    id: UUID = SQLField(
        default_factory=uuid7,
        primary_key=True,
    )
    name: str = SQLField(index=True, description="回测名称")
    symbols: str = SQLField(description="标的列表（JSON）")
    start_date: date = SQLField(description="开始日期")
    end_date: date = SQLField(description="结束日期")

    initial_capital: Decimal = SQLField(description="初始资金")
    final_capital: Decimal | None = SQLField(default=None, description="最终资金")
    total_return: Decimal | None = SQLField(default=None, description="总收益率")

    max_drawdown: Decimal | None = SQLField(default=None, description="最大回撤")
    sharpe_ratio: Decimal | None = SQLField(default=None, description="夏普比率")

    ema_short: int = SQLField(description="短期 EMA 周期")
    ema_long: int = SQLField(description="长期 EMA 周期")

    status: str = SQLField(
        default="pending",
        description="状态：pending/running/completed/failed",
    )
    error_message: str | None = SQLField(default=None, description="错误信息")

    created_at: date = SQLField(default_factory=date.today, description="创建时间")


class VectorizedStrategyConfig(BaseModel):
    """向量化策略配置。"""

    ema_short: int = Field(default=5, ge=1, description="短期 EMA 周期")
    ema_long: int = Field(default=20, ge=1, description="长期 EMA 周期")

    stop_loss_pct: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
        description="止损比例（0-1）",
    )
    take_profit_pct: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
        description="止盈比例（0-1）",
    )


class VectorizedBacktestConfig(BaseModel):
    """向量化回测配置。"""

    mode: BacktestMode = BacktestMode.VECTORIZED

    symbols: list[str] = Field(description="标的列表")
    start_date: date = Field(description="开始日期")
    end_date: date = Field(description="结束日期")

    initial_capital: Decimal = Field(default=Decimal("100000"), description="初始资金")

    strategy_config: VectorizedStrategyConfig = Field(
        default_factory=VectorizedStrategyConfig,
        description="策略配置",
    )

    commission_rate: Decimal = Field(
        default=Decimal("0.0003"),
        ge=Decimal("0"),
        le=Decimal("0.001"),
        description="佣金率（万三）",
    )

    slippage_rate: Decimal = Field(
        default=Decimal("0.001"),
        ge=Decimal("0"),
        le=Decimal("0.005"),
        description="滑点率（百分比）",
    )


class BacktestMetrics(BaseModel):
    """回测指标。"""

    total_return: Decimal = Field(description="总收益率")
    annual_return: Decimal | None = Field(default=None, description="年化收益率")
    max_drawdown: Decimal = Field(description="最大回撤")
    sharpe_ratio: Decimal | None = Field(default=None, description="夏普比率")
    sortino_ratio: Decimal | None = Field(default=None, description="索提诺比率")
    calmar_ratio: Decimal | None = Field(default=None, description="卡玛比率")

    total_trades: int = Field(description="总交易次数")
    winning_trades: int = Field(description="盈利交易次数")
    losing_trades: int = Field(description="亏损交易次数")
    win_rate: Decimal | None = Field(default=None, description="胜率")

    profit_factor: Decimal | None = Field(default=None, description="盈亏比")


__all__ = [
    "BacktestMetrics",
    "BacktestMode",
    "VectorizedBacktestConfig",
    "VectorizedBacktestRun",
    "VectorizedStrategyConfig",
]
