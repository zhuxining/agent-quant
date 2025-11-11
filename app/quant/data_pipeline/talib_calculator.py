"""Indicator calculator backed by pandas and TA-Lib."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
import talib


class IndicatorCalculator:
	"""计算涨幅, EMA, MACD, RSI, ATR 等指标."""

	def __init__(
		self,
		change_periods: Sequence[int] | None = None,
		ema_periods: Sequence[int] | None = None,
		rsi_periods: Sequence[int] | None = None,
		atr_periods: Sequence[int] | None = None,
		macd_periods: Sequence[int] = (12, 26, 9),
		close_column: str = "close",
		high_column: str = "high",
		low_column: str = "low",
		mid_price_column: str = "mid_price",
	):
		self.change_periods = tuple(change_periods or (1, 5))
		self.ema_periods = tuple(ema_periods or (20, 50))
		self.rsi_periods = tuple(rsi_periods or (7, 14))
		self.atr_periods = tuple(atr_periods or (3, 14))
		if len(macd_periods) != 3:
			raise ValueError("MACD 参数必须是 (fast, slow, signal) 三个整数")
		self.macd_periods = tuple(macd_periods)
		self.close_column = close_column
		self.high_column = high_column
		self.low_column = low_column
		self.mid_price_column = mid_price_column

	def compute_mid_price(self, frame: pd.DataFrame) -> pd.DataFrame:
		"""计算高低价均值，生成中间价列."""
		self._ensure_columns(frame, [self.high_column, self.low_column])
		result = frame.copy()
		result[self.mid_price_column] = (result[self.high_column] + result[self.low_column]) / 2
		return result

	def compute_change(self, frame: pd.DataFrame) -> pd.DataFrame:
		"""计算多周期涨幅（ROCP），返回小数形式(0.02 = 2%)."""
		self._ensure_columns(frame, [self.close_column])
		result = frame.copy()
		close = self._column_as_ndarray(result, self.close_column)
		for period in self.change_periods:
			result[f"change_pct_{period}"] = talib.ROCP(close, timeperiod=period)
		return result

	def compute_ema(self, frame: pd.DataFrame) -> pd.DataFrame:
		"""使用 TA-Lib 计算多周期 EMA, 返回附加指标列后的 DataFrame."""
		self._ensure_columns(frame, [self.close_column])
		result = frame.copy()
		close = self._column_as_ndarray(result, self.close_column)
		for period in self.ema_periods:
			column_name = f"ema_{period}"
			result[column_name] = talib.EMA(close, timeperiod=period)
		return result

	def compute_macd(self, frame: pd.DataFrame) -> pd.DataFrame:
		"""计算 MACD 及其 signal/histogram."""
		self._ensure_columns(frame, [self.close_column])
		result = frame.copy()
		close = self._column_as_ndarray(result, self.close_column)
		fast, slow, signal = self.macd_periods
		macd, macd_signal, macd_hist = talib.MACD(
			close, fastperiod=fast, slowperiod=slow, signalperiod=signal
		)
		result["macd"] = macd
		result["macd_signal"] = macd_signal
		result["macd_hist"] = macd_hist
		return result

	def compute_rsi(self, frame: pd.DataFrame) -> pd.DataFrame:
		"""计算多周期 RSI 指标."""
		self._ensure_columns(frame, [self.close_column])
		result = frame.copy()
		close = self._column_as_ndarray(result, self.close_column)
		for period in self.rsi_periods:
			result[f"rsi_{period}"] = talib.RSI(close, timeperiod=period)
		return result

	def compute_atr(self, frame: pd.DataFrame) -> pd.DataFrame:
		"""计算多周期 ATR."""
		self._ensure_columns(frame, [self.high_column, self.low_column, self.close_column])
		result = frame.copy()
		high = self._column_as_ndarray(result, self.high_column)
		low = self._column_as_ndarray(result, self.low_column)
		close = self._column_as_ndarray(result, self.close_column)
		for period in self.atr_periods:
			result[f"atr_{period}"] = talib.ATR(high, low, close, timeperiod=period)
		return result

	@staticmethod
	def _column_as_ndarray(frame: pd.DataFrame, column: str) -> np.ndarray:
		return frame[column].to_numpy(dtype=float, copy=False)

	@staticmethod
	def _ensure_columns(frame: pd.DataFrame, columns: Sequence[str]) -> None:
		missing = [col for col in columns if col not in frame.columns]
		if missing:
			raise ValueError(f"DataFrame 缺少必需列: {', '.join(missing)}")


__all__ = ["IndicatorCalculator"]
