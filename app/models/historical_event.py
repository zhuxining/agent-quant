"""历史事件模型。"""

from datetime import date, datetime
from enum import Enum
from uuid import UUID, uuid7

from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField, SQLModel


class EventType(str, Enum):
    """历史事件类型。"""

    NEWS = "news"
    FINANCIAL = "financial"
    POLICY = "policy"
    MACRO = "macro"


class HistoricalEvent(SQLModel, table=True):
    """历史事件模型。

    用于存储影响市场的重大事件（新闻、财报、政策、宏观），
    支持混合回测策略结合历史事件和基本面分析。
    """

    __tablename__ = "historical_events"

    id: UUID = SQLField(
        default_factory=uuid7,
        primary_key=True,
        index=True,
    )
    event_date: date = SQLField(
        index=True,
        description="事件日期",
    )

    symbol: str = SQLField(
        index=True,
        description="标的代码（如 000001.SZ）",
    )

    event_type: EventType = SQLField(
        index=True,
        description="事件类型：news/financial/policy/macro",
    )

    title: str = SQLField(
        description="事件标题",
    )

    content: str | None = SQLField(
        default=None,
        description="事件内容或描述",
    )

    impact_score: int = SQLField(
        ge=-5,
        le=5,
        description="影响评分（-5 到 5）",
    )

    source: str = SQLField(
        default="manual",
        description="事件来源：manual/llm/api/csv_import",
    )

    created_at: datetime = SQLField(
        default_factory=datetime.now,
        description="创建时间",
    )

    updated_at: datetime | None = SQLField(
        default=None,
        description="更新时间",
    )

    class Config:
        table_name = "historical_events"


class HistoricalEventCreate(BaseModel):
    """创建历史事件请求。"""

    event_date: date = Field(description="事件日期")
    symbol: str = Field(description="标的代码")

    event_type: EventType = Field(description="事件类型")
    title: str = Field(description="事件标题")

    content: str | None = Field(
        default=None,
        description="事件内容或描述",
    )

    impact_score: int = Field(
        ge=-5,
        le=5,
        description="影响评分（-5 到 5）",
    )

    source: str = Field(
        default="manual",
        description="事件来源：manual/llm/api/csv_import",
    )


class HistoricalEventUpdate(BaseModel):
    """更新历史事件请求。"""

    title: str | None = Field(default=None, description="新的标题")
    content: str | None = Field(default=None, description="新的内容")
    impact_score: int | None = Field(
        default=None,
        ge=-5,
        le=5,
        description="新的影响评分",
    )


class HistoricalEventResponse(BaseModel):
    """历史事件响应。"""

    id: UUID
    event_date: date
    symbol: str
    event_type: EventType
    title: str
    content: str | None
    impact_score: int
    source: str
    created_at: datetime
    updated_at: datetime | None


class EventImpactAnalysis(BaseModel):
    """事件影响分析结果。"""

    total_events: int = Field(description="总事件数")
    positive_events: int = Field(description="正面事件数")
    negative_events: int = Field(description="负面事件数")
    neutral_events: int = Field(description="中性事件数")
    avg_impact_score: float = Field(description="平均影响评分")


__all__ = [
    "EventImpactAnalysis",
    "EventType",
    "HistoricalEvent",
    "HistoricalEventCreate",
    "HistoricalEventResponse",
    "HistoricalEventUpdate",
]
