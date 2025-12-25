"""数据类型转换工具函数."""

from typing import Any

import pandas as pd


def safe_float(value: Any) -> float | None:
    """安全地将值转换为浮点数.

    处理 None、NaN 等特殊情况,转换失败时返回 None.

    Args:
        value: 待转换的值

    Returns:
        转换后的浮点数,如果转换失败或值为 None/NaN 则返回 None
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except TypeError, ValueError:
        return None


def safe_int(value: Any) -> int | None:
    """安全地将值转换为整数.

    处理 None、NaN 等特殊情况,转换失败时返回 None.

    Args:
        value: 待转换的值

    Returns:
        转换后的整数,如果转换失败或值为 None/NaN 则返回 None
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return int(value)
    except TypeError, ValueError:
        return None


__all__ = ["safe_float", "safe_int"]
