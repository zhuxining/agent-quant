"""SQLModel schemas for tradable symbol management."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar
from uuid import UUID

from pydantic import ConfigDict, field_validator
from sqlmodel import Field, SQLModel

from .base_model import BaseModel


class SymbolBase(SQLModel):
	"""Shared fields for tradable symbols."""

	symbol: str = Field(
		sa_column_kwargs={"comment": "标的代码，例如 AAPL.US"},
		min_length=1,
		max_length=48,
		index=True,
		unique=True,
	)
	display_name: str | None = Field(
		default=None,
		sa_column_kwargs={"comment": "展示名称"},
	)
	exchange: str | None = Field(
		default=None,
		sa_column_kwargs={"comment": "交易所或市场标识"},
	)
	sector: str | None = Field(
		default=None,
		sa_column_kwargs={"comment": "所属行业"},
	)
	priority: int = Field(
		default=0,
		sa_column_kwargs={"comment": "排序优先级，越大越靠前"},
	)
	is_active: bool = Field(
		default=True,
		sa_column_kwargs={"comment": "是否参与任务调度/信号生成"},
	)
	notes: str | None = Field(
		default=None,
		sa_column_kwargs={"comment": "额外说明"},
	)

	@field_validator("symbol")
	@classmethod
	def _normalize_symbol(cls, value: str) -> str:
		normalized = value.strip().upper()
		if not normalized:
			raise ValueError("symbol 不能为空")
		return normalized


class SymbolRecord(BaseModel, SymbolBase, table=True):
	"""Symbol persistence model."""

	__tablename__: ClassVar[str] = "quant_symbols"
	__table_args__ = {"comment": "可交易标的配置"}


class SymbolCreate(SymbolBase):
	"""Payload schema for creating symbols."""

	model_config = ConfigDict(extra="forbid")


class SymbolUpdate(SQLModel):
	"""Partial update schema for symbols."""

	model_config = ConfigDict(extra="forbid")

	display_name: str | None = None
	exchange: str | None = None
	sector: str | None = None
	priority: int | None = None
	is_active: bool | None = None
	notes: str | None = None


class SymbolRead(SymbolBase):
	"""Read model returned by APIs."""

	model_config = ConfigDict(from_attributes=True)

	id: UUID
	created_at: datetime | None = None
	updated_at: datetime | None = None
