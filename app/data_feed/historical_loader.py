"""历史数据加载模块。

支持从 CSV 文件和数据库加载历史行情数据，用于离线回测和混合策略回测。
"""

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession


class HistoricalDataLoader:
    """历史数据加载器。

    支持从 CSV 文件和数据库加载历史 OHLCV 数据。
    自动识别多种数据格式，返回标准化的 DataFrame。
    """

    def __init__(self, indicator_calculator: Any | None = None):
        """初始化历史数据加载器。

        Args:
            indicator_calculator: 技术指标计算器（可选）
        """
        self.indicator_calculator = indicator_calculator

    def load_from_csv(
        self,
        file_path: str | Path,
        symbol: str | None = None,
        date_column: str = "date",
    ) -> pd.DataFrame:
        """从 CSV 文件加载历史数据。

        自动识别多种格式：
        - 标准 OHLCV: date, symbol, open, high, low, close, volume
        - AkShare: date, open, high, low, close, volume, amount, change_pct
        - Longport: timestamp, symbol, open, high, low, close, volume, turnover

        Args:
            file_path: CSV 文件路径
            symbol: 标的代码（如果 CSV 中没有 symbol 列）
            date_column: 日期列名，默认为 "date"

        Returns:
            标准化的 DataFrame，包含列：date, symbol, open, high, low, close, volume

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 缺少必需的列
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 读取 CSV
        df = pd.read_csv(file_path)

        # 检测数据格式
        detected_format = self._detect_format(df)

        # 标准化列名
        df = self._standardize_columns(df, detected_format)

        # 转换日期列
        df = self._convert_dates(df, detected_format, date_column)

        # 添加 symbol 列（如果需要）
        if "symbol" not in df.columns and symbol:
            df["symbol"] = symbol

        # 验证必需列
        required_cols = ["date", "symbol", "open", "high", "low", "close", "volume"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            raise ValueError(f"缺少必需的列: {missing_cols}")

        # 选择需要的列
        df = df[required_cols]

        # 转换数据类型
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # 排序
        df = df.sort_values(["symbol", "date"]).reset_index(drop=True)

        return df

    async def load_from_db(
        self,
        session: AsyncSession,
        symbol: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """从数据库加载历史数据。

        查询 historical_bars 表，支持按标的代码和日期范围过滤。

        Args:
            session: 数据库会话
            symbol: 标的代码（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            标准化的 DataFrame，包含列：date, symbol, open, high, low, close, volume
        """
        # 注意：HistoricalBars 表需要在 models/backtest.py 中定义
        # TODO: 实现 HistoricalBars 模型并启用 DB 加载
        # 临时返回空 DataFrame，等待表创建
        return pd.DataFrame()

    async def load_multiple_symbols(
        self,
        file_paths: dict[str, str] | None = None,
        symbols: list[str] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        session: AsyncSession | None = None,
    ) -> pd.DataFrame:
        """批量加载多个标的的历史数据。

        可以从 CSV 文件或数据库批量加载。

        Args:
            file_paths: 标的代码到文件路径的映射，如 {"000001.SZ": "/path/to/file.csv"}
            symbols: 标的代码列表（用于从数据库加载）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            session: 数据库会话（从数据库加载时必需）

        Returns:
            合并后的 DataFrame，包含所有标的的数据

        Raises:
            ValueError: 既没有提供 file_paths 也没有提供 symbols
        """
        if file_paths is None and symbols is None:
            raise ValueError("必须提供 file_paths 或 symbols 参数")

        result_frames = []

        # 从 CSV 文件加载
        if file_paths:
            for symbol, file_path in file_paths.items():
                try:
                    df = self.load_from_csv(file_path, symbol=symbol)
                    result_frames.append(df)
                except (FileNotFoundError, ValueError) as e:
                    print(f"加载 {symbol} 失败: {e}")

        # 从数据库加载
        if symbols and session:
            for symbol in symbols:
                try:
                    df = await self.load_from_db(
                        session=session,
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
                    )
                    result_frames.append(df)
                except Exception as e:
                    print(f"从数据库加载 {symbol} 失败: {e}")

        if not result_frames:
            return pd.DataFrame()

        # 合并所有数据
        result_df = pd.concat(result_frames, ignore_index=True)

        # 排序
        result_df = result_df.sort_values(["symbol", "date"]).reset_index(drop=True)

        return result_df

    async def incremental_update(
        self,
        session: AsyncSession,
        symbol: str,
        csv_path: str | None = None,
        db_start_date: date | None = None,
        db_end_date: date | None = None,
    ) -> pd.DataFrame:
        """增量更新历史数据。

        合并数据库现有数据和 CSV 文件中的新数据。

        Args:
            session: 数据库会话
            symbol: 标的代码
            csv_path: CSV 文件路径（可选）
            db_start_date: 数据库查询开始日期
            db_end_date: 数据库查询结束日期

        Returns:
            合并后的 DataFrame
        """
        # 加载数据库中的现有数据
        existing_df = await self.load_from_db(
            session=session,
            symbol=symbol,
            start_date=db_start_date,
            end_date=db_end_date,
        )

        # 加载 CSV 文件中的新数据
        if csv_path:
            try:
                new_df = self.load_from_csv(csv_path, symbol=symbol)

                # 如果有现有数据，只添加新数据
                if not existing_df.empty:
                    last_date = existing_df["date"].max()
                    new_df = new_df[new_df["date"] > last_date]

                if not new_df.empty:
                    merged_df = pd.concat([existing_df, new_df], ignore_index=True)
                    merged_df = merged_df.sort_values(["symbol", "date"]).reset_index(drop=True)

                    # 去重（保留最新数据）
                    merged_df = merged_df.drop_duplicates(subset=["symbol", "date"], keep="last")

                    return merged_df
            except (FileNotFoundError, ValueError) as e:
                print(f"加载 CSV 文件失败: {e}")

        return existing_df

    @staticmethod
    def _detect_format(df: pd.DataFrame) -> str:
        """检测 CSV 文件的数据格式。

        Args:
            df: 原始 DataFrame

        Returns:
            格式类型：'standard', 'akshare', 'longport'
        """
        cols = set(df.columns)

        # 检测 Longport 格式（timestamp 列）
        if "timestamp" in cols or "time" in cols:
            return "longport"

        # 检测 AkShare 格式（amount, change_pct 列）
        if "amount" in cols and "change_pct" in cols:
            return "akshare"

        # 默认为标准格式
        return "standard"

    @staticmethod
    def _standardize_columns(df: pd.DataFrame, format_type: str) -> pd.DataFrame:
        """标准化列名。

        Args:
            df: 原始 DataFrame
            format_type: 数据格式类型

        Returns:
            标准化列名后的 DataFrame
        """
        df = df.copy()

        if format_type == "akshare":
            # AkShare 格式：date, open, high, low, close, volume, amount, change_pct
            # 列名已经是标准格式，只需要添加 symbol 列（如果需要）
            pass

        elif format_type == "longport":
            # Longport 格式：timestamp, symbol, open, high, low, close, volume, turnover
            # 需要将 timestamp 转换为 date 列
            if "timestamp" in df.columns:
                df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.date
                df = df.drop(columns=["timestamp"])
            elif "time" in df.columns:
                df["date"] = pd.to_datetime(df["time"], unit="ms").dt.date
                df = df.drop(columns=["time"])

        # 标准格式不需要转换
        return df

    @staticmethod
    def _convert_dates(
        df: pd.DataFrame,
        format_type: str,
        date_column: str,
    ) -> pd.DataFrame:
        """转换日期列。

        Args:
            df: DataFrame
            format_type: 数据格式类型
            date_column: 日期列名

        Returns:
            转换后的 DataFrame
        """
        df = df.copy()

        if format_type == "longport":
            # Longport 格式已经在 _standardize_columns 中处理
            pass
        else:
            # 标准格式和 AkShare 格式
            if date_column in df.columns:
                df["date"] = pd.to_datetime(df[date_column]).dt.date

        return df


__all__ = [
    "HistoricalDataLoader",
]
