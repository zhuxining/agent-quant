"""Prompt 格式化工具函数。"""

from collections.abc import Iterable
from decimal import Decimal

SCALE = 6


def fmt_number(value: float | Decimal | None, *, suffix: str = "") -> str:
    """格式化数值, 固定保留 6 位小数."""
    if value is None:
        return "N/A" + suffix
    try:
        return f"{float(value):.{SCALE}f}{suffix}"
    except TypeError, ValueError:
        return f"{value}{suffix}"


def fmt_currency(value: float | Decimal | None) -> str:
    """格式化货币值。"""
    return f"${fmt_number(value)}" if value is not None else "$N/A"


def fmt_pct(value: float | Decimal | None) -> str:
    """格式化百分比值 (将小数转换为百分数)。"""
    if value is None:
        return fmt_number(value)
    try:
        return fmt_number(float(value) * 100, suffix="%")
    except TypeError, ValueError:
        return fmt_number(value, suffix="%")


def fmt_list(values: Iterable[float | Decimal] | None) -> str:
    """格式化数值列表为逗号分隔字符串。"""
    if not values:
        return ""
    return ", ".join(fmt_number(v) for v in values)


def fmt_series_number(values: Iterable[float | Decimal] | None) -> list[float | Decimal]:
    """格式化数值序列为保留 6 位小数的列表。"""
    if not values:
        return []

    formatted: list[float | Decimal] = []
    for value in values:
        try:
            formatted.append(round(float(value), SCALE))
        except TypeError, ValueError:
            formatted.append(value)  # 保留原值以避免丢失信息
    return formatted


__all__ = [
    "fmt_currency",
    "fmt_list",
    "fmt_number",
    "fmt_pct",
    "fmt_series_number",
]
