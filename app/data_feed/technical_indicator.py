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

DEFAULT_DAILY_TERM_COUNT = 200
DEFAULT_HOURLY_TERM_COUNT = 240
DAILY_TERM_PERIOD = Period.Day
HOURLY_TERM_PERIOD = Period.Min_60


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

    整合了小时线和日线的技术指标数据,用于生成交易决策所需的完整市场视图。

    命名规则:
    - hourly_*_series: 小时线指标序列(最近 10 个)
    - hourly_*_latest: 小时线指标当前值
    - daily_*_series: 日线指标序列(最近 10 个)
    - daily_*_latest: 日线指标当前值

    Attributes:
        symbol: 股票代码
        hourly_mid_prices_series: 小时线中间价序列
        hourly_ema20_series: 小时线 EMA20 序列
        hourly_macd_series: 小时线 MACD 序列
        hourly_macd_hist_series: 小时线 MACD 柱状图序列
        hourly_rsi7_series: 小时线 RSI7 序列
        hourly_rsi14_series: 小时线 RSI14 序列
        daily_current_price: 日线当前价格
        daily_mid_prices: 日线中间价
        daily_change_pct_1: 日线 1 日涨幅
        daily_change_pct_5: 日线 5 日涨幅
        daily_ema5_latest: 日线 EMA5 当前值
        daily_ema10_latest: 日线 EMA10 当前值
        daily_ema20_latest: 日线 EMA20 当前值
        daily_ema60_latest: 日线 EMA60 当前值
        daily_macd_series: 日线 MACD 序列
        daily_macd_hist_series: 日线 MACD 柱状图序列
        daily_adx_series: 日线 ADX 序列
        daily_cci_series: 日线 CCI 序列
        daily_rsi7_latest: 日线 RSI7 当前值
        daily_rsi14_latest: 日线 RSI14 当前值
        daily_stoch_k_latest: 日线 Stoch K 当前值
        daily_stoch_d_latest: 日线 Stoch D 当前值
        daily_atr3_latest: 日线 ATR3 当前值
        daily_atr14_latest: 日线 ATR14 当前值
        daily_obv_latest: 日线 OBV 当前值
        daily_ad_latest: 日线 A/D 当前值
        daily_volume_latest: 日线最新成交量
        daily_volume_sma_5: 日线 5 日均成交量
        daily_volume_sma_10: 日线 10 日均成交量
        daily_volume_sma_20: 日线 20 日均成交量

    """

    symbol: str
    hourly_mid_prices_series: list[float]
    hourly_ema20_series: list[float]
    hourly_macd_series: list[float]
    hourly_macd_hist_series: list[float]
    hourly_rsi7_series: list[float]
    hourly_rsi14_series: list[float]

    daily_ema20_latest: float | None
    daily_ema60_latest: float | None
    daily_atr3_latest: float | None
    daily_atr14_latest: float | None
    daily_volume_latest: float | None
    daily_volume_sma_5: float | None

    daily_volume_sma_20: float | None
    daily_macd_series: list[float]
    daily_macd_hist_series: list[float]
    daily_rsi14_series: list[float]
    daily_rsi14_latest: float | None
    daily_change_pct_1: float | None
    daily_change_pct_5: float | None
    daily_stoch_k_latest: float | None
    daily_stoch_d_latest: float | None
    daily_obv_latest: float | None
    daily_ad_latest: float | None


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
        daily_term_count: int = DEFAULT_DAILY_TERM_COUNT,
        hourly_term_count: int = DEFAULT_HOURLY_TERM_COUNT,
        end_date: datetime | None = None,
    ) -> dict[str, TechnicalFeedSlice]:
        """构建包含长期和短期两个时间周期的行情切片,附带完整技术指标。

        Args:
            symbol: 股票代码
            daily_term_count: 长期数据的 K 线数量
            hourly_term_count: 短期数据的 K 线数量
            end_date: 结束日期,None 表示使用当前时间

        Returns:
            包含 'daily_term' 和 'hourly_term' 两个键的字典
        """

        daily_term_slice = self.build_daily_term(
            symbol=symbol,
            count=daily_term_count,
            end_date=end_date,
        )
        hourly_term_slice = self.build_hourly_term(
            symbol=symbol,
            count=hourly_term_count,
            end_date=end_date,
        )
        return {"daily_term": daily_term_slice, "hourly_term": hourly_term_slice}

    def build_snapshot(
        self,
        symbol: str,
        daily_term_count: int = DEFAULT_DAILY_TERM_COUNT,
        hourly_term_count: int = DEFAULT_HOURLY_TERM_COUNT,
        end_date: datetime | None = None,
    ) -> TechnicalSnapshot:
        """构建单个标的的行情摘要。

        整合长短期数据,提取关键指标值,生成结构化的行情快照。

        Returns:
            包含当前价格、技术指标及历史序列的完整摘要
        """

        slices = self.build(
            symbol=symbol,
            daily_term_count=daily_term_count,
            hourly_term_count=hourly_term_count,
            end_date=end_date,
        )
        realtime_data = self.source.get_realtime_quote(symbol)
        return self._to_snapshot(symbol, realtime_data, slices["hourly_term"], slices["daily_term"])

    def build_snapshots(
        self,
        symbols: Sequence[str],
        daily_term_count: int = DEFAULT_DAILY_TERM_COUNT,
        hourly_term_count: int = DEFAULT_HOURLY_TERM_COUNT,
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
                daily_term_count=daily_term_count,
                hourly_term_count=hourly_term_count,
                end_date=end_date,
            )
            for symbol in symbols
        ]

    def build_daily_term(
        self,
        symbol: str,
        count: int = DEFAULT_DAILY_TERM_COUNT,
        end_date: datetime | None = None,
    ) -> TechnicalFeedSlice:
        """单独构建长线(日线)行情切片。"""

        return self._build_slice(
            symbol=symbol,
            period=DAILY_TERM_PERIOD,
            count=count,
            end_date=end_date,
        )

    def build_hourly_term(
        self,
        symbol: str,
        count: int = DEFAULT_HOURLY_TERM_COUNT,
        end_date: datetime | None = None,
    ) -> TechnicalFeedSlice:
        """单独构建短线(小时线)行情切片。"""

        return self._build_slice(
            symbol=symbol,
            period=HOURLY_TERM_PERIOD,
            count=count,
            end_date=end_date,
        )

    def get_latest_price(
        self,
        symbol: str,
        *,
        end_date: datetime | None = None,
    ) -> Decimal | None:
        """获取最新K线收盘价。

        从小时线最后一条数据获取收盘价,支持历史回测。

        Args:
            symbol: 股票代码
            end_date: 结束日期,用于回测历史数据

        Returns:
            收盘价的 Decimal 值,如果无数据则返回 None
        """
        slice_ = self.build_hourly_term(
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

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        """安全地将值转换为浮点数。

        处理 None、NaN 等特殊情况,转换失败时返回 None。
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        try:
            return float(value)
        except TypeError, ValueError:
            return None

    def _to_snapshot(
        self,
        symbol: str,
        realtime_data: dict[str, Any],
        hourly_term: TechnicalFeedSlice,
        daily_term: TechnicalFeedSlice,
    ) -> TechnicalSnapshot:
        """将长短期切片转换为结构化的行情摘要。

        提取当前值和历史序列,组装成适合 Prompt 使用的数据结构。
        """
        latest_long = daily_term.latest

        # 组装摘要数据结构
        return TechnicalSnapshot(
            symbol=symbol,
            hourly_mid_prices_series=self._series_tail(hourly_term.frame, "mid_price"),
            hourly_ema20_series=self._series_tail(hourly_term.frame, "ema_20"),
            hourly_macd_series=self._series_tail(hourly_term.frame, "macd"),
            hourly_macd_hist_series=self._series_tail(hourly_term.frame, "macd_hist"),
            hourly_rsi7_series=self._series_tail(hourly_term.frame, "rsi_7"),
            hourly_rsi14_series=self._series_tail(hourly_term.frame, "rsi_14"),
            daily_ema20_latest=self._safe_float(latest_long.get("ema_20")),
            daily_ema60_latest=self._safe_float(latest_long.get("ema_60")),
            daily_atr3_latest=self._safe_float(latest_long.get("atr_3")),
            daily_atr14_latest=self._safe_float(latest_long.get("atr_14")),
            daily_volume_latest=self._safe_float(latest_long.get("volume")),
            daily_volume_sma_5=self._safe_float(latest_long.get("volume_sma_5")),
            daily_volume_sma_20=self._safe_float(latest_long.get("volume_sma_20")),
            daily_macd_series=self._series_tail(daily_term.frame, "macd"),
            daily_macd_hist_series=self._series_tail(daily_term.frame, "macd_hist"),
            daily_rsi14_series=self._series_tail(daily_term.frame, "rsi_14"),
            daily_rsi14_latest=self._safe_float(latest_long.get("rsi_14")),
            daily_change_pct_1=self._safe_float(latest_long.get("change_pct_1")),
            daily_change_pct_5=self._safe_float(latest_long.get("change_pct_5")),
            daily_stoch_k_latest=self._safe_float(latest_long.get("stoch_k_14")),
            daily_stoch_d_latest=self._safe_float(latest_long.get("stoch_d_14")),
            daily_obv_latest=self._safe_float(latest_long.get("obv")),
            daily_ad_latest=self._safe_float(latest_long.get("ad")),
        )


__all__ = [
    "DAILY_TERM_PERIOD",
    "DEFAULT_DAILY_TERM_COUNT",
    "DEFAULT_HOURLY_TERM_COUNT",
    "HOURLY_TERM_PERIOD",
    "TechnicalFeedSlice",
    "TechnicalIndicatorFeed",
    "TechnicalSnapshot",
]
