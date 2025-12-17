"""数据源加工模块。

提供账户持仓、技术指标等数据的获取和 Prompt 构建功能。
"""

from .account_position import build_account_prompt
from .technical_indicator import TechnicalIndicatorFeed, TechnicalSnapshot

__all__ = [
    "TechnicalIndicatorFeed",
    "TechnicalSnapshot",
    "build_account_prompt",
]
