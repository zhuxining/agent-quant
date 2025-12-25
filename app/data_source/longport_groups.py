"""Longport 自选分组数据源封装。

提供基于 QuoteContext.watchlist 的分组及证券查询能力。
"""

from __future__ import annotations

from collections.abc import Iterable

from longport.openapi import (
    QuoteContext,
    SecuritiesUpdateMode,
    WatchlistGroup,
    WatchlistSecurity,
)

from app.data_source.longport_source import LongportSource


class LongportWatchlistSource:
    """封装 Longport 自选分组查询。"""

    def __init__(self, quote_ctx: QuoteContext | None = None) -> None:
        self._quote_ctx = quote_ctx or LongportSource().quote_ctx

    def fetch_groups(self) -> list[WatchlistGroup]:
        """获取全部分组列表。"""

        return self._quote_ctx.watchlist()

    def create_group(self, name: str, securities: list[str] | None = None) -> int:
        """创建自选分组并返回分组 ID。"""

        return self._quote_ctx.create_watchlist_group(name=name, securities=securities)

    def update_group(
        self,
        group_id: int,
        *,
        name: str | None = None,
        securities: list[str] | None = None,
        mode: type[SecuritiesUpdateMode] | str | None = None,
    ) -> WatchlistGroup:
        """更新自选分组。

        Args:
            group_id: 分组 ID
            name: 新分组名, 不修改则传 None
            securities: 证券代码列表
            mode: 变更模式, 可接受枚举或字符串(add/remove/replace)
        Returns:
            更新后的分组对象
        """

        mode_enum = self._normalize_mode(mode)
        self._quote_ctx.update_watchlist_group(
            group_id,
            name=name,
            securities=securities,
            mode=mode_enum,
        )

        updated = self.find_group(group_id)
        if updated is None:
            msg = f"未找到分组: {group_id}"
            raise ValueError(msg)
        return updated

    def find_group(self, group_id: int) -> WatchlistGroup | None:
        """按 ID 查找分组, 未找到返回 None。"""

        return next((group for group in self.fetch_groups() if group.id == group_id), None)

    @staticmethod
    def serialize_security(security: WatchlistSecurity) -> dict[str, object]:
        """将 SDK 返回的 WatchlistSecurity 序列化为可 JSON 化的 dict。"""

        watched_price = (
            float(security.watched_price) if security.watched_price is not None else None
        )
        watched_at = security.watched_at.isoformat() if security.watched_at else None
        market = getattr(security.market, "value", str(security.market))

        return {
            "symbol": security.symbol,
            "market": market,
            "name": security.name,
            "watched_price": watched_price,
            "watched_at": watched_at,
        }

    def serialize_group(self, group: WatchlistGroup) -> dict[str, object]:
        """将 WatchlistGroup 序列化为可直接返回的 dict。"""

        securities: Iterable[WatchlistSecurity] = getattr(group, "securities", []) or []
        return {
            "id": group.id,
            "name": group.name,
            "securities": [self.serialize_security(sec) for sec in securities],
        }

    @staticmethod
    def _normalize_mode(
        mode: type[SecuritiesUpdateMode] | str | None,
    ) -> type[SecuritiesUpdateMode] | None:
        if mode is None:
            return None
        if isinstance(mode, type) and issubclass(mode, SecuritiesUpdateMode):
            return mode

        mapping: dict[str, type[SecuritiesUpdateMode]] = {
            "add": SecuritiesUpdateMode.Add,
            "remove": SecuritiesUpdateMode.Remove,
            "replace": SecuritiesUpdateMode.Replace,
        }
        mode_enum = mapping.get(mode.lower())
        if mode_enum is None:
            msg = f"无效的 mode: {mode}, 仅支持 add/remove/replace"
            raise ValueError(msg)
        return mode_enum


__all__ = ["LongportWatchlistSource"]
