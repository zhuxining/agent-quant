"""Prompt 格式化工具函数."""

from collections.abc import Iterable
from decimal import Decimal

SCALE = 4


def fmt_number(value: float | Decimal | None) -> str:
    """格式化数值, 固定保留 n 位小数."""
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{SCALE}f}"
    except TypeError, ValueError:
        return str(value)


def fmt_pct(value: float | Decimal | None) -> str:
    """格式化百分比值 (将小数转换为百分数)。"""
    if value is None:
        return "N/A"
    return f"{fmt_number(float(value) * 100)}%"


def fmt_list(values: Iterable[float | Decimal] | None) -> str:
    """格式化数值列表为逗号分隔字符串。"""
    if not values:
        return ""
    return ", ".join(fmt_number(v) for v in values)


def fmt_currency(value: float | Decimal | None) -> str:
    """格式化货币值。"""
    return f"¥{fmt_number(value)}" if value is not None else "N/A"


def round_numeric(value: float | Decimal | None) -> float | Decimal | None:
    """格式化单个数值为保留 n 位小数的数字 (用于 JSON)。"""
    if value is None:
        return None
    try:
        return round(float(value), SCALE)
    except TypeError, ValueError:
        return value


def round_numeric_series(values: Iterable[float | Decimal] | None) -> list[float | Decimal | None]:
    """格式化数值序列为保留 n 位小数的数字列表 (用于 JSON)。"""
    if not values:
        return []
    return [round_numeric(v) for v in values]


__all__ = [
    "fmt_list",
    "fmt_number",
    "fmt_pct",
    "round_numeric",
    "round_numeric_series",
]
