"""净值追踪与计算。"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

import pandas as pd


@dataclass(slots=True)
class EquityPoint:
    """单日净值快照。"""

    date: date
    equity: Decimal
    cash: Decimal
    market_value: Decimal
    daily_return: float | None = None


@dataclass
class EquityCurve:
    """净值曲线, 用于记录和分析回测期间的资产变化。"""

    points: list[EquityPoint] = field(default_factory=list)

    def add(self, point: EquityPoint) -> None:
        """添加净值点并自动计算日收益率。"""
        if self.points:
            prev_equity = self.points[-1].equity
            if prev_equity > 0:
                daily_ret = float((point.equity - prev_equity) / prev_equity * 100)
                point.daily_return = daily_ret
        self.points.append(point)

    def to_dataframe(self) -> pd.DataFrame:
        """转换为 DataFrame 便于分析。"""
        if not self.points:
            return pd.DataFrame()
        return pd.DataFrame([
            {
                "date": p.date,
                "equity": float(p.equity),
                "cash": float(p.cash),
                "market_value": float(p.market_value),
                "daily_return": p.daily_return,
            }
            for p in self.points
        ])

    def to_returns_series(self) -> pd.Series:
        """生成收益率序列, 用于 quantstats 分析。"""
        df = self.to_dataframe()
        if df.empty:
            return pd.Series(dtype=float)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        # 计算简单收益率
        returns = df["equity"].pct_change().dropna()
        return returns

    @property
    def total_return(self) -> float | None:
        """计算总收益率 (%)。"""
        if len(self.points) < 2:
            return None
        initial = self.points[0].equity
        final = self.points[-1].equity
        if initial <= 0:
            return None
        return float((final - initial) / initial * 100)

    @property
    def final_equity(self) -> Decimal | None:
        """最终净值。"""
        if not self.points:
            return None
        return self.points[-1].equity


__all__ = [
    "EquityCurve",
    "EquityPoint",
]
