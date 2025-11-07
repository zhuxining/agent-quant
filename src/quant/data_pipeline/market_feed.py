"""Market data services built on top of configured data sources."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from datetime import datetime
from typing import Any

from longport.openapi import AdjustType, Period

from src.quant.core.interfaces import MarketDataSource
from src.quant.core.types import MarketBar

from .indicators import IndicatorService
from .longport_source import interval_to_period
from .snapshots import SnapshotAssembler

DEFAULT_SHORT_TERM_PERIOD = Period.Day
DEFAULT_LONG_TERM_PERIOD = Period.Week
DEFAULT_ADJUST = AdjustType.ForwardAdjust


class MarketDataService:
	"""Orchestrates market data retrieval."""

	def __init__(self, data_source: MarketDataSource) -> None:
		self._data_source = data_source

	def fetch_window(
		self,
		symbol: str,
		start: datetime,
		end: datetime,
		*,
		interval: str = "1m",
	) -> Sequence[MarketBar]:
		"""Fetch a list of OHLCV bars for the requested window."""
		return self._data_source.fetch_ohlcv(symbol, start, end, interval=interval)

	def fetch_period(
		self,
		symbol: str,
		*,
		period: Any,
		count: int,
		adjust: Any = DEFAULT_ADJUST,
		end_time: datetime | None = None,
	) -> Sequence[MarketBar]:
		"""Fetch OHLCV bars for a given period when the data source supports it."""
		fetcher = getattr(self._data_source, "fetch_by_period", None)
		if fetcher is None:
			msg = "数据源不支持按周期拉取数据"
			raise NotImplementedError(msg)
		normalized_period = interval_to_period(period)
		return fetcher(
			symbol,
			period=normalized_period,
			count=count,
			adjust=adjust,
			end_time=end_time,
		)


class PromptSnapshotService:
	"""High-level orchestrator producing prompt-ready snapshots."""

	def __init__(
		self,
		market_data: MarketDataService,
		indicator_service: IndicatorService,
		assembler: SnapshotAssembler,
	) -> None:
		self._market_data = market_data
		self._indicator_service = indicator_service
		self._assembler = assembler

	def build_snapshot(
		self,
		symbol: str,
		*,
		short_term_params: Mapping[str, Any] | None = None,
		long_term_params: Mapping[str, Any] | None = None,
		short_term_len: int = 10,
		long_term_len: int = 15,
		end_time: datetime | None = None,
	) -> dict[str, Any]:
		"""Load multi-period data and assemble a prompt snapshot."""
		short_cfg = _merge_period_options(
			{
				"period": DEFAULT_SHORT_TERM_PERIOD,
				"count": 120,
				"adjust": DEFAULT_ADJUST,
			},
			short_term_params,
		)
		long_cfg = _merge_period_options(
			{
				"period": DEFAULT_LONG_TERM_PERIOD,
				"count": 120,
				"adjust": DEFAULT_ADJUST,
			},
			long_term_params,
		)

		short_bars = self._market_data.fetch_period(
			symbol,
			period=short_cfg["period"],
			count=short_cfg["count"],
			adjust=short_cfg["adjust"],
			end_time=end_time,
		)
		long_bars = self._market_data.fetch_period(
			symbol,
			period=long_cfg["period"],
			count=long_cfg["count"],
			adjust=long_cfg["adjust"],
			end_time=end_time,
		)

		short_indicators = self._indicator_service.compute(short_bars)
		long_indicators = self._indicator_service.compute(long_bars)

		return self._assembler.assemble(
			symbol,
			short_bars,
			short_indicators,
			long_bars,
			long_indicators,
			short_term_len=short_term_len,
			long_term_len=long_term_len,
		)


def _merge_period_options(
	defaults: MutableMapping[str, Any],
	overrides: Mapping[str, Any] | None,
) -> MutableMapping[str, Any]:
	"""Merge default period configuration with overrides."""
	if overrides:
		defaults.update(overrides)
	return defaults
