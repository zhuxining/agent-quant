"""Assemble multi-timeframe market data enriched with technical indicators."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from app.data_source.longport_source import LongportSource, interval_to_period
from app.utils.converters import safe_float
from app.utils.talib_calculator import IndicatorCalculator


@dataclass(slots=True)
class TechnicalFeedSlice:
    """单一时间周期的行情快照,包含带技术指标的 OHLCV 数据。

    Attributes:
        symbol: 股票代码
        period: K 线周期
        frame: 包含 OHLCV 及技术指标的 DataFrame
    """

    symbol: str
    period: Any
    frame: pd.DataFrame

    @property
    def latest(self) -> pd.Series:
        """返回最新一行数据,便于快速查询当前指标值。"""

        if self.frame.empty:
            msg = f"{self.symbol} ({self.period.name}) 没有可用数据"
            raise ValueError(msg)
        return self.frame.iloc[-1]


@dataclass(slots=True)
class TechnicalSnapshot:
    """面向 Prompt/Workflow 的行情摘要。

    单周期的技术指标数据, 用于生成交易决策所需的市场视图.
    指标顺序: change_pct, EMA, ADX, MACD, RSI, ATR, BBANDS, AD, volume

    Attributes:
        symbol: 股票代码
        period: K 线周期 (如 "1d", "1h", "4h", "15m")
    """

    symbol: str
    period: str  # "1d", "1h", "4h", "15m" 等

    # ============ 价格指标 ============
    latest_price: float | None  # 最新收盘价
    change_pct_1: float | None
    change_pct_5: float | None

    # ============ 趋势指标: EMA ============
    ema5_series: list[float]  # EMA(5) 序列
    ema10_series: list[float]  # EMA(10) 序列
    ema20_series: list[float]  # EMA(20) 序列
    ema60_series: list[float]  # EMA(60) 序列

    # ============ 趋势强度指标: ADX ============
    adx14_series: list[float]  # ADX(14) 序列

    # ============ 动量指标: MACD ============
    macd_series: list[float]  # MACD 序列
    macd_signal_series: list[float]  # MACD Signal 序列
    macd_hist_series: list[float]  # MACD Histogram 序列

    # ============ 动量指标: RSI ============
    rsi7_latest: float | None  # RSI(7) 最新值
    rsi14_latest: float | None  # RSI(14) 最新值

    # ============ 波动指标: ATR ============
    atr3_latest: float | None  # ATR(3) 最新值
    atr14_latest: float | None  # ATR(14) 最新值

    # ============ 波动指标: BBANDS ============
    bbands_upper_latest: float | None  # 布林带上轨
    bbands_middle_latest: float | None  # 布林带中轨
    bbands_lower_latest: float | None  # 布林带下轨

    # ============ 成交量指标: AD ============
    ad_series: list[float]  # AD 序列

    # ============ 成交量指标 ============
    volume_latest: float | None  # 最新成交量
    volume_sma_5: float | None  # 5 周期成交量均线
    volume_sma_20: float | None  # 20 周期成交量均线


class TechnicalIndicatorFeed:
    """
    该类负责从数据源获取原始 K 线数据,计算技术指标,
    并生成适用于交易决策的多时间周期行情摘要。
    """

    def __init__(
        self,
        indicator_calculator: IndicatorCalculator | None = None,
        source: LongportSource | None = None,
    ) -> None:
        """初始化技术指标数据源。

        Args:
            indicator_calculator: 指标计算器,默认使用 IndicatorCalculator
            source: 行情数据源,默认使用 LongportSource
        """
        self.indicator_calculator = indicator_calculator or IndicatorCalculator
        self.source = source or LongportSource()

    def build_snapshot(
        self,
        symbol: str,
        period: str = "1d",
        count: int = 100,
        end_date: datetime | None = None,
    ) -> TechnicalSnapshot:
        """构建单个标的的单周期行情摘要.

        指定周期和数据点数量, 提取关键指标值, 生成结构化的行情快照.

        Args:
            symbol: 股票代码
            period: K 线周期, 如 "1d", "1h", "4h", "15m"
            count: K 线数量, 默认 100
            end_date: 结束日期, None 表示当前时间

        Returns:
            包含指标值和历史序列的摘要
        """
        period_obj = interval_to_period(period)
        slice_ = self._build_slice(
            symbol=symbol,
            period=period_obj,
            count=count,
            end_date=end_date,
        )
        return self._to_snapshot(symbol=symbol, period=period, slice_=slice_)

    def build_snapshots(
        self,
        symbols: Sequence[str],
        period: str = "1d",
        count: int = 100,
        end_date: datetime | None = None,
    ) -> list[TechnicalSnapshot]:
        """批量构建多个标的的单周期行情摘要。

        Args:
            symbols: 股票代码列表
            period: K 线周期, 如 "1d", "1h", "4h", "15m"
            count: K 线数量, 默认 100
            end_date: 结束日期, None 表示当前时间

        Returns:
            按输入顺序返回的摘要列表
        """
        return [
            self.build_snapshot(
                symbol=symbol,
                period=period,
                count=count,
                end_date=end_date,
            )
            for symbol in symbols
        ]

    def _build_slice(
        self,
        symbol: str,
        period: Any,
        count: int,
        end_date: datetime | None,
    ) -> TechnicalFeedSlice:
        """内部方法:构建单一周期的行情切片。

        获取原始 K 线数据并计算所有技术指标。
        """
        frame = self.source.get_candles_frame(
            symbol=symbol,
            interval=period,
            count=count,
            end_date=end_date,
        )
        enriched = self._apply_indicators(frame)
        return TechnicalFeedSlice(symbol=symbol, period=period, frame=enriched)

    def _apply_indicators(self, frame: pd.DataFrame) -> pd.DataFrame:
        """按分类顺序计算技术指标。

        顺序遵循逻辑链: 基础 → 趋势 → 强度 → 动量 → 波动 → 成交量 → 聚合
        """

        # 1. 基础指标
        enriched = self.indicator_calculator.compute_change(frame)
        enriched = self.indicator_calculator.compute_mid_price(enriched)

        # 2. 趋势方向指标
        enriched = self.indicator_calculator.compute_ema(enriched)
        enriched = self.indicator_calculator.compute_macd(enriched)

        # 3. 趋势强度指标
        enriched = self.indicator_calculator.compute_adx(enriched)

        # 4. 动量指标
        enriched = self.indicator_calculator.compute_cci(enriched)
        enriched = self.indicator_calculator.compute_rsi(enriched)
        enriched = self.indicator_calculator.compute_stoch(enriched)

        # 5. 波动指标
        enriched = self.indicator_calculator.compute_atr(enriched)
        enriched = self.indicator_calculator.compute_bbands(enriched)

        # 6. 成交量指标
        enriched = self.indicator_calculator.compute_obv(enriched)
        enriched = self.indicator_calculator.compute_ad(enriched)

        # 7. 聚合指标
        enriched = self.indicator_calculator.compute_volume_sma(enriched)

        return enriched

    @staticmethod
    def _series_tail(frame: pd.DataFrame, column: str, count: int = 10) -> list[float]:
        """提取指定列的最后 N 个有效值。

        自动跳过 NaN 值,返回浮点数列表。

        Args:
            frame: 数据帧
            column: 列名
            count: 提取数量,默认 10

        Returns:
            浮点数列表,如果列不存在则返回空列表
        """
        if column not in frame:
            return []
        series = frame[column]
        if hasattr(series, "dropna"):
            series = series.dropna()
        values = series.tail(count).tolist()
        return [float(v) for v in values if pd.notna(v)]

    def _to_snapshot(
        self,
        symbol: str,
        period: str,
        slice_: TechnicalFeedSlice,
    ) -> TechnicalSnapshot:
        """将单周期切片转换为结构化的行情摘要.

        提取当前值和历史序列, 组装成适合 Prompt 使用的数据结构.
        """
        latest = slice_.latest

        return TechnicalSnapshot(
            symbol=symbol,
            period=period,
            # 价格指标
            latest_price=safe_float(latest.get("close")),
            change_pct_1=safe_float(latest.get("change_pct_1")),
            change_pct_5=safe_float(latest.get("change_pct_5")),
            # 趋势指标: EMA
            ema5_series=self._series_tail(slice_.frame, "ema_5"),
            ema10_series=self._series_tail(slice_.frame, "ema_10"),
            ema20_series=self._series_tail(slice_.frame, "ema_20"),
            ema60_series=self._series_tail(slice_.frame, "ema_60"),
            # 趋势强度指标: ADX
            adx14_series=self._series_tail(slice_.frame, "adx_14"),
            # 动量指标: MACD
            macd_series=self._series_tail(slice_.frame, "macd"),
            macd_signal_series=self._series_tail(slice_.frame, "macd_signal"),
            macd_hist_series=self._series_tail(slice_.frame, "macd_hist"),
            # 动量指标: RSI
            rsi7_latest=safe_float(latest.get("rsi_7")),
            rsi14_latest=safe_float(latest.get("rsi_14")),
            # 波动指标: ATR
            atr3_latest=safe_float(latest.get("atr_3")),
            atr14_latest=safe_float(latest.get("atr_14")),
            # 波动指标: BBANDS
            bbands_upper_latest=safe_float(latest.get("bb_upper_5")),
            bbands_middle_latest=safe_float(latest.get("bb_middle_5")),
            bbands_lower_latest=safe_float(latest.get("bb_lower_5")),
            # 成交量指标: AD
            ad_series=self._series_tail(slice_.frame, "ad"),
            # 成交量指标
            volume_latest=safe_float(latest.get("volume")),
            volume_sma_5=safe_float(latest.get("volume_sma_5")),
            volume_sma_20=safe_float(latest.get("volume_sma_20")),
        )


__all__ = [
    "TechnicalFeedSlice",
    "TechnicalIndicatorFeed",
    "TechnicalSnapshot",
]
