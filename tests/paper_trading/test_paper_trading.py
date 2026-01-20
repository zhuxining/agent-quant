"""Paper Trading 端到端测试。"""

from decimal import Decimal

from app.paper_trading import (
    CommissionCalculator,
    EnhancedOrderExecutor,
    TradingConfig,
    TradingConfigFactory,
    build_account_overview,
)
from app.paper_trading.slippage import (
    NoSlippageCalculator,
    PercentageSlippageCalculator,
    SlippageType,
)


def test_trading_config_creation():
    """测试交易配置创建。"""
    config = TradingConfig(
        commission_rate=Decimal("0.0003"),
        slippage_pct=Decimal("0.001"),
        slippage_mode="percentage",
        t_plus_1_enabled=True,
        t_plus_1_delay_seconds=0,
        position_limit_pct=Decimal("0.2"),
        max_positions=3,
        default_stop_loss_pct=Decimal("0.02"),
        default_take_profit_pct=Decimal("0.05"),
        min_trade_amount=Decimal("100"),
    )

    assert config.commission_rate == Decimal("0.0003")
    assert config.slippage_pct == Decimal("0.001")
    assert config.t_plus_1_enabled is True

    print(f"\n{'=' * 60}")
    print("交易配置测试结果")
    print(f"{'=' * 60}")
    print(f"手续费率: {config.commission_rate}")
    print(f"滑点率: {config.slippage_pct}")
    print(f"T+1 启用: {config.t_plus_1_enabled}")
    print(f"持仓限制: {config.position_limit_pct}%")
    print(f"止损比例: {config.default_stop_loss_pct}")
    print(f"止盈比例: {config.default_take_profit_pct}")
    print(f"{'=' * 60}\n")

    return True


def test_commission_calculation():
    """测试手续费计算。"""
    config = TradingConfig(
        commission_rate=Decimal("0.0003"),
        slippage_pct=Decimal("0.001"),
    )
    calculator = CommissionCalculator(config)

    # 测试按成交金额计算
    amount = Decimal("10000")
    commission = calculator.calculate_by_amount(amount, config)

    expected = Decimal("10000") * Decimal("0.0003")
    assert commission == expected, f"手续费应为 {expected}, 实际为 {commission}"

    print(f"\n{'=' * 60}")
    print("手续费计算测试结果")
    print(f"{'=' * 60}")
    print(f"交易金额: {amount}")
    print(f"手续费率: 0.03%")
    print(f"手续费: {commission}")
    print(f"{'=' * 60}\n")

    return True


def test_commission_by_shares():
    """测试按股数计算手续费。"""
    config = TradingConfig(
        commission_rate=Decimal("0.0003"),
        slippage_pct=Decimal("0.001"),
    )
    calculator = CommissionCalculator(config)

    price = Decimal("10.0")
    shares = 1000

    commission = calculator.calculate_by_shares(shares, price, config)

    expected = Decimal("1000") * Decimal("10.0") * Decimal("0.0003") / Decimal("10000")
    assert commission == expected, f"手续费应为 {expected}, 实际为 {commission}"

    print(f"\n{'=' * 60}")
    print("按股数计算测试结果")
    print(f"{'=' * 60}")
    print(f"成交股数: {shares}")
    print(f"成交价格: {price}")
    print(f"手续费: {commission}")
    print(f"{'=' * 60}\n")

    return True


def test_percentage_slippage():
    """测试百分比滑点计算。"""
    config = TradingConfig(
        commission_rate=Decimal("0.0003"),
        slippage_pct=Decimal("0.001"),
    )
    calculator = PercentageSlippageCalculator(config.slippage_pct)

    # 测试买入滑点（价格更高）
    price = Decimal("10.0")
    quantity = 1000

    from app.models import OrderSide

    buy_slippage = calculator.calculate(price, quantity, OrderSide.BUY)

    expected = Decimal("10.0") * Decimal("1000") * Decimal("0.001")
    expected = expected / Decimal("100")  # Convert from total value to per-unit

    assert buy_slippage > 0, "买入滑点应为正数"
    assert buy_slippage == expected, f"买入滑点应为 {expected}"

    # 测试卖出滑点（价格更低）
    sell_slippage = calculator.calculate(price, quantity, OrderSide.SELL)

    assert sell_slippage < 0, "卖出滑点应为负数"
    assert sell_slippage == -expected, f"卖出滑点应为 {-expected}"

    print(f"\n{'=' * 60}")
    print("百分比滑点测试结果")
    print(f"{'=' * 60}")
    print(f"滑点率: 0.1%")
    print(f"买入滑点: {buy_slippage}")
    print(f"卖出滑点: {sell_slippage}")
    print(f"{'=' * 60}\n")

    return True


def test_no_slippage():
    """测试无滑点。"""
    calculator = NoSlippageCalculator()
    from app.models import OrderSide

    slippage = calculator.calculate(Decimal("10.0"), 1000, OrderSide.BUY)
    assert slippage == Decimal("0"), "无滑点应返回 0"

    print(f"\n{'=' * 60}")
    print("无滑点测试结果")
    print(f"{'=' * 60}")
    print(f"买入滑点: 0")
    print(f"卖出滑点: 0")
    print(f"{'=' * 60}\n")

    return True


def test_trading_config_factory():
    """测试交易配置工厂。"""
    default_config = TradingConfigFactory.get_default_config()
    assert default_config.commission_rate == Decimal("0.0003")

    # 从字典创建
    config_dict = {
        "commission_rate": "0.0005",
        "slippage_pct": "0.002",
        "t_plus_1_enabled": True,
    }
    custom_config = TradingConfigFactory.get_from_dict(config_dict)
    assert custom_config.commission_rate == Decimal("0.0005")
    assert custom_config.t_plus_1_enabled is True

    print(f"\n{'=' * 60}")
    print("交易配置工厂测试结果")
    print(f"{'=' * 60}")
    print(f"默认配置: ✅")
    print(f"字典创建配置: ✅")
    print(f"{'=' * 60}\n")

    return True


def test_total_cost_and_net_proceeds():
    """测试订单执行结果的总成本和净收益计算。"""

    # 模拟订单执行结果
    from app.paper_trading.enhanced_order import OrderExecutionResult
    from app.models import OrderSide, OrderType, OrderStatus, VirtualTradeOrder
    import uuid

    order = VirtualTradeOrder(
        id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        symbol="000001.SZ",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        price=Decimal("10.0"),
        quantity=1000,
        status=OrderStatus.PENDING,
    )

    result = OrderExecutionResult(
        order=order,
        executed_price=Decimal("10.01"),  # 滑点后价格
        executed_quantity=1000,
        commission=Decimal("3.0"),  # 10000 * 0.0003
        slippage_amount=Decimal("10.0"),  # 滑点成本
    )

    # 测试总成本
    total_cost = result.total_cost
    expected = Decimal("10.01") * Decimal("1000") + Decimal("3.0") + Decimal("10.0")
    assert total_cost == expected, f"总成本计算错误: {total_cost} vs {expected}"

    # 测试净收益
    net_proceeds = result.net_proceeds
    expected_net = (Decimal("10.01") * Decimal("1000")) - Decimal("3.0") - Decimal("10.0")
    assert net_proceeds == expected_net, f"净收益计算错误: {net_proceeds} vs {expected_net}"

    print(f"\n{'=' * 60}")
    print("总成本和净收益测试结果")
    print(f"{'=' * 60}")
    print(f"成交金额: {result.executed_price * Decimal(str(result.executed_quantity))}")
    print(f"手续费: {result.commission}")
    print(f"滑点: {result.slippage_amount}")
    print(f"总成本: {total_cost}")
    print(f"净收益: {net_proceeds}")
    print(f"{'=' * 60}\n")

    return True


def test_trading_config_validation():
    """测试交易配置验证。"""

    # 测试有效配置
    valid_config = TradingConfig(
        commission_rate=Decimal("0.0003"),
        slippage_pct=Decimal("0.001"),
    )

    # 验证手续费率范围
    assert Decimal("0") <= valid_config.commission_rate <= Decimal("0.001")

    # 验证滑点率范围
    assert Decimal("0") <= valid_config.slippage_pct <= Decimal("0.01")

    # 验证止损止盈比例
    assert Decimal("0") <= valid_config.default_stop_loss_pct <= Decimal("1")

    # 验证持仓限制
    assert Decimal("0") <= valid_config.position_limit_pct <= Decimal("1")

    print(f"\n{'=' * 60}")
    print("交易配置验证测试结果")
    print(f"{'=' * 60}")
    print(f"手续费率范围: ✅ (0 ~ 0.1%)")
    print(f"滑点率范围: ✅ (0 ~ 1%)")
    print(f"止损止盈范围: ✅ (0 ~ 100%)")
    print(f"持仓限制范围: ✅ (0 ~ 100%)")
    print(f"{'=' * 60}\n")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Paper Trading 端到端测试套件")
    print("=" * 60)

    test_count = 0
    passed_count = 0

    tests = [
        ("交易配置创建", test_trading_config_creation),
        ("手续费计算（按金额）", test_commission_calculation),
        ("手续费计算（按股数）", test_commission_by_shares),
        ("百分比滑点", test_percentage_slippage),
        ("无滑点", test_no_slippage),
        ("交易配置工厂", test_trading_config_factory),
        ("总成本和净收益", test_total_cost_and_net_proceeds),
        ("配置验证", test_trading_config_validation),
    ]

    for test_name, test_func in tests:
        test_count += 1
        try:
            if test_func():
                passed_count += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 未返回 True")
        except Exception as e:
            print(f"❌ {test_name} 失败: {e}")

    print("\n" + "=" * 60)
    print(f"测试总结: {passed_count}/{test_count} 通过")
    print("=" * 60)

    if passed_count == test_count:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️  {test_count - passed_count} 个测试失败")
