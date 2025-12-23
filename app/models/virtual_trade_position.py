from decimal import Decimal
from enum import StrEnum
from typing import Any, ClassVar

from sqlmodel import Field, SQLModel

from .base_model import BaseModel


class PositionSide(StrEnum):
    LONG = "long"
    SHORT = "short"


class PositionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class VirtualTradePositionBase(SQLModel):
    account_number: str = Field(sa_column_kwargs={"comment": "所属交易账户号"})
    symbol_exchange: str = Field(sa_column_kwargs={"comment": "标的股票"})
    side: PositionSide = Field(sa_column_kwargs={"comment": "持仓方向 (多/空)"})
    quantity: int = Field(ge=0, sa_column_kwargs={"comment": "当前总持仓数量"})
    available_quantity: int = Field(ge=0, sa_column_kwargs={"comment": "可交易数量 (扣除冻结部分)"})
    average_cost: Decimal = Field(default=Decimal("0"), sa_column_kwargs={"comment": "持仓成本价"})
    market_price: Decimal | None = Field(
        default=None, sa_column_kwargs={"comment": "最新行情价, 无则为空"}
    )
    market_value: Decimal = Field(
        default=Decimal("0"), sa_column_kwargs={"comment": "最新持仓市值"}
    )
    unrealized_pnl: Decimal = Field(default=Decimal("0"), sa_column_kwargs={"comment": "浮动盈亏"})
    realized_pnl: Decimal = Field(default=Decimal("0"), sa_column_kwargs={"comment": "已实现盈亏"})
    status: PositionStatus = Field(
        default=PositionStatus.OPEN, sa_column_kwargs={"comment": "持仓状态"}
    )
    profit_target: Decimal | None = Field(default=None, sa_column_kwargs={"comment": "止盈目标价"})
    stop_loss: Decimal | None = Field(default=None, sa_column_kwargs={"comment": "止损目标价"})
    notes: str | None = Field(default=None, sa_column_kwargs={"comment": "备注说明"})


class VirtualTradePosition(BaseModel, VirtualTradePositionBase, table=True):
    __tablename__: ClassVar[Any] = "virtual_trade_position"
    __table_args__ = {"comment": "交易账户持仓表"}


class VirtualTradePositionCreate(VirtualTradePositionBase):
    pass


class VirtualTradePositionUpdate(SQLModel):
    quantity: int | None = Field(default=None, ge=0, description="当前总持仓数量")
    available_quantity: int | None = Field(default=None, ge=0, description="可交易数量")
    average_cost: Decimal | None = Field(default=None, description="持仓成本")
    market_price: Decimal | None = Field(default=None, description="最新行情价")
    market_value: Decimal | None = Field(default=None, description="最新市值")
    unrealized_pnl: Decimal | None = Field(default=None, description="浮动盈亏")
    realized_pnl: Decimal | None = Field(default=None, description="已实现盈亏")
    status: PositionStatus | None = Field(default=None, description="持仓状态")
    profit_target: Decimal | None = Field(default=None, sa_column_kwargs={"comment": "止盈目标价"})
    stop_loss: Decimal | None = Field(default=None, sa_column_kwargs={"comment": "止损目标价"})
    notes: str | None = Field(default=None, description="备注")


class VirtualTradePositionRead(BaseModel, VirtualTradePositionBase):
    pass
