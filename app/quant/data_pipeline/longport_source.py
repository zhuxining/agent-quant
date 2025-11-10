"""Longport data source helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from longport.openapi import AdjustType, Config, Period, QuoteContext


class LongportSource:
	"""封装的 Longport 行情数据源。"""

	def __init__(self) -> None:
		self._config = Config.from_env()
		self._quote_ctx = QuoteContext(self._config)

	@property
	def quote_ctx(self) -> QuoteContext:
		return self._quote_ctx

	def _fetch_raw_candles(
		self,
		symbol: str,
		period: Any,
		count: int,
		adjust: Any,
		end_date: datetime | None,
	):
		if end_date is not None:
			candles = self._quote_ctx.history_candlesticks_by_offset(
				symbol,
				period,
				adjust,
				False,
				count,
				end_date,
			)
		else:
			candles = self._quote_ctx.candlesticks(symbol, period, count, adjust)

		if not candles:
			raise ValueError(f"未获取到 {symbol} 的K线数据")
		return candles

	def get_candles_frame(
		self,
		symbol: str,
		interval: str | Period = "1d",
		end_date: datetime | None = None,
		count: int = 120,
		adjust: Any = AdjustType.ForwardAdjust,
	) -> pd.DataFrame:
		"""返回按时间排序的 K 线 DataFrame，interval 支持字符串如 1m/1h/1d。"""

		period = interval_to_period(interval)
		candles_raw = self._fetch_raw_candles(symbol, period, count, adjust, end_date)

		frames = [
			{
				"symbol": symbol,
				"timestamp": candle.timestamp,
				"open": float(candle.open),
				"high": float(candle.high),
				"low": float(candle.low),
				"close": float(candle.close),
				"volume": float(candle.volume),
			}
			for candle in candles_raw
		]
		frame = pd.DataFrame(frames)
		frame["datetime"] = pd.to_datetime(frame["timestamp"], unit="s")
		frame.sort_values("datetime", inplace=True)
		frame.reset_index(drop=True, inplace=True)
		return frame


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


__all__ = ["LongportSource"]
