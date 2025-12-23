from typing import Any, ClassVar

from pydantic import computed_field
from sqlmodel import Field, SQLModel

from .base_model import BaseModel


class VirtualTradeStockBase(SQLModel):
    symbol: str = Field(index=True, sa_column_kwargs={"comment": "标的代码, 例如 AAPL"})
    name: str = Field(sa_column_kwargs={"comment": "公司名称"})
    exchange: str = Field(sa_column_kwargs={"comment": "交易所代码, 例如 NASDAQ"})
    lot_size: int = Field(default=1, ge=1, sa_column_kwargs={"comment": "最小下单股数"})
    is_active: bool = Field(default=True, sa_column_kwargs={"comment": "是否允许交易"})


class VirtualTradeStock(BaseModel, VirtualTradeStockBase, table=True):
    __tablename__: ClassVar[Any] = "virtual_trade_stock"
    __table_args__ = {"comment": "可交易股票列表"}


class VirtualTradeStockCreate(VirtualTradeStockBase):
    pass


class VirtualTradeStockUpdate(VirtualTradeStockBase):
    pass


class VirtualTradeStockRead(BaseModel, VirtualTradeStockBase):
    @computed_field
    @property
    def symbol_exchange(self) -> str:
        return f"{self.symbol}.{self.exchange}"
