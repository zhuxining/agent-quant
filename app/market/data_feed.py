"""Assemble multi-timeframe market data enriched with technical indicators."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from longport.openapi import AdjustType, Period
import pandas as pd

from .longport_source import LongportSource
from .talib_calculator import IndicatorCalculator

DEFAULT_LONG_TERM_COUNT = 200
DEFAULT_SHORT_TERM_COUNT = 240
LONG_TERM_PERIOD = Period.Day
SHORT_TERM_PERIOD = Period.Min_60
DEFAULT_ADJUST = AdjustType.ForwardAdjust


@dataclass(slots=True)
class FeedSlice:
    """Single timeframe snapshot containing the enriched OHLCV frame."""

    symbol: str
    period: Any
    frame: pd.DataFrame

    @property
    def latest(self) -> pd.Series:
        """Return the most recent row for quick lookup."""

        if self.frame.empty:
            msg = f"{self.symbol} ({self.period.name}) 没有可用数据"
            raise ValueError(msg)
        return self.frame.iloc[-1]


@dataclass(slots=True)
class MarketSnapshot:
    """面向 Prompt/Workflow 的行情摘要。"""

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


class DataFeed:
    """构建长线与短线两组行情数据,并附带核心指标。"""

    def __init__(
        self,
        indicator_calculator: IndicatorCalculator | None = None,
        source: LongportSource | None = None,
    ) -> None:
        self.indicator_calculator = indicator_calculator or IndicatorCalculator()
        self.source = source or LongportSource()

    def build(
        self,
        symbol: str,
        long_term_count: int = DEFAULT_LONG_TERM_COUNT,
        short_term_count: int = DEFAULT_SHORT_TERM_COUNT,
        adjust: Any = DEFAULT_ADJUST,
        end_date: datetime | None = None,
    ) -> dict[str, FeedSlice]:
        """Return both long-term and short-term slices enriched with indicators."""

        long_term_slice = self.build_long_term(
            symbol=symbol,
            count=long_term_count,
            adjust=adjust,
            end_date=end_date,
        )
        short_term_slice = self.build_short_term(
            symbol=symbol,
            count=short_term_count,
            adjust=adjust,
            end_date=end_date,
        )
        return {"long_term": long_term_slice, "short_term": short_term_slice}

    def build_snapshot(
        self,
        symbol: str,
        long_term_count: int = DEFAULT_LONG_TERM_COUNT,
        short_term_count: int = DEFAULT_SHORT_TERM_COUNT,
        adjust: Any = DEFAULT_ADJUST,
        end_date: datetime | None = None,
    ) -> MarketSnapshot:
        """构建单个标的的行情摘要。"""

        slices = self.build(
            symbol=symbol,
            long_term_count=long_term_count,
            short_term_count=short_term_count,
            adjust=adjust,
            end_date=end_date,
        )
        return self._to_snapshot(symbol, slices["short_term"], slices["long_term"])

    def build_snapshots(
        self,
        symbols: Sequence[str],
        long_term_count: int = DEFAULT_LONG_TERM_COUNT,
        short_term_count: int = DEFAULT_SHORT_TERM_COUNT,
        adjust: Any = DEFAULT_ADJUST,
        end_date: datetime | None = None,
    ) -> list[MarketSnapshot]:
        """批量构建多个标的的行情摘要。"""

        snapshots: list[MarketSnapshot] = []
        for symbol in symbols:
            snapshots.append(
                self.build_snapshot(
                    symbol=symbol,
                    long_term_count=long_term_count,
                    short_term_count=short_term_count,
                    adjust=adjust,
                    end_date=end_date,
                )
            )
        return snapshots

    def build_long_term(
        self,
        symbol: str,
        count: int = DEFAULT_LONG_TERM_COUNT,
        adjust: Any = DEFAULT_ADJUST,
        end_date: datetime | None = None,
    ) -> FeedSlice:
        """单独构建长线(日线)行情切片。"""

        return self._build_slice(
            symbol=symbol,
            period=LONG_TERM_PERIOD,
            count=count,
            adjust=adjust,
            end_date=end_date,
        )

    def build_short_term(
        self,
        symbol: str,
        count: int = DEFAULT_SHORT_TERM_COUNT,
        adjust: Any = DEFAULT_ADJUST,
        end_date: datetime | None = None,
    ) -> FeedSlice:
        """单独构建短线(小时线)行情切片。"""

        return self._build_slice(
            symbol=symbol,
            period=SHORT_TERM_PERIOD,
            count=count,
            adjust=adjust,
            end_date=end_date,
        )

    def get_latest_price(
        self,
        symbol: str,
        *,
        adjust: Any = DEFAULT_ADJUST,
        end_date: datetime | None = None,
    ) -> Decimal | None:
        """Return the most recent close price from short-term data."""

        slice_ = self.build_short_term(
            symbol=symbol,
            count=1,
            adjust=adjust,
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
        adjust: Any,
        end_date: datetime | None,
    ) -> FeedSlice:
        frame = self.source.get_candles_frame(
            symbol=symbol,
            interval=period,
            count=count,
            adjust=adjust,
            end_date=end_date,
        )
        enriched = self._apply_indicators(frame)
        return FeedSlice(symbol=symbol, period=period, frame=enriched)

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
        if column not in frame:
            return []
        series = frame[column]
        if hasattr(series, "dropna"):
            series = series.dropna()
        values = series.tail(count).tolist()
        return [float(v) for v in values if pd.notna(v)]

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        try:
            return float(value)
        except TypeError, ValueError:
            return None

    def _to_snapshot(
        self, symbol: str, short_term: FeedSlice, long_term: FeedSlice
    ) -> MarketSnapshot:
        latest_short = short_term.latest
        latest_long = long_term.latest
        volume_series = long_term.frame.get("volume")
        volume_avg = None
        if volume_series is not None and hasattr(volume_series, "dropna"):
            clean = volume_series.dropna()
            if not clean.empty:
                volume_avg = float(clean.mean())
        return MarketSnapshot(
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
    "DEFAULT_ADJUST",
    "DEFAULT_LONG_TERM_COUNT",
    "DEFAULT_SHORT_TERM_COUNT",
    "LONG_TERM_PERIOD",
    "SHORT_TERM_PERIOD",
    "DataFeed",
    "FeedSlice",
    "MarketSnapshot",
]
