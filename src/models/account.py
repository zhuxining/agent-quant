"""SQLModel schemas for trading account persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import Column, DateTime
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel

from src.quant.core.types import AccountSnapshot, ExecutedTrade, PositionSnapshot
from src.utils.utils import utc_now

from .base_model import BaseModel


def _utc_column(comment: str) -> Column[datetime]:
	"""Build a timezone-aware DateTime column with the provided comment."""
	return Column(DateTime(timezone=True), nullable=False, comment=comment)


class AccountBase(SQLModel):
	"""Shared account fields."""

	cash: float = Field(default=0.0, sa_column_kwargs={"comment": "账户现金余额"})
	realized_pnl: float = Field(default=0.0, sa_column_kwargs={"comment": "已实现盈亏"})
	snapshot_at: datetime = Field(default_factory=utc_now, sa_column=_utc_column("账户快照时间"))


class AccountRecord(BaseModel, AccountBase, table=True):
	"""账户快照持久化模型。"""

	__tablename__: ClassVar[str] = "quant_accounts"
	__table_args__ = {"comment": "交易账户状态表"}

	account_id: str = Field(index=True, unique=True, sa_column_kwargs={"comment": "账户唯一标识"})

	def to_snapshot(self, positions: dict[str, PositionSnapshot]) -> AccountSnapshot:
		"""Convert persisted state into an in-memory snapshot."""
		return AccountSnapshot(
			cash=self.cash,
			positions=positions,
			realized_pnl=self.realized_pnl,
			timestamp=self.snapshot_at,
		)

	def apply_snapshot(self, snapshot: AccountSnapshot) -> None:
		"""Update stored values based on the provided snapshot."""
		self.cash = snapshot.cash
		self.realized_pnl = snapshot.realized_pnl
		self.snapshot_at = snapshot.timestamp


class PositionBase(SQLModel):
	"""Shared position columns."""

	symbol: str = Field(index=True, sa_column_kwargs={"comment": "标的代码"})
	quantity: float = Field(sa_column_kwargs={"comment": "持仓数量"})
	avg_price: float = Field(sa_column_kwargs={"comment": "持仓成本价"})
	last_price: float | None = Field(default=None, sa_column_kwargs={"comment": "最近成交价"})
	marked_at: datetime = Field(default_factory=utc_now, sa_column=_utc_column("持仓快照时间"))


class PositionRecord(PositionBase, table=True):
	"""账户持仓记录。"""

	__tablename__: ClassVar[str] = "quant_positions"
	__table_args__ = {"comment": "账户持仓表"}

	id: int | None = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "主键ID"})
	account_id: str = Field(
		foreign_key="quant_accounts.account_id",
		index=True,
		sa_column_kwargs={"comment": "所属账户"},
	)

	def to_snapshot(self) -> PositionSnapshot:
		"""Return in-memory representation of the position."""
		return PositionSnapshot(
			symbol=self.symbol,
			quantity=self.quantity,
			avg_price=self.avg_price,
			last_price=self.last_price,
		)

	@classmethod
	def from_snapshot(cls, account_id: str, snapshot: PositionSnapshot) -> PositionRecord:
		"""Create a persistent record from a snapshot."""
		return cls(
			account_id=account_id,
			symbol=snapshot.symbol,
			quantity=snapshot.quantity,
			avg_price=snapshot.avg_price,
			last_price=snapshot.last_price,
		)


class TradeBase(SQLModel):
	"""Shared trade execution columns."""

	symbol: str = Field(index=True, sa_column_kwargs={"comment": "成交标的"})
	side: str = Field(sa_column_kwargs={"comment": "买卖方向"})
	quantity: float = Field(sa_column_kwargs={"comment": "成交数量"})
	price: float = Field(sa_column_kwargs={"comment": "成交价格"})
	realized_pnl: float = Field(default=0.0, sa_column_kwargs={"comment": "本次已实现盈亏"})
	executed_at: datetime = Field(default_factory=utc_now, sa_column=_utc_column("成交时间"))
	extra: dict[str, Any] = Field(
		default_factory=dict,
		sa_column=Column(JSON, nullable=False, comment="附加字段"),
	)


class TradeRecord(TradeBase, table=True):
	"""成交流水记录。"""

	__tablename__: ClassVar[str] = "quant_trades"
	__table_args__ = {"comment": "成交日志表"}

	id: int | None = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "主键ID"})
	account_id: str = Field(
		foreign_key="quant_accounts.account_id",
		index=True,
		sa_column_kwargs={"comment": "所属账户"},
	)

	@classmethod
	def from_trade(cls, account_id: str, trade: ExecutedTrade) -> TradeRecord:
		"""Persist an executed trade."""
		return cls(
			account_id=account_id,
			symbol=trade.symbol,
			side=trade.side,
			quantity=trade.quantity,
			price=trade.price,
			realized_pnl=trade.realized_pnl,
			executed_at=trade.executed_at,
			extra=trade.metadata,
		)

	def to_trade(self) -> ExecutedTrade:
		"""Rehydrate the domain trade representation."""
		return ExecutedTrade(
			symbol=self.symbol,
			side=self.side,
			quantity=self.quantity,
			price=self.price,
			realized_pnl=self.realized_pnl,
			executed_at=self.executed_at,
			metadata=self.extra,
		)
