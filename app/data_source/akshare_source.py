"""AkShare data source helpers for Chinese A-share market."""

from datetime import datetime
from typing import Any

import akshare as ak
import pandas as pd


class AkShareSource:
    """封装的 AkShare 行情数据源。

    使用 AkShare API 获取中国 A 股的实时行情、历史数据、新闻和基本面数据。
    """

    def __init__(self) -> None:
        """初始化 AkShare 数据源。"""
        pass

    def get_spot_quotes(self, symbols: list[str] | None = None) -> list[dict[str, Any]]:
        """获取 A 股实时行情。

        Args:
            symbols: 股票代码列表，如 ["000001", "600000"]。如果为 None，则获取所有 A 股实时行情。

        Returns:
            包含实时行情的字典列表，每个字典包含 symbol, price, volume 等字段
        """
        try:
            if symbols:
                df = ak.stock_zh_a_spot_em()
                filtered_df = df[df["代码"].isin(symbols)]
            else:
                df = ak.stock_zh_a_spot_em()
                filtered_df = df

            quotes = [
                {
                    "symbol": row["代码"],
                    "name": row["名称"],
                    "price": float(row["最新价"]),
                    "prev_close": float(row["昨收"]),
                    "open": float(row["今开"]),
                    "high": float(row["最高"]),
                    "low": float(row["最低"]),
                    "volume": float(row["成交量"]),
                    "turnover": float(row["成交额"]),
                    "change_pct": float(row["涨跌幅"]),
                }
                for _, row in filtered_df.iterrows()
            ]
            return quotes
        except Exception as e:
            raise ValueError(f"获取 A 股实时行情失败: {e}") from e

    def get_candles_frame(
        self,
        symbol: str,
        period: str = "daily",
        end_date: str | datetime | None = None,
        count: int = 120,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """获取 A 股历史 K 线数据。

        Args:
            symbol: 股票代码，如 "000001"（平安银行）
            period: K 线周期，支持 "daily"/"weekly"/"monthly"
            end_date: 结束日期，格式如 "20241231" 或 datetime 对象，默认为当前日期
            count: 获取数量
            adjust: 复权类型，"qfq"=前复权（默认），"hfq"=后复权，""=不复权

        Returns:
            包含 OHLCV 数据的 DataFrame，按时间升序排列
        """
        try:
            if end_date is None:
                end_date = datetime.now().strftime("%Y%m%d")
            elif isinstance(end_date, datetime):
                end_date = end_date.strftime("%Y%m%d")

            if period == "daily":
                df = ak.stock_zh_a_hist(
                    symbol=symbol, period="daily", end_date=end_date, adjust=adjust
                )
            elif period == "weekly":
                df = ak.stock_zh_a_hist(
                    symbol=symbol, period="weekly", end_date=end_date, adjust=adjust
                )
            elif period == "monthly":
                df = ak.stock_zh_a_hist(
                    symbol=symbol, period="monthly", end_date=end_date, adjust=adjust
                )
            else:
                raise ValueError(f"不支持的周期: {period}")

            df = df.rename(
                columns={
                    "日期": "datetime",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "turnover",
                }
            )

            df["symbol"] = symbol
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.sort_values("datetime").reset_index(drop=True)

            if len(df) > count:
                df = df.tail(count).reset_index(drop=True)

            return df
        except Exception as e:
            raise ValueError(f"获取 {symbol} 的K线数据失败: {e}") from e

    def get_news(self, symbol: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """获取 A 股新闻数据。

        Args:
            symbol: 股票代码，如 "000001"。如果为 None，则获取所有 A 股新闻
            limit: 获取数量

        Returns:
            包含新闻数据的字典列表
        """
        try:
            df = ak.stock_news_em(symbol=symbol) if symbol else ak.stock_news_em()

            news_list = []
            for _, row in df.head(limit).iterrows():
                news_list.append(
                    {
                        "symbol": row.get("代码", symbol) if symbol else "",
                        "title": row.get("新闻标题", ""),
                        "content": row.get("新闻内容", ""),
                        "publish_time": row.get("发布时间", ""),
                        "source": row.get("文章来源", ""),
                        "url": row.get("新闻链接", ""),
                    }
                )

            return news_list
        except Exception as e:
            raise ValueError(f"获取 A 股新闻失败: {e}") from e

    def get_fundamental(self, symbol: str) -> dict[str, Any]:
        """获取 A 股基本面数据。

        Args:
            symbol: 股票代码，如 "000001"

        Returns:
            包含基本面数据的字典
        """
        try:
            info_df = ak.stock_individual_info_em(symbol=symbol)

            info_dict = {}
            for _, row in info_df.iterrows():
                key = row["item"]
                value = row["value"]
                info_dict[key] = value

            try:
                indicator_df = ak.stock_financial_analysis_indicator(symbol=symbol)
                if not indicator_df.empty:
                    latest_indicator = indicator_df.iloc[0]
                    info_dict["最新财务指标"] = latest_indicator.to_dict()
            except Exception:
                pass

            return info_dict
        except Exception as e:
            raise ValueError(f"获取 {symbol} 的基本面数据失败: {e}") from e


__all__ = [
    "AkShareSource",
]
