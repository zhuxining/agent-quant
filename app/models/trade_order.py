from decimal import Decimal
from enum import StrEnum
from typing import Any, ClassVar

from sqlmodel import Field, SQLModel

from .base_model import BaseModel


class OrderSide(StrEnum):
	BUY = "buy"
	SELL = "sell"


class OrderType(StrEnum):
	MARKET = "market"
	LIMIT = "limit"


class TradeOrderStatus(StrEnum):
	PENDING = "pending"
	FILLED = "filled"
	CANCELLED = "cancelled"
	FAILED = "failed"


class TradeOrderBase(SQLModel):
	account_number: str = Field(sa_column_kwargs={"comment": "下单账户号"})
	symbol_exchange: str = Field(sa_column_kwargs={"comment": "标的股票"})
	side: OrderSide = Field(sa_column_kwargs={"comment": "买卖方向"})
	order_type: OrderType = Field(
		default=OrderType.MARKET, sa_column_kwargs={"comment": "订单类型 (市价/限价)"}
	)
	quantity: int = Field(gt=0, sa_column_kwargs={"comment": "委托数量"})
	price: Decimal | None = Field(default=None, sa_column_kwargs={"comment": "委托价格"})
	status: TradeOrderStatus = Field(
		default=TradeOrderStatus.PENDING, sa_column_kwargs={"comment": "订单状态"}
	)
	executed_quantity: int = Field(default=0, ge=0, sa_column_kwargs={"comment": "已成交数量"})
	average_price: Decimal | None = Field(
		default=None, sa_column_kwargs={"comment": "成交均价 (如有)"}
	)
	notes: str | None = Field(default=None, sa_column_kwargs={"comment": "订单备注"})


class TradeOrder(BaseModel, TradeOrderBase, table=True):
	__tablename__: ClassVar[Any] = "trade_order"
	__table_args__ = {"comment": "交易订单表"}


class TradeOrderCreate(TradeOrderBase):
	pass


class TradeOrderUpdate(SQLModel):
	status: TradeOrderStatus | None = Field(default=None, description="订单状态")
	executed_quantity: int | None = Field(default=None, ge=0, description="已成交数量")
	average_price: Decimal | None = Field(default=None, description="成交均价")
	price: Decimal | None = Field(default=None, description="最新委托价格")
	external_order_id: str | None = Field(default=None, description="券商订单号")
	notes: str | None = Field(default=None, description="备注信息")


class TradeOrderRead(BaseModel, TradeOrderBase):
	pass
