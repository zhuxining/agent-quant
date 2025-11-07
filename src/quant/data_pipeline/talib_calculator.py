"""Indicator calculator backed by pandas and TA-Lib."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
import talib

from src.quant.core.interfaces import IndicatorCalculator
from src.quant.core.types import IndicatorSnapshot, MarketBar


class TalibIndicatorCalculator(IndicatorCalculator):
	"""Compute technical indicators for a sequence of market bars."""

	def compute(self, bars: Sequence[MarketBar]) -> IndicatorSnapshot:
		"""Compute EMA, MACD, RSI, and ATR series for the provided bars."""
		if not bars:
			msg = "缺少行情数据，无法计算指标"
			raise ValueError(msg)

		frame = _bars_to_frame(bars)
		highs = frame["high"].to_numpy(dtype=np.float64)
		lows = frame["low"].to_numpy(dtype=np.float64)
		closes = frame["close"].to_numpy(dtype=np.float64)

		frame["mid"] = (highs + lows) / 2.0
		frame["ema_20"] = talib.EMA(closes, timeperiod=20)
		frame["ema_50"] = talib.EMA(closes, timeperiod=50)

		macd, macd_signal, macd_hist = talib.MACD(
			closes,
			fastperiod=12,
			slowperiod=26,
			signalperiod=9,
		)
		frame["macd"] = macd
		frame["macd_signal"] = macd_signal
		frame["macd_hist"] = macd_hist

		frame["rsi_7"] = talib.RSI(closes, timeperiod=7)
		frame["rsi_14"] = talib.RSI(closes, timeperiod=14)

		frame["atr_3"] = talib.ATR(highs, lows, closes, timeperiod=3)
		frame["atr_14"] = talib.ATR(highs, lows, closes, timeperiod=14)

		latest = frame.iloc[-1]
		values = {
			"close": _maybe_float(latest.get("close")),
			"ema_20": _maybe_float(latest.get("ema_20")),
			"ema_50": _maybe_float(latest.get("ema_50")),
			"macd": _maybe_float(latest.get("macd")),
			"macd_signal": _maybe_float(latest.get("macd_signal")),
			"macd_hist": _maybe_float(latest.get("macd_hist")),
			"rsi_7": _maybe_float(latest.get("rsi_7")),
			"rsi_14": _maybe_float(latest.get("rsi_14")),
			"atr_3": _maybe_float(latest.get("atr_3")),
			"atr_14": _maybe_float(latest.get("atr_14")),
			"volume": _maybe_float(latest.get("volume")),
		}

		series = {
			"mid": _safe_list(frame["mid"]),
			"ema_20": _safe_list(frame["ema_20"]),
			"ema_50": _safe_list(frame["ema_50"]),
			"macd": _safe_list(frame["macd"]),
			"macd_signal": _safe_list(frame["macd_signal"]),
			"macd_hist": _safe_list(frame["macd_hist"]),
			"rsi_7": _safe_list(frame["rsi_7"]),
			"rsi_14": _safe_list(frame["rsi_14"]),
			"atr_3": _safe_list(frame["atr_3"]),
			"atr_14": _safe_list(frame["atr_14"]),
			"volume": _safe_list(frame["volume"]),
		}

		symbol = bars[-1].symbol
		timestamp = frame["timestamp"].iloc[-1]
		if hasattr(timestamp, "to_pydatetime"):
			timestamp = timestamp.to_pydatetime()

		return IndicatorSnapshot(
			symbol=symbol,
			timestamp=timestamp,
			values=values,
			metadata={"series": series},
		)


def _bars_to_frame(bars: Sequence[MarketBar]) -> pd.DataFrame:
	"""Convert market bars to a pandas DataFrame sorted by timestamp."""
	records = [
		{
			"symbol": bar.symbol,
			"timestamp": bar.timestamp,
			"open": float(bar.open),
			"high": float(bar.high),
			"low": float(bar.low),
			"close": float(bar.close),
			"volume": float(bar.volume),
		}
		for bar in bars
	]
	frame = pd.DataFrame(records)
	frame.sort_values("timestamp", inplace=True)
	frame.reset_index(drop=True, inplace=True)
	return frame


def _safe_list(series: pd.Series) -> list[float | None]:
	"""Convert a pandas Series to a list with None in place of NaN."""
	values = []
	for value in series.tolist():
		if pd.isna(value):
			values.append(None)
		else:
			values.append(float(value))
	return values


def _maybe_float(value: Any) -> float | None:
	"""Return a float unless the value is missing."""
	if value is None or pd.isna(value):
		return None
	return float(value)
