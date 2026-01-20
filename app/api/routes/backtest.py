"""回测配置 API 端点。"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import ClassVar

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.deps import CurrentUserDep
from app.models.backtest import (
    BacktestMode,
    VectorizedStrategyConfig,
)
from app.utils.responses import ResponseEnvelope, success_response

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRunCreate(BaseModel):
    """创建回测运行请求。"""

    name: ClassVar[str] = "我的回测"
    mode: ClassVar[BacktestMode] = BacktestMode.VECTORIZED

    symbols: ClassVar[list[str]] = ["000001.SZ"]
    start_date: ClassVar[date] = date(2024, 1, 1)
    end_date: ClassVar[date] = date(2024, 12, 31)

    initial_capital: ClassVar[Decimal] = Decimal("100000")

    strategy_config: VectorizedStrategyConfig | None = None

    commission_rate: Decimal | None = None
    slippage_rate: Decimal | None = None


class BacktestRunResponse(BaseModel):
    """回测运行响应。"""

    run_id: str
    status: str
    total_return: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown: float | None = None
    message: str


@router.get("/config/strategies", response_model=ResponseEnvelope[VectorizedStrategyConfig])
async def get_strategy_config(
    current_user: CurrentUserDep,
):
    """获取默认策略配置。

    Returns:
        策略配置
    """
    default_config = VectorizedStrategyConfig()
    return success_response(data=default_config)


@router.post("/config/strategies", response_model=ResponseEnvelope[dict])
async def save_strategy_config(
    config: VectorizedStrategyConfig,
    current_user: CurrentUserDep,
):
    """保存策略配置。

    Args:
        config: 策略配置

    Returns:
        操作结果
    """
    return success_response(
        data={"message": "策略配置已保存（功能开发中）"},
    )


__all__ = [
    "router",
]
