"""Longport data source helpers."""

from __future__ import annotations

from datetime import datetime

from longport.openapi import AdjustType, Candlestick, Config, Period, QuoteContext
import pandas as pd

from app.core.config import settings


class LongportSource:
    """封装的 Longport 行情数据源。

    使用 Longport API 获取股票/ETF 的 K 线数据。
    配置从环境变量或 settings 中读取。
    """

    def __init__(self, config: Config | None = None) -> None:
        """初始化数据源。

        Args:
            config: Longport 配置对象, 如未提供则从环境变量读取
        """
        if config is not None:
            self._config = config
        elif settings.LONGPORT_APP_KEY:
            self._config = Config(
                app_key=settings.LONGPORT_APP_KEY,
                app_secret=settings.LONGPORT_APP_SECRET,
                access_token=settings.LONGPORT_ACCESS_TOKEN,
            )
        else:
            self._config = Config.from_env()
        self._quote_ctx = QuoteContext(self._config)

    @property
    def quote_ctx(self) -> QuoteContext:
        """返回底层的 QuoteContext 实例。"""
        return self._quote_ctx

    def _fetch_raw_candles(
        self,
        symbol: str,
        period: Period,
        count: int,
        adjust: AdjustType,
        end_date: datetime | None,
    ) -> list[Candlestick]:
        """获取原始 K 线数据。

        Args:
            symbol: 股票代码
            period: K 线周期
            count: 获取数量
            adjust: 复权类型
            end_date: 结束日期

        Returns:
            K 线列表

        Raises:
            ValueError: 未获取到数据时抛出
        """
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
        adjust: AdjustType = AdjustType.ForwardAdjust,
    ) -> pd.DataFrame:
        """获取 K 线数据并返回 DataFrame。

        Args:
            symbol: 股票代码, 如 "159300.SZ"
            interval: K 线周期, 支持 "1m"/"5m"/"15m"/"30m"/"1h"/"4h"/"1d"/"1w"/"1mo"
            end_date: 结束日期, 默认为当前时间
            count: 获取数量
            adjust: 复权类型, 默认前复权

        Returns:
            包含 OHLCV 数据的 DataFrame, 按时间升序排列
        """
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
        return frame.sort_values("datetime").reset_index(drop=True)


def interval_to_period(interval: str | Period) -> Period:
    """将字符串周期转换为 Period 枚举。

    Args:
        interval: 周期字符串或 Period 枚举

    Returns:
        对应的 Period 枚举值
    """
    if isinstance(interval, Period):
        return interval

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
    return mapping.get(interval.lower(), Period.Day)


__all__ = [
    "LongportSource",
    "interval_to_period",
]
