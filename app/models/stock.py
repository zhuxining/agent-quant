from typing import Any, ClassVar

from sqlmodel import Field, SQLModel

from .base_model import BaseModel


class StockBase(SQLModel):
	symbol: str = Field(index=True, sa_column_kwargs={"comment": "标的代码, 例如 AAPL"})
	name: str = Field(sa_column_kwargs={"comment": "公司名称"})
	exchange: str = Field(sa_column_kwargs={"comment": "交易所代码, 例如 NASDAQ"})
	currency: str = Field(default="USD", sa_column_kwargs={"comment": "结算货币"})
	lot_size: int = Field(default=1, ge=1, sa_column_kwargs={"comment": "最小下单股数"})
	is_active: bool = Field(default=True, sa_column_kwargs={"comment": "是否允许交易"})


class Stock(BaseModel, StockBase, table=True):
	__tablename__: ClassVar[Any] = "stock"
	__table_args__ = {"comment": "可交易股票列表"}


class StockCreate(StockBase):
	pass


class StockUpdate(StockBase):
	pass


class StockRead(BaseModel, StockBase):
	pass
