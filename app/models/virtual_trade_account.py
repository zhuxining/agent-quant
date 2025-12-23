from decimal import Decimal
from typing import Any, ClassVar

from sqlmodel import Field, SQLModel

from .base_model import BaseModel


class VirtualTradeAccountBase(SQLModel):
    name: str = Field(sa_column_kwargs={"comment": "交易账户名称"})
    account_number: str = Field(
        index=True, sa_column_kwargs={"comment": "交易账户号", "unique": True}
    )
    balance: Decimal = Field(default=Decimal("0"), sa_column_kwargs={"comment": "可用余额"})
    buying_power: Decimal = Field(default=Decimal("0"), sa_column_kwargs={"comment": "可用购买力"})
    realized_pnl: Decimal = Field(default=Decimal("0"), sa_column_kwargs={"comment": "已实现盈亏"})
    is_active: bool = Field(default=True, sa_column_kwargs={"comment": "是否启用"})
    description: str | None = Field(default=None, sa_column_kwargs={"comment": "备注说明"})


class VirtualTradeAccount(BaseModel, VirtualTradeAccountBase, table=True):
    __tablename__: ClassVar[Any] = "virtual_trade_account"
    __table_args__ = {"comment": "交易账户表"}


class VirtualTradeAccountCreate(VirtualTradeAccountBase):
    pass


class VirtualTradeAccountUpdate(VirtualTradeAccountBase):
    pass


class VirtualTradeAccountRead(BaseModel, VirtualTradeAccountBase):
    pass
