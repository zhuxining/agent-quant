"""数据源适配模块。

统一对接外部行情源, 如 Longport。
"""

from .longport_source import LongportSource, interval_to_period

__all__ = [
    "LongportSource",
    "interval_to_period",
]
