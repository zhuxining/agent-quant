"""回测运行记录模型。"""

import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, ClassVar

from sqlmodel import Field, SQLModel

from app.models.base_model import BaseModel


class BacktestStatus(StrEnum):
    """回测运行状态。"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BacktestRunBase(SQLModel):
    """回测运行记录基类。"""

    name: str = Field(sa_column_kwargs={"comment": "回测名称"})
    symbols: str = Field(sa_column_kwargs={"comment": "标的列表 (JSON)"})
    start_date: datetime.date = Field(sa_column_kwargs={"comment": "回测开始日期"})
    end_date: datetime.date = Field(sa_column_kwargs={"comment": "回测结束日期"})
    interval_days: int = Field(default=1, sa_column_kwargs={"comment": "决策间隔天数"})
    initial_capital: Decimal = Field(
        default=Decimal("1000000"),
        sa_column_kwargs={"comment": "初始资金"},
    )
    account_number: str = Field(sa_column_kwargs={"comment": "回测专用账户号"})
    status: BacktestStatus = Field(
        default=BacktestStatus.PENDING,
        sa_column_kwargs={"comment": "运行状态"},
    )
    final_equity: Decimal | None = Field(
        default=None,
        sa_column_kwargs={"comment": "最终净值"},
    )
    total_return: float | None = Field(
        default=None,
        sa_column_kwargs={"comment": "总收益率 (%)"},
    )
    sharpe_ratio: float | None = Field(
        default=None,
        sa_column_kwargs={"comment": "夏普比率"},
    )
    max_drawdown: float | None = Field(
        default=None,
        sa_column_kwargs={"comment": "最大回撤 (%)"},
    )
    error_message: str | None = Field(
        default=None,
        sa_column_kwargs={"comment": "错误信息"},
    )


class BacktestRun(BaseModel, BacktestRunBase, table=True):
    """回测运行记录表。"""

    __tablename__: ClassVar[Any] = "backtest_run"
    __table_args__ = {"comment": "回测运行记录表"}


class BacktestRunCreate(BacktestRunBase):
    """创建回测运行的输入模型。"""

    pass


class BacktestRunRead(BaseModel, BacktestRunBase):
    """回测运行的输出模型。"""

    pass


__all__ = [
    "BacktestRun",
    "BacktestRunCreate",
    "BacktestRunRead",
    "BacktestStatus",
]
