"""Assemble multi-timeframe market data enriched with technical indicators."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

import pandas as pd
from longport.openapi import AdjustType, Period

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


class DataFeed:
	"""构建长线与短线两组行情数据，并附带核心指标。"""

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

	def build_long_term(
		self,
		symbol: str,
		count: int = DEFAULT_LONG_TERM_COUNT,
		adjust: Any = DEFAULT_ADJUST,
		end_date: datetime | None = None,
	) -> FeedSlice:
		"""单独构建长线（日线）行情切片。"""

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
		"""单独构建短线（小时线）行情切片。"""

		return self._build_slice(
			symbol=symbol,
			period=SHORT_TERM_PERIOD,
			count=count,
			adjust=adjust,
			end_date=end_date,
		)

	def build_prompt(
		self,
		symbol: str,
		long_term_count: int = DEFAULT_LONG_TERM_COUNT,
		short_term_count: int = DEFAULT_SHORT_TERM_COUNT,
		adjust: Any = DEFAULT_ADJUST,
		end_date: datetime | None = None,
	) -> str:
		"""构建用于 Agent Prompt 的行情摘要文本。"""

		slices = self.build(
			symbol=symbol,
			long_term_count=long_term_count,
			short_term_count=short_term_count,
			adjust=adjust,
			end_date=end_date,
		)
		return self._render_prompt(symbol, slices["short_term"], slices["long_term"])

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
		"""顺序计算中间价与各类指标，确保 DataFrame 持续扩展。"""

		enriched = self.indicator_calculator.compute_mid_price(frame)
		enriched = self.indicator_calculator.compute_change(enriched)
		enriched = self.indicator_calculator.compute_ema(enriched)
		enriched = self.indicator_calculator.compute_macd(enriched)
		enriched = self.indicator_calculator.compute_rsi(enriched)
		enriched = self.indicator_calculator.compute_atr(enriched)
		return enriched

	def _render_prompt(self, symbol: str, short_term: FeedSlice, long_term: FeedSlice) -> str:
		latest = short_term.latest
		volume_series = cast(pd.Series, long_term.frame["volume"])
		lines = [
			f"** {symbol} **",
			(
				'"current_price = '
				f"{self._format_number(latest['close'], 1)}, "
				f"current_ema20 = {self._format_number(latest.get('ema_20'))}, "
				f"current_macd = {self._format_number(latest.get('macd'))}, "
				f'current_rsi (7 period) = {self._format_number(latest.get("rsi_7"))}"'
			),
			"",
			"**short-term context (1-h timeframe):**",
			"",
			f"Mid prices: {self._format_series(short_term.frame['mid_price'])}",
			f"EMA indicators (20-period): {self._format_series(short_term.frame['ema_20'])}",
			f"MACD indicators: {self._format_series(short_term.frame['macd'])}",
			f"RSI indicators (7-Period): {self._format_series(short_term.frame['rsi_7'])}",
			f"RSI indicators (14-Period): {self._format_series(short_term.frame['rsi_14'])}",
			"",
			"**Longer-term context (1-day timeframe):**",
			"",
			(
				"20-Period EMA: "
				f"{self._format_number(long_term.latest.get('ema_20'))} vs. 50-Period EMA: "
				f"{self._format_number(long_term.latest.get('ema_50'))}"
			),
			(
				"3-Period ATR: "
				f"{self._format_number(long_term.latest.get('atr_3'))} vs. 14-Period ATR: "
				f"{self._format_number(long_term.latest.get('atr_14'))}"
			),
			(
				"Current Volume: "
				f"{self._format_number(long_term.latest.get('volume'))} vs. Average Volume: "
				f"{self._format_number(self._mean(volume_series))}"
			),
			f"MACD indicators: {self._format_series(long_term.frame['macd'])}",
			f"RSI indicators (14-Period): {self._format_series(long_term.frame['rsi_14'])}",
		]
		return "\n".join(lines)

	@staticmethod
	def _mean(series: pd.Series) -> float | None:
		clean = series.dropna()
		return float(clean.mean()) if not clean.empty else None

	@staticmethod
	def _format_series(
		series: pd.Series | Iterable[float],
		digits: int = 3,
		count: int = 10,
	) -> str:
		if isinstance(series, pd.Series):
			values = series.dropna().tail(count).tolist()
		else:
			values = list(series)
		if not values:
			return "[]"
		formatted = ", ".join(f"{value:.{digits}f}" for value in values)
		return f"[{formatted}]"

	@staticmethod
	def _format_number(value: Any, digits: int = 3) -> str:
		number = DataFeed._coerce_number(value)
		if number is None:
			return "N/A"
		return f"{number:.{digits}f}"

	@staticmethod
	def _coerce_number(value: Any) -> float | None:
		if value is None:
			return None
		if isinstance(value, pd.Series):
			if value.empty:
				return None
			value = value.iloc[-1]
		if not pd.api.types.is_scalar(value):
			return None
		if pd.isna(value):
			return None
		return float(value)


__all__ = [
	"DataFeed",
	"FeedSlice",
	"DEFAULT_LONG_TERM_COUNT",
	"DEFAULT_SHORT_TERM_COUNT",
	"LONG_TERM_PERIOD",
	"SHORT_TERM_PERIOD",
	"DEFAULT_ADJUST",
]
