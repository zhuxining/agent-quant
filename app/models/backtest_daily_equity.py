"""回测每日净值快照模型。"""

import datetime
from decimal import Decimal
from typing import Any, ClassVar
from uuid import UUID

from sqlmodel import Field, SQLModel

from app.models.base_model import BaseModel


class BacktestDailyEquityBase(SQLModel):
    """每日净值快照基类。"""

    backtest_run_id: UUID = Field(
        foreign_key="backtest_run.id",
        sa_column_kwargs={"comment": "所属回测运行"},
    )
    trade_date: datetime.date = Field(sa_column_kwargs={"comment": "日期"})
    equity: Decimal = Field(sa_column_kwargs={"comment": "总净值"})
    cash: Decimal = Field(sa_column_kwargs={"comment": "现金余额"})
    market_value: Decimal = Field(sa_column_kwargs={"comment": "持仓市值"})
    daily_return: float | None = Field(
        default=None,
        sa_column_kwargs={"comment": "日收益率 (%)"},
    )


class BacktestDailyEquity(BaseModel, BacktestDailyEquityBase, table=True):
    """每日净值快照表。"""

    __tablename__: ClassVar[Any] = "backtest_daily_equity"
    __table_args__ = {"comment": "每日净值快照表"}


class BacktestDailyEquityCreate(BacktestDailyEquityBase):
    """创建每日净值的输入模型。"""

    pass


class BacktestDailyEquityRead(BaseModel, BacktestDailyEquityBase):
    """每日净值的输出模型。"""

    pass


__all__ = [
    "BacktestDailyEquity",
    "BacktestDailyEquityCreate",
    "BacktestDailyEquityRead",
]
