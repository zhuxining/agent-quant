"""向量化技术面回测引擎。"""

from decimal import Decimal
from typing import Any

import pandas as pd

from app.models.backtest import (
    BacktestMetrics,
    VectorizedBacktestConfig,
    VectorizedStrategyConfig,
)


class VectorizedTechnicalStrategy:
    """向量化技术面策略。"""

    def __init__(self, config: VectorizedStrategyConfig | None = None):
        """初始化策略。

        Args:
            config: 策略配置，默认使用默认配置
        """
        self.config = config or VectorizedStrategyConfig()

    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        """批量生成交易信号。

        基于 EMA 交叉策略：
        - EMA 金叉（短期上穿长期）→ 买入信号 (1)
        - EMA 死叉（短期下穿长期）→ 卖出信号 (-1)

        Args:
            bars: K 线数据 DataFrame，必须包含 close, ema_short, ema_long 列

        Returns:
            交易信号 Series，index 与 bars 一致
        """
        if len(bars) == 0:
            return pd.Series(dtype=int)

        signals = pd.Series(0, index=bars.index, dtype=int)

        ema_short = bars["ema_short"]
        ema_long = bars["ema_long"]

        ema_short_prev = ema_short.shift(1)
        ema_long_prev = ema_long.shift(1)

        buy_signals = (ema_short > ema_long) & (ema_short_prev <= ema_long_prev)
        sell_signals = (ema_short < ema_long) & (ema_short_prev >= ema_long_prev)

        signals[buy_signals] = 1
        signals[sell_signals] = -1

        return signals

    def calculate_indicators(self, bars: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标。

        Args:
            bars: K 线数据 DataFrame，必须包含 close 列

        Returns:
            添加技术指标的 DataFrame
        """
        if "close" not in bars.columns:
            raise ValueError("bars DataFrame 必须包含 'close' 列")

        df = bars.copy()

        df["ema_short"] = df["close"].ewm(span=self.config.ema_short, adjust=False).mean()
        df["ema_long"] = df["close"].ewm(span=self.config.ema_long, adjust=False).mean()

        return df


class VectorizedBacktestEngine:
    """向量化回测引擎。"""

    def __init__(self, config: VectorizedBacktestConfig):
        """初始化回测引擎。

        Args:
            config: 回测配置
        """
        self.config = config
        self.strategy = VectorizedTechnicalStrategy(config.strategy_config)

    def run(self) -> tuple[pd.DataFrame, BacktestMetrics]:
        """执行向量化回测。

        Args:
            None

        Returns:
            (result_df, metrics) - 回测结果 DataFrame 和绩效指标
        """
        from app.data_source.akshare_source import AkShareSource

        source = AkShareSource()

        result_frames = []

        for symbol in self.config.symbols:
            symbol_result = self._backtest_symbol(source, symbol)
            result_frames.append(symbol_result)

        result_df = pd.concat(result_frames, ignore_index=True)
        metrics = self._calculate_metrics(result_df)

        return result_df, metrics

    def _backtest_symbol(self, source: Any, symbol: str) -> pd.DataFrame:
        """对单个标的进行回测。

        Args:
            source: 数据源
            symbol: 标的代码

        Returns:
            回测结果 DataFrame
        """
        try:
            bars = source.get_candles_frame(
                symbol=symbol,
                interval="1d",
                count=None,
                end_date=None,
            )

            if bars.empty:
                raise ValueError(f"无法获取 {symbol} 的历史数据")

            bars = self.strategy.calculate_indicators(bars)

            signals = self.strategy.generate_signals(bars)

            bars["signal"] = signals
            bars["returns"] = bars["close"].pct_change()
            bars["strategy_returns"] = bars["signal"].shift(1) * bars["returns"]

            bars = bars.iloc[1:]

            return self._apply_costs(bars, symbol)

        except Exception as e:
            print(f"回测 {symbol} 失败: {e}")
            return pd.DataFrame()

    def _apply_costs(self, bars: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """应用交易成本（佣金、滑点）。

        Args:
            bars: K 线数据
            symbol: 标的代码

        Returns:
            添加成本后的 DataFrame
        """
        df = bars.copy()

        df["trade_occurred"] = df["signal"].abs() > 0
        df["trade_direction"] = df["signal"]

        df["gross_return"] = df["strategy_returns"]
        df["commission"] = df["trade_occurred"] * df["close"] * self.config.commission_rate

        df["slippage"] = df["trade_occurred"] * df["close"] * self.config.slippage_rate

        df["net_return"] = df["gross_return"] - df["commission"] - df["slippage"]

        df["cumulative_return"] = (1 + df["net_return"]).cumprod()

        df["equity"] = self.config.initial_capital * df["cumulative_return"]

        return df

    def _calculate_metrics(self, result_df: pd.DataFrame) -> BacktestMetrics:
        """计算回测绩效指标。

        Args:
            result_df: 回测结果 DataFrame

        Returns:
            绩效指标对象
        """
        if result_df.empty:
            return BacktestMetrics(
                total_return=Decimal("0"),
                max_drawdown=Decimal("0"),
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
            )

        final_equity = result_df["equity"].iloc[-1]
        total_return = (final_equity - self.config.initial_capital) / self.config.initial_capital

        equity_series = result_df["equity"]
        cumulative_return = equity_series / self.config.initial_capital - 1
        running_max = cumulative_return.cummax()
        drawdown = cumulative_return - running_max
        max_drawdown = -drawdown.min()

        net_returns = result_df["net_return"].dropna()

        trades = result_df[result_df["trade_occurred"]]
        total_trades = len(trades)

        winning_trades = len(trades[trades["net_return"] > 0])
        losing_trades = total_trades - winning_trades

        win_rate = (
            Decimal(str(winning_trades)) / Decimal(str(total_trades))
            if total_trades > 0
            else Decimal("0")
        )

        if len(net_returns) > 0:
            mean_return = net_returns.mean()
            std_return = net_returns.std()

            sharpe_ratio = (
                Decimal(str(mean_return / std_return)) * (252**0.5)
                if std_return > 0
                else Decimal("0")
            )
        else:
            sharpe_ratio = Decimal("0")

        profit_factor = (
            trades[trades["net_return"] > 0]["net_return"].sum()
            / abs(trades[trades["net_return"] < 0]["net_return"].sum())
            if losing_trades > 0
            else Decimal("0")
        )

        return BacktestMetrics(
            total_return=Decimal(str(total_return)),
            annual_return=Decimal(str(total_return * 12)),
            max_drawdown=Decimal(str(max_drawdown)),
            sharpe_ratio=sharpe_ratio,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
        )


__all__ = [
    "VectorizedBacktestEngine",
    "VectorizedTechnicalStrategy",
]
