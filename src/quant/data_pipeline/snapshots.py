"""Utilities to assemble structured prompt snapshots."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from src.quant.core.types import IndicatorSnapshot, MarketBar


def _tail(values: Sequence[float | None], length: int) -> list[float]:
	"""Return the last ``length`` non-null values converted to floats."""
	trimmed: list[float] = []
	for value in values[-length:]:
		if value is None:
			continue
		numeric = float(value)
		if math.isnan(numeric):
			continue
		trimmed.append(numeric)
	return trimmed


def _latest(series: Sequence[float | None]) -> float | None:
	"""Return the latest non-null numeric value from a sequence."""
	for value in reversed(series):
		if value is None:
			continue
		numeric = float(value)
		if math.isnan(numeric):
			continue
		return numeric
	return None


@dataclass(slots=True)
class SnapshotAssembler:
	"""Compose prompt-ready snapshots from indicator outputs."""

	def assemble(
		self,
		symbol: str,
		short_bars: Sequence[MarketBar],
		short_indicators: IndicatorSnapshot,
		long_bars: Sequence[MarketBar],
		long_indicators: IndicatorSnapshot,
		*,
		short_term_len: int = 10,
		long_term_len: int = 15,
	) -> dict[str, Any]:
		"""Combine short/long indicator series into a prompt snapshot structure."""
		if not short_bars and not long_bars:
			raise ValueError("缺少K线数据，无法生成快照")

		short_series = short_indicators.metadata.get("series", {})
		long_series = long_indicators.metadata.get("series", {})

		latest_close = (
			short_indicators.values.get("close")
			if short_bars
			else long_indicators.values.get("close")
		)
		latest_volume = (
			short_indicators.values.get("volume")
			if short_bars
			else long_indicators.values.get("volume")
		)

		snapshot: dict[str, Any] = {
			"symbol": symbol,
			"current_price": latest_close,
			"current_ema20": short_indicators.values.get("ema_20"),
			"current_macd": short_indicators.values.get("macd"),
			"current_rsi7": short_indicators.values.get("rsi_7"),
			"short_term": {
				"mid_prices": _tail(short_series.get("mid", []), short_term_len),
				"ema20_values": _tail(short_series.get("ema_20", []), short_term_len),
				"macd_values": _tail(short_series.get("macd", []), short_term_len),
				"rsi7_values": _tail(short_series.get("rsi_7", []), short_term_len),
				"rsi14_values": _tail(short_series.get("rsi_14", []), short_term_len),
			},
			"long_term": {
				"ema20": long_indicators.values.get("ema_20"),
				"ema50": long_indicators.values.get("ema_50"),
				"atr3": long_indicators.values.get("atr_3"),
				"atr14": long_indicators.values.get("atr_14"),
				"current_volume": latest_volume,
				"average_volume": _average(long_series.get("volume", [])),
				"macd_values": _tail(long_series.get("macd", []), long_term_len),
				"rsi14_values": _tail(long_series.get("rsi_14", []), long_term_len),
			},
		}

		return snapshot


def _average(values: Sequence[float | None]) -> Any | None:
	"""Calculate the average of a sequence ignoring missing values."""
	cleaned = [float(value) for value in values if value is not None and not _is_nan(value)]
	if not cleaned:
		return None
	return sum(cleaned) / len(cleaned)


def _is_nan(value: float | None) -> bool:
	"""Return whether the provided value is NaN."""
	if value is None:
		return False
	try:
		numeric = float(value)
	except (TypeError, ValueError):
		return True
	return math.isnan(numeric)
