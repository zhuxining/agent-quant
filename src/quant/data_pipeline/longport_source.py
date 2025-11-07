"""Longport-backed market data source implementations."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Any

from longport.openapi import AdjustType, Config, Period, QuoteContext

from src.quant.core.interfaces import MarketDataSource
from src.quant.core.types import MarketBar


class LongportMarketDataSource(MarketDataSource):
	"""Fetch OHLCV bars using the Longport OpenAPI."""

	def __init__(
		self,
		config: Config | None = None,
		*,
		quote_context: QuoteContext | None = None,
	) -> None:
		self._config = config or Config.from_env()
		self._quote_ctx = quote_context or QuoteContext(self._config)

	def fetch_ohlcv(
		self,
		symbol: str,
		count: int = 100,
		*,
		interval: str = "1d",
	) -> Sequence[MarketBar]:
		"""Fetch OHLCV bars by mapping interval strings to Longport periods."""
		period = interval_to_period(interval)
		return self.fetch_by_period(symbol, period=period, count=count)

	def fetch_by_period(
		self,
		symbol: str,
		*,
		period: Any,
		count: int,
		adjust: Any = AdjustType.ForwardAdjust,
		end_time: datetime | None = None,
	) -> Sequence[MarketBar]:
		"""Fetch OHLCV bars for the requested period and length."""
		if end_time is not None:
			candles = self._quote_ctx.history_candlesticks_by_offset(
				symbol,
				period,
				adjust,
				False,
				count,
				end_time,
			)
		else:
			candles = self._quote_ctx.candlesticks(symbol, period, count, adjust)

		if not candles:
			msg = f"未获取到 {symbol} 的K线数据"
			raise ValueError(msg)

		return tuple(_normalize_candles(symbol, candles))


def _normalize_candles(symbol: str, candles: Iterable) -> Iterable[MarketBar]:
	"""Convert Longport candlestick objects to MarketBar dataclasses."""
	for candle in candles:
		yield MarketBar(
			symbol=symbol,
			timestamp=_coerce_timestamp(candle.timestamp),
			open=float(candle.open),
			high=float(candle.high),
			low=float(candle.low),
			close=float(candle.close),
			volume=float(candle.volume),
		)


def _coerce_timestamp(timestamp: int | float | datetime) -> datetime:
	"""Normalize timestamps returned by the SDK to aware datetimes."""
	if isinstance(timestamp, datetime):
		return timestamp
	return datetime.fromtimestamp(float(timestamp))


def interval_to_period(interval: str | Period) -> Period:
	"""Map interval strings to Period enums."""
	if isinstance(interval, Period):
		return interval
	normalized = interval.lower()
	mapping = {
		"1m": Period.Min_1,
		"5m": Period.Min_5,
		"15m": Period.Min_15,
		"30m": Period.Min_30,
		"1h": Period.Min_60,
		"4h": Period.Min_240,
		"1d": Period.Day,
		"1w": Period.Week,
		"1mo": Period.Month,
	}
	return mapping.get(normalized, Period.Day)
