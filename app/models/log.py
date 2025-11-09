from enum import StrEnum
from typing import Any, ClassVar

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel

from .base_model import BaseModel


class LogLevel(StrEnum):
	DEBUG = "debug"
	INFO = "info"
	WARNING = "warning"
	ERROR = "error"
	CRITICAL = "critical"


class LogBase(SQLModel):
	level: LogLevel = Field(sa_column_kwargs={"comment": "日志级别"})
	message: str = Field(sa_column_kwargs={"comment": "日志内容"})
	source: str | None = Field(default=None, sa_column_kwargs={"comment": "日志来源模块"})
	trace_id: str | None = Field(default=None, sa_column_kwargs={"comment": "请求或任务追踪ID"})
	extra: dict[str, Any] | None = Field(
		default=None,
		sa_column=Column(JSON, comment="额外字段(JSON)"),
	)


class Log(BaseModel, LogBase, table=True):
	__tablename__: ClassVar[Any] = "log"
	__table_args__ = {"comment": "应用日志记录"}


class LogCreate(LogBase):
	pass


class LogRead(BaseModel, LogBase):
	pass
