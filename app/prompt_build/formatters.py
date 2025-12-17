"""Prompt 格式化工具函数。"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal


def fmt_number(value: float | Decimal | None, *, suffix: str = "") -> str:
    """格式化数值, 保留有效数字。"""
    if value is None:
        return "N/A" + suffix
    try:
        return f"{float(value):.6g}{suffix}"
    except (TypeError, ValueError):
        return f"{value}{suffix}"


def fmt_currency(value: float | Decimal | None) -> str:
    """格式化货币值。"""
    return f"${fmt_number(value)}"


def fmt_pct(value: float | Decimal | None) -> str:
    """格式化百分比值。"""
    return fmt_number(value, suffix="%")


def fmt_list(values: Iterable[float] | None) -> str:
    """格式化数值列表为逗号分隔字符串。"""
    if not values:
        return ""
    return ", ".join(fmt_number(v) for v in values)


__all__ = [
    "fmt_currency",
    "fmt_list",
    "fmt_number",
    "fmt_pct",
]
