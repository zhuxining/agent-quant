"""历史事件管理器。

提供历史事件的 CRUD 操作和影响分析。
"""

from datetime import date, datetime
from typing import ClassVar
from uuid import UUID

from loguru import logger
from sqlmodel import Session, desc, select

from app.models.historical_event import (
    EventImpactAnalysis,
    EventType,
    HistoricalEvent,
    HistoricalEventCreate,
    HistoricalEventUpdate,
)


class ImpactScoreCalculator:
    """影响评分计算器。"""

    POSITIVE_KEYWORDS: ClassVar[list[str]] = [
        "利好",
        "超预期",
        "突破",
        "增长",
        "收购",
        "业绩",
        "盈利",
        "复苏",
        "强势",
        "增长",
        "上涨",
        "拉升",
    ]

    NEGATIVE_KEYWORDS: ClassVar[list[str]] = [
        "利空",
        "不及预期",
        "下跌",
        "风险",
        "监管",
        "处罚",
        "调查",
        "亏损",
        "下滑",
        "弱势",
        "暴跌",
        "回调",
        "跌停",
    ]

    def calculate(
        self,
        event_type: EventType,
        content: str | None,
    ) -> int:
        """计算事件影响评分。

        Args:
            event_type: 事件类型
            content: 事件内容

        Returns:
            影响评分（-5 到 5）
        """
        if event_type == EventType.NEWS and content:
            return self._calculate_news_score(content)
        elif event_type == EventType.FINANCIAL and content:
            return self._calculate_financial_score(content)
        elif event_type == EventType.POLICY and content:
            return self._calculate_policy_score(content)
        elif event_type == EventType.MACRO and content:
            return self._calculate_macro_score(content)
        else:
            return 0

    def _calculate_news_score(self, content: str) -> int:
        """计算新闻事件影响评分。"""
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in content)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in content)

        if positive_count > negative_count:
            return min(3, positive_count - negative_count)
        elif negative_count > positive_count:
            return max(-3, negative_count - positive_count)
        else:
            return 0

    def _calculate_financial_score(self, content: str) -> int:
        """计算财报事件影响评分。"""
        positive_keywords = ["超预期", "增长", "盈利", "业绩", "收入", "利润"]
        negative_keywords = ["不及预期", "下滑", "亏损", "减收", "下降"]

        if any(kw in content for kw in positive_keywords):
            return 2
        elif any(kw in content for kw in negative_keywords):
            return -2
        else:
            return 0

    def _calculate_policy_score(self, content: str) -> int:
        """计算政策事件影响评分。"""
        positive_keywords = ["利好", "支持", "放宽", "优惠", "补贴", "降准"]
        negative_keywords = ["利空", "收紧", "限制", "加息", "监管"]

        if any(kw in content for kw in positive_keywords):
            return 2
        elif any(kw in content for kw in negative_keywords):
            return -2
        else:
            return 0

    def _calculate_macro_score(self, content: str) -> int:
        """计算宏观事件影响评分。"""
        positive_keywords = ["增长", "复苏", "反弹", "企稳", "向好", "改善"]
        negative_keywords = ["衰退", "通胀", "通缩", "紧缩", "疲软"]

        if any(kw in content for kw in positive_keywords):
            return 1
        elif any(kw in content for kw in negative_keywords):
            return -1
        else:
            return 0

    def _calculate_news_score(self, content: str) -> int:
        """计算新闻事件影响评分。"""
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in content)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in content)

        if positive_count > negative_count:
            return min(3, positive_count - negative_count)
        elif negative_count > positive_count:
            return max(-3, negative_count - positive_count)
        else:
            return 0

    def _calculate_financial_score(self, content: str) -> int:
        """计算财报事件影响评分。"""
        positive_keywords = ["超预期", "增长", "盈利", "业绩", "收入", "利润"]
        negative_keywords = ["不及预期", "下滑", "亏损", "减收", "下降"]

        if any(kw in content for kw in positive_keywords):
            return 2
        elif any(kw in content for kw in negative_keywords):
            return -2
        else:
            return 0

    def _calculate_policy_score(self, content: str) -> int:
        """计算政策事件影响评分。"""
        positive_keywords = ["利好", "支持", "放宽", "优惠", "补贴", "降准"]
        negative_keywords = ["利空", "收紧", "限制", "加息", "监管"]

        if any(kw in content for kw in positive_keywords):
            return 2
        elif any(kw in content for kw in negative_keywords):
            return -2
        else:
            return 0

    def _calculate_macro_score(self, content: str) -> int:
        """计算宏观事件影响评分。"""
        positive_keywords = ["增长", "复苏", "反弹", "企稳", "向好", "改善"]
        negative_keywords = ["衰退", "通胀", "通缩", "紧缩", "疲软"]

        if any(kw in content for kw in positive_keywords):
            return 1
        elif any(kw in content for kw in negative_keywords):
            return -1
        else:
            return 0


class HistoricalEventManager:
    """历史事件管理器。

    提供历史事件的 CRUD 操作和影响分析。
    """

    def __init__(self, session: Session) -> None:
        """初始化事件管理器。

        Args:
            session: 数据库会话
        """
        self.session = session
        self.impact_calculator = ImpactScoreCalculator()

    def create_event(
        self,
        event: HistoricalEventCreate,
        source: str = "manual",
    ) -> HistoricalEvent:
        """创建历史事件。

        Args:
            event: 事件创建请求
            source: 事件来源

        Returns:
            创建的历史事件
        """
        impact_score = self.impact_calculator.calculate(event.event_type, event.content)

        new_event = HistoricalEvent(
            event_date=event.event_date,
            symbol=event.symbol,
            event_type=event.event_type,
            title=event.title,
            content=event.content,
            impact_score=impact_score,
            source=source,
        )

        self.session.add(new_event)
        self.session.flush()

        logger.info(f"创建历史事件: {event.title} (评分: {impact_score})")
        return new_event

    def get_events(
        self,
        symbol: str | None = None,
        event_type: EventType | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 100,
    ) -> list[HistoricalEvent]:
        """查询历史事件。

        Args:
            symbol: 标的代码过滤
            event_type: 事件类型过滤
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制

        Returns:
            历史事件列表
        """
        statement = select(HistoricalEvent)

        if symbol:
            statement = statement.where(HistoricalEvent.symbol == symbol)

        if event_type:
            statement = statement.where(HistoricalEvent.event_type == event_type)

        if start_date:
            statement = statement.where(HistoricalEvent.event_date >= start_date)

        if end_date:
            statement = statement.where(HistoricalEvent.event_date <= end_date)

        statement = statement.order_by(desc(HistoricalEvent.event_date))
        statement = statement.limit(limit)

        result = self.session.execute(statement)
        return list(result.scalars().all())

    def get_event_by_id(self, event_id: UUID) -> HistoricalEvent | None:
        """根据 ID 获取事件。

        Args:
            event_id: 事件 ID

        Returns:
            历史事件对象，不存在返回 None
        """
        statement = select(HistoricalEvent).where(HistoricalEvent.id == event_id)
        result = self.session.execute(statement)
        return result.scalar_one_or_none()

    def update_event(
        self,
        event_id: UUID,
        event_update: HistoricalEventUpdate,
    ) -> HistoricalEvent | None:
        """更新历史事件。

        Args:
            event_id: 事件 ID
            event_update: 更新数据

        Returns:
            更新后的事件对象，不存在返回 None
        """
        statement = select(HistoricalEvent).where(HistoricalEvent.id == event_id)
        result = self.session.execute(statement)
        event = result.scalar_one_or_none()

        if event is None:
            logger.warning(f"事件不存在: {event_id}")
            return None

        if event_update.title is not None:
            event.title = event_update.title

        if event_update.content is not None:
            event.content = event_update.content

        if event_update.impact_score is not None:
            event.impact_score = event_update.impact_score

        event.updated_at = datetime.now()

        self.session.commit()
        self.session.refresh(event)

        logger.info(f"更新历史事件: {event.title}")
        return event

    def delete_event(self, event_id: UUID) -> bool:
        """删除历史事件。

        Args:
            event_id: 事件 ID

        Returns:
            是否删除成功
        """
        statement = select(HistoricalEvent).where(HistoricalEvent.id == event_id)
        result = self.session.execute(statement)
        event = result.scalar_one_or_none()

        if event is None:
            logger.warning(f"事件不存在: {event_id}")
            return False

        self.session.delete(event)
        self.session.commit()

        logger.info(f"删除历史事件: {event.title}")
        return True

    def analyze_impact(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> EventImpactAnalysis:
        """分析事件影响统计。

        Args:
            symbol: 标的代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            影响分析结果
        """
        statement = select(HistoricalEvent).where(
            HistoricalEvent.symbol == symbol,
            HistoricalEvent.event_date >= start_date,
            HistoricalEvent.event_date <= end_date,
        )

        result = self.session.execute(statement)
        events = result.scalars().all()

        total_events = len(events)
        positive_events = sum(1 for e in events if e.impact_score > 0)
        negative_events = sum(1 for e in events if e.impact_score < 0)
        neutral_events = total_events - positive_events - negative_events

        avg_impact_score = (
            sum(e.impact_score for e in events) / total_events if total_events > 0 else 0
        )

        return EventImpactAnalysis(
            total_events=total_events,
            positive_events=positive_events,
            negative_events=negative_events,
            neutral_events=neutral_events,
            avg_impact_score=avg_impact_score,
        )

    def get_events_by_date_range(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> dict[str, list[HistoricalEvent]]:
        """按日期范围查询事件。

        Args:
            symbol: 标的代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            按日期分组的事件字典
        """
        statement = select(HistoricalEvent).where(
            HistoricalEvent.symbol == symbol,
            HistoricalEvent.event_date >= start_date,
            HistoricalEvent.event_date <= end_date,
        )

        statement = statement.order_by(desc(HistoricalEvent.event_date))

        result = self.session.execute(statement)
        events = list(result.scalars().all())

        grouped_events: dict[str, list[HistoricalEvent]] = {}
        for event in events:
            date_key = event.event_date.isoformat()
            if date_key not in grouped_events:
                grouped_events[date_key] = []
            grouped_events[date_key].append(event)

        return grouped_events


__all__ = [
    "EventImpactAnalysis",
    "HistoricalEventManager",
    "ImpactScoreCalculator",
]
