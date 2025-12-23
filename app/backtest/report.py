"""回测报告生成: 使用 quantstats 分析绩效。"""

from pathlib import Path

import pandas as pd
import quantstats as qs

from app.backtest.equity import EquityCurve


class BacktestReporter:
    """回测报告生成器。

    使用 quantstats 库分析收益率序列,生成 HTML 报告和绩效指标。
    """

    def __init__(self, equity_curve: EquityCurve, benchmark_ticker: str = "000300.SS"):
        """初始化报告生成器。

        Args:
            equity_curve: 净值曲线
            benchmark_ticker: 基准指数代码 (默认沪深300)
        """
        self.equity_curve = equity_curve
        self.benchmark_ticker = benchmark_ticker
        self._returns: pd.Series | None = None

    @property
    def returns(self) -> pd.Series:
        """获取收益率序列。"""
        if self._returns is None:
            self._returns = self.equity_curve.to_returns_series()
        return self._returns

    def calculate_metrics(self) -> dict:
        """计算绩效指标。"""
        try:
            import quantstats as qs
        except ImportError:
            return self._fallback_metrics()

        if self.returns.empty:
            return {}

        return {
            "total_return": float(qs.stats.comp(self.returns) * 100),
            "cagr": float(qs.stats.cagr(self.returns) * 100),
            "sharpe": float(qs.stats.sharpe(self.returns)),
            "sortino": float(qs.stats.sortino(self.returns)),
            "max_drawdown": float(qs.stats.max_drawdown(self.returns) * 100),
            "volatility": float(qs.stats.volatility(self.returns) * 100),
            "calmar": float(qs.stats.calmar(self.returns)),
            "win_rate": float(qs.stats.win_rate(self.returns) * 100),
        }

    def _fallback_metrics(self) -> dict:
        """quantstats 不可用时的简化指标计算。"""
        if self.returns.empty:
            return {}

        total_return = self.equity_curve.total_return or 0.0
        volatility = float(self.returns.std() * (252**0.5) * 100) if len(self.returns) > 1 else 0.0

        # 简化版夏普比率 (假设无风险利率为 0)
        mean_return = float(self.returns.mean() * 252)
        sharpe = mean_return / (volatility / 100) if volatility > 0 else 0.0

        # 简化版最大回撤
        cumulative = (1 + self.returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdowns = (cumulative - rolling_max) / rolling_max
        max_drawdown = float(drawdowns.min() * 100)

        return {
            "total_return": total_return,
            "sharpe": sharpe,
            "max_drawdown": max_drawdown,
            "volatility": volatility,
        }

    def generate_html_report(
        self,
        output_path: str | Path,
        title: str = "Backtest Report",
    ) -> Path:
        """生成 HTML 报告。

        Args:
            output_path: 输出文件路径
            title: 报告标题

        Returns:
            报告文件路径
        """

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        qs.reports.html(
            self.returns,
            benchmark=None,  # TODO: 可选择添加基准对比
            output=str(output_path),
            title=title,
        )

        return output_path

    def print_summary(self) -> None:
        """打印绩效摘要。"""
        metrics = self.calculate_metrics()
        if not metrics:
            print("无可用数据")
            return

        print("\n" + "=" * 50)
        print("回测绩效摘要")
        print("=" * 50)
        print(f"总收益率:     {metrics.get('total_return', 0):.2f}%")
        print(f"夏普比率:     {metrics.get('sharpe', 0):.2f}")
        print(f"最大回撤:     {metrics.get('max_drawdown', 0):.2f}%")
        print(f"年化波动率:   {metrics.get('volatility', 0):.2f}%")
        if "cagr" in metrics:
            print(f"年化收益率:   {metrics.get('cagr', 0):.2f}%")
        if "sortino" in metrics:
            print(f"索提诺比率:   {metrics.get('sortino', 0):.2f}")
        if "win_rate" in metrics:
            print(f"胜率:         {metrics.get('win_rate', 0):.2f}%")
        print("=" * 50 + "\n")


__all__ = [
    "BacktestReporter",
]
