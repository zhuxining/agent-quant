"""Assemble multi-timeframe market data enriched with technical indicators."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from longport.openapi import Period
import pandas as pd

from app.data_source.longport_source import LongportSource
from app.utils.talib_calculator import IndicatorCalculator

DEFAULT_LONG_TERM_COUNT = 200
DEFAULT_SHORT_TERM_COUNT = 240
LONG_TERM_PERIOD = Period.Day
SHORT_TERM_PERIOD = Period.Min_60


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

    整合了短期和长期的技术指标数据,用于生成交易决策所需的完整市场视图。

    Attributes:
        symbol: 股票代码
        current_price: 当前价格(短期最新收盘价)
        current_ema20: 当前 20 周期 EMA(短期)
        current_macd: 当前 MACD 值(短期)
        current_rsi7: 当前 7 周期 RSI(短期)
        short_term_mid_prices: 短期中间价序列(最近 10 个)
        short_term_ema20: 短期 EMA20 序列(最近 10 个)
        short_term_macd: 短期 MACD 序列(最近 10 个)
        short_term_rsi7: 短期 RSI7 序列(最近 10 个)
        short_term_rsi14: 短期 RSI14 序列(最近 10 个)
        long_term_ema20: 长期 EMA20 当前值
        long_term_ema50: 长期 EMA50 当前值
        long_term_atr3: 长期 ATR3 当前值(短期波动)
        long_term_atr14: 长期 ATR14 当前值(标准波动)
        long_term_volume_current: 长期最新成交量
        long_term_volume_avg: 长期平均成交量
        long_term_macd: 长期 MACD 序列(最近 10 个)
        long_term_rsi14: 长期 RSI14 序列(最近 10 个)
    """

    symbol: str
    current_price: float | None
    current_ema20: float | None
    current_macd: float | None
    current_rsi7: float | None
    short_term_mid_prices: list[float]
    short_term_ema20: list[float]
    short_term_macd: list[float]
    short_term_rsi7: list[float]
    short_term_rsi14: list[float]
    long_term_ema20: float | None
    long_term_ema50: float | None
    long_term_atr3: float | None
    long_term_atr14: float | None
    long_term_volume_current: float | None
    long_term_volume_avg: float | None
    long_term_macd: list[float]
    long_term_rsi14: list[float]


class TechnicalIndicatorFeed:
    """构建长线与短线两组行情数据,并附带核心技术指标。

    该类负责从数据源获取原始 K 线数据,计算技术指标,
    并生成适用于交易决策的多时间周期行情摘要。

    默认配置:
        - 长期数据:日线,200 根 K 线
        - 短期数据:60 分钟线,240 根 K 线
        - 复权方式:前复权
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

    def build(
        self,
        symbol: str,
        long_term_count: int = DEFAULT_LONG_TERM_COUNT,
        short_term_count: int = DEFAULT_SHORT_TERM_COUNT,
        end_date: datetime | None = None,
    ) -> dict[str, TechnicalFeedSlice]:
        """构建包含长期和短期两个时间周期的行情切片,附带完整技术指标。

        Args:
            symbol: 股票代码
            long_term_count: 长期数据的 K 线数量
            short_term_count: 短期数据的 K 线数量
            end_date: 结束日期,None 表示使用当前时间

        Returns:
            包含 'long_term' 和 'short_term' 两个键的字典
        """

        long_term_slice = self.build_long_term(
            symbol=symbol,
            count=long_term_count,
            end_date=end_date,
        )
        short_term_slice = self.build_short_term(
            symbol=symbol,
            count=short_term_count,
            end_date=end_date,
        )
        return {"long_term": long_term_slice, "short_term": short_term_slice}

    def build_snapshot(
        self,
        symbol: str,
        long_term_count: int = DEFAULT_LONG_TERM_COUNT,
        short_term_count: int = DEFAULT_SHORT_TERM_COUNT,
        end_date: datetime | None = None,
    ) -> TechnicalSnapshot:
        """构建单个标的的行情摘要。

        整合长短期数据,提取关键指标值,生成结构化的行情快照。

        Returns:
            包含当前价格、技术指标及历史序列的完整摘要
        """

        slices = self.build(
            symbol=symbol,
            long_term_count=long_term_count,
            short_term_count=short_term_count,
            end_date=end_date,
        )
        return self._to_snapshot(symbol, slices["short_term"], slices["long_term"])

    def build_snapshots(
        self,
        symbols: Sequence[str],
        long_term_count: int = DEFAULT_LONG_TERM_COUNT,
        short_term_count: int = DEFAULT_SHORT_TERM_COUNT,
        end_date: datetime | None = None,
    ) -> list[TechnicalSnapshot]:
        """批量构建多个标的的行情摘要。

        Args:
            symbols: 股票代码列表

        Returns:
            按输入顺序返回的摘要列表
        """
        return [
            self.build_snapshot(
                symbol=symbol,
                long_term_count=long_term_count,
                short_term_count=short_term_count,
                end_date=end_date,
            )
            for symbol in symbols
        ]

    def build_long_term(
        self,
        symbol: str,
        count: int = DEFAULT_LONG_TERM_COUNT,
        end_date: datetime | None = None,
    ) -> TechnicalFeedSlice:
        """单独构建长线(日线)行情切片。"""

        return self._build_slice(
            symbol=symbol,
            period=LONG_TERM_PERIOD,
            count=count,
            end_date=end_date,
        )

    def build_short_term(
        self,
        symbol: str,
        count: int = DEFAULT_SHORT_TERM_COUNT,
        end_date: datetime | None = None,
    ) -> TechnicalFeedSlice:
        """单独构建短线(小时线)行情切片。"""

        return self._build_slice(
            symbol=symbol,
            period=SHORT_TERM_PERIOD,
            count=count,
            end_date=end_date,
        )

    def get_latest_price(
        self,
        symbol: str,
        *,
        end_date: datetime | None = None,
    ) -> Decimal | None:
        """获取最新收盘价。

        从短期数据中提取最近一根 K 线的收盘价,用于快速查询当前价格。

        Returns:
            收盘价的 Decimal 值,如果无数据则返回 None
        """

        slice_ = self.build_short_term(
            symbol=symbol,
            count=1,
            end_date=end_date,
        )
        if slice_.frame.empty:
            return None
        latest_close = slice_.latest.get("close")
        if latest_close is None:
            return None
        return Decimal(str(latest_close))

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
        """顺序计算中间价与各类指标,确保 DataFrame 持续扩展。"""

        enriched = self.indicator_calculator.compute_mid_price(frame)
        enriched = self.indicator_calculator.compute_change(enriched)
        enriched = self.indicator_calculator.compute_ema(enriched)
        enriched = self.indicator_calculator.compute_macd(enriched)
        enriched = self.indicator_calculator.compute_rsi(enriched)
        enriched = self.indicator_calculator.compute_atr(enriched)
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

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        """安全地将值转换为浮点数。

        处理 None、NaN 等特殊情况,转换失败时返回 None。
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _to_snapshot(
        self, symbol: str, short_term: TechnicalFeedSlice, long_term: TechnicalFeedSlice
    ) -> TechnicalSnapshot:
        """将长短期切片转换为结构化的行情摘要。

        提取当前值和历史序列,组装成适合 Prompt 使用的数据结构。
        """
        latest_short = short_term.latest
        latest_long = long_term.latest
        # 计算长期平均成交量

        volume_series = long_term.frame.get("volume")
        volume_avg = None
        if volume_series is not None and hasattr(volume_series, "dropna"):
            clean = volume_series.dropna()
            if not clean.empty:
                volume_avg = float(clean.mean())

        # 组装摘要数据结构
        return TechnicalSnapshot(
            symbol=symbol,
            current_price=self._safe_float(latest_short.get("close")),
            current_ema20=self._safe_float(latest_short.get("ema_20")),
            current_macd=self._safe_float(latest_short.get("macd")),
            current_rsi7=self._safe_float(latest_short.get("rsi_7")),
            short_term_mid_prices=self._series_tail(short_term.frame, "mid_price"),
            short_term_ema20=self._series_tail(short_term.frame, "ema_20"),
            short_term_macd=self._series_tail(short_term.frame, "macd"),
            short_term_rsi7=self._series_tail(short_term.frame, "rsi_7"),
            short_term_rsi14=self._series_tail(short_term.frame, "rsi_14"),
            long_term_ema20=self._safe_float(latest_long.get("ema_20")),
            long_term_ema50=self._safe_float(latest_long.get("ema_50")),
            long_term_atr3=self._safe_float(latest_long.get("atr_3")),
            long_term_atr14=self._safe_float(latest_long.get("atr_14")),
            long_term_volume_current=self._safe_float(latest_long.get("volume")),
            long_term_volume_avg=volume_avg,
            long_term_macd=self._series_tail(long_term.frame, "macd"),
            long_term_rsi14=self._series_tail(long_term.frame, "rsi_14"),
        )


__all__ = [
    "DEFAULT_LONG_TERM_COUNT",
    "DEFAULT_SHORT_TERM_COUNT",
    "LONG_TERM_PERIOD",
    "SHORT_TERM_PERIOD",
    "TechnicalFeedSlice",
    "TechnicalIndicatorFeed",
    "TechnicalSnapshot",
]
