"""向量化回测端到端测试。"""

from datetime import date
from decimal import Decimal

from app.backtest import VectorizedBacktestEngine
from app.models.backtest import BacktestMode, VectorizedBacktestConfig, VectorizedStrategyConfig


def test_vectorized_backtest_execution():
    """测试向量化回测完整流程。"""
    # 配置回测参数
    config = VectorizedBacktestConfig(
        mode=BacktestMode.VECTORIZED,
        symbols=["000001.SZ"],  # 平安银行
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        initial_capital=Decimal("100000"),
        strategy_config=VectorizedStrategyConfig(
            ema_short=5,
            ema_long=20,
        ),
        commission_rate=Decimal("0.0003"),  # 万三手续费
        slippage_rate=Decimal("0.001"),  # 0.1% 滑点
    )

    # 创建回测引擎
    engine = VectorizedBacktestEngine(config)

    # 执行回测
    result_df, metrics = engine.run()

    # 打印调试信息
    print(f"\n回测结果 DataFrame 形状: {result_df.shape}")
    print(f"列名: {result_df.columns.tolist()}")
    if not result_df.empty:
        print(f"前5行:\n{result_df.head()}")

    # 验证结果
    assert not result_df.empty, "回测结果不应为空"
    assert "equity" in result_df.columns, "结果应包含权益曲线"
    assert "net_return" in result_df.columns, "结果应包含净收益"

    # 验证指标
    assert metrics.total_trades > 0, "应产生交易"
    assert metrics.max_drawdown >= 0, "最大回撤应为正数"
    assert isinstance(metrics.sharpe_ratio, Decimal), "夏普比率应为 Decimal"

    # 打印结果摘要
    print(f"\n{'=' * 60}")
    print("向量化回测测试结果")
    print(f"{'=' * 60}")
    print(f"标的: {config.symbols[0]}")
    print(f"日期范围: {config.start_date} → {config.end_date}")
    print(f"初始资金: {config.initial_capital}")
    print("\n策略参数:")
    print(f"  EMA短期: {config.strategy_config.ema_short}")
    print(f"  EMA长期: {config.strategy_config.ema_long}")
    print(f"  手续费率: {config.commission_rate}")
    print(f"  滑点率: {config.slippage_rate}")
    print("\n绩效指标:")
    print(f"  总收益率: {float(metrics.total_return):.2%}")
    print(f"  最大回撤: {float(metrics.max_drawdown):.2%}")
    print(f"  夏普比率: {float(metrics.sharpe_ratio):.4f}")
    print(f"  总交易次数: {metrics.total_trades}")
    print(f"  盈利交易: {metrics.winning_trades}")
    print(f"  亏损交易: {metrics.losing_trades}")
    print(f"  胜率: {float(metrics.win_rate) if metrics.win_rate is not None else 0:.2%}")
    print(f"  盈亏比: {float(metrics.profit_factor) if metrics.profit_factor is not None else 0:.2f}")
    print(f"{'=' * 60}\n")

    return True


if __name__ == "__main__":
    test_vectorized_backtest_execution()
