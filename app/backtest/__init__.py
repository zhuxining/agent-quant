"""回测模块: 基于历史数据验证交易策略。"""

from .engine import BacktestConfig, BacktestEngine, BacktestResult
from .equity import EquityCurve, EquityPoint
from .report import BacktestReporter
from .vectorized_technical import VectorizedBacktestEngine

__all__ = [
    "BacktestConfig",
    "BacktestEngine",
    "BacktestReporter",
    "BacktestResult",
    "EquityCurve",
    "EquityPoint",
    "VectorizedBacktestEngine",
]
