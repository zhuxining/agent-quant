"""Indicator calculator backed by pandas and TA-Lib."""

from collections.abc import Sequence

import numpy as np
import pandas as pd
import talib


class IndicatorCalculator:
    """计算涨幅, EMA, MACD, RSI, ATR 等指标."""

    DEFAULT_CHANGE_PERIODS = (1, 5)
    DEFAULT_EMA_PERIODS = (20, 50)
    DEFAULT_RSI_PERIODS = (7, 14)
    DEFAULT_ATR_PERIODS = (3, 14)
    DEFAULT_MACD_PERIODS = (12, 26, 9)
    DEFAULT_CLOSE_COLUMN = "close"
    DEFAULT_HIGH_COLUMN = "high"
    DEFAULT_LOW_COLUMN = "low"

    @staticmethod
    def compute_change(
        frame: pd.DataFrame,
        *,
        change_periods: Sequence[int] | None = None,
        close_column: str = DEFAULT_CLOSE_COLUMN,
    ) -> pd.DataFrame:
        """计算多周期涨幅(ROCP),返回小数形式(0.02 = 2%)."""

        periods = tuple(change_periods or IndicatorCalculator.DEFAULT_CHANGE_PERIODS)
        IndicatorCalculator._ensure_columns(frame, [close_column])
        result = frame.copy()
        close = IndicatorCalculator._column_as_ndarray(result, close_column)
        for period in periods:
            result[f"change_pct_{period}"] = talib.ROCP(close, timeperiod=period)
        return result

    @staticmethod
    def compute_mid_price(
        frame: pd.DataFrame,
        *,
        high_column: str = DEFAULT_HIGH_COLUMN,
        low_column: str = DEFAULT_LOW_COLUMN,
    ) -> pd.DataFrame:
        """计算高低价均值,生成中间价列."""

        IndicatorCalculator._ensure_columns(frame, [high_column, low_column])
        result = frame.copy()
        high = IndicatorCalculator._column_as_ndarray(result, high_column)
        low = IndicatorCalculator._column_as_ndarray(result, low_column)
        result["mid_price"] = talib.MIDPRICE(high, low, timeperiod=2)
        return result

    @staticmethod
    def compute_ema(
        frame: pd.DataFrame,
        *,
        ema_periods: Sequence[int] | None = None,
        close_column: str = DEFAULT_CLOSE_COLUMN,
    ) -> pd.DataFrame:
        """使用 TA-Lib 计算多周期 EMA, 返回附加指标列后的 DataFrame."""

        periods = tuple(ema_periods or IndicatorCalculator.DEFAULT_EMA_PERIODS)
        IndicatorCalculator._ensure_columns(frame, [close_column])
        result = frame.copy()
        close = IndicatorCalculator._column_as_ndarray(result, close_column)
        for period in periods:
            column_name = f"ema_{period}"
            result[column_name] = talib.EMA(close, timeperiod=period)
        return result

    @staticmethod
    def compute_macd(
        frame: pd.DataFrame,
        *,
        macd_periods: Sequence[int] | None = None,
        close_column: str = DEFAULT_CLOSE_COLUMN,
    ) -> pd.DataFrame:
        """计算 MACD 及其 signal/histogram."""

        periods = tuple(macd_periods or IndicatorCalculator.DEFAULT_MACD_PERIODS)
        if len(periods) != 3:
            raise ValueError("MACD 参数必须是 (fast, slow, signal) 三个整数")
        IndicatorCalculator._ensure_columns(frame, [close_column])
        result = frame.copy()
        close = IndicatorCalculator._column_as_ndarray(result, close_column)
        fast, slow, signal = periods
        macd, macd_signal, macd_hist = talib.MACD(
            close, fastperiod=fast, slowperiod=slow, signalperiod=signal
        )
        result["macd"] = macd
        result["macd_signal"] = macd_signal
        result["macd_hist"] = macd_hist
        return result

    @staticmethod
    def compute_rsi(
        frame: pd.DataFrame,
        *,
        rsi_periods: Sequence[int] | None = None,
        close_column: str = DEFAULT_CLOSE_COLUMN,
    ) -> pd.DataFrame:
        """计算多周期 RSI 指标."""

        periods = tuple(rsi_periods or IndicatorCalculator.DEFAULT_RSI_PERIODS)
        IndicatorCalculator._ensure_columns(frame, [close_column])
        result = frame.copy()
        close = IndicatorCalculator._column_as_ndarray(result, close_column)
        for period in periods:
            result[f"rsi_{period}"] = talib.RSI(close, timeperiod=period)
        return result

    @staticmethod
    def compute_atr(
        frame: pd.DataFrame,
        *,
        atr_periods: Sequence[int] | None = None,
        high_column: str = DEFAULT_HIGH_COLUMN,
        low_column: str = DEFAULT_LOW_COLUMN,
        close_column: str = DEFAULT_CLOSE_COLUMN,
    ) -> pd.DataFrame:
        """计算多周期 ATR."""

        periods = tuple(atr_periods or IndicatorCalculator.DEFAULT_ATR_PERIODS)
        IndicatorCalculator._ensure_columns(frame, [high_column, low_column, close_column])
        result = frame.copy()
        high = IndicatorCalculator._column_as_ndarray(result, high_column)
        low = IndicatorCalculator._column_as_ndarray(result, low_column)
        close = IndicatorCalculator._column_as_ndarray(result, close_column)
        for period in periods:
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
