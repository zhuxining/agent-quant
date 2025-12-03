"""PromptComposer 单元测试。"""

from decimal import Decimal

from app.execution.prompt_composer import PromptComposer

from app.market.data_feed import MarketSnapshot
from app.models import PositionSide
from app.trade.account import AccountOverview
from app.trade.position import PositionSummary


class TestPromptComposer:
    """测试 PromptComposer 的各个格式化方法。"""

    def test_compose_market_section_empty(self):
        """测试空市场数据的情况。"""
        result = PromptComposer.compose_market_section([])
        assert "暂无市场数据" in result
        assert "## 当前所有标的的市场数据" in result

    def test_compose_market_section_with_data(self):
        """测试有市场数据的情况。"""
        snapshot = MarketSnapshot(
            symbol="AAPL.US",
            current_price=150.5,
            current_ema20=149.0,
            current_macd=1.2,
            current_rsi7=65.5,
            short_term_mid_prices=[148.0, 149.0, 150.5],
            short_term_ema20=[148.5, 149.0, 149.5],
            short_term_macd=[1.0, 1.1, 1.2],
            short_term_rsi7=[63.0, 64.0, 65.5],
            short_term_rsi14=[60.0, 61.0, 62.0],
            long_term_ema20=145.0,
            long_term_ema50=140.0,
            long_term_atr3=2.5,
            long_term_atr14=3.0,
            long_term_volume_current=1000000.0,
            long_term_volume_avg=950000.0,
            long_term_macd=[0.8, 1.0, 1.2],
            long_term_rsi14=[58.0, 60.0, 62.0],
        )

        result = PromptComposer.compose_market_section([snapshot])

        assert "AAPL.US DATA" in result
        assert "current_price = 150.5" in result
        assert "current_ema20 = 149.0" in result
        assert "Short-term Context" in result
        assert "Longer-term Context" in result

    def test_compose_account_section(self):
        """测试账户信息格式化。"""
        account = AccountOverview(
            account_number="ACC001",
            name="测试账户",
            cash_available=Decimal("10000.50"),
            buying_power=Decimal("10000.50"),
            realized_pnl=Decimal("500.25"),
            return_pct=5.0,
            sharpe_ratio=1.5,
        )

        result = PromptComposer.compose_account_section(account)

        assert "## 账户与持仓信息" in result
        assert "绩效指标" in result
        assert "当前收益率: 5.0%" in result
        assert "夏普率: 1.5" in result
        assert "可用现金: $10000.50" in result

    def test_compose_account_section_with_none_metrics(self):
        """测试绩效指标为 None 的情况。"""
        account = AccountOverview(
            account_number="ACC002",
            name="新账户",
            cash_available=Decimal("5000.0"),
            buying_power=Decimal("5000.0"),
            realized_pnl=Decimal("0"),
            return_pct=None,
            sharpe_ratio=None,
        )

        result = PromptComposer.compose_account_section(account)

        assert "当前收益率: N/A%" in result
        assert "夏普率: N/A" in result

    def test_compose_position_section_empty(self):
        """测试空持仓的情况。"""
        result = PromptComposer.compose_position_section([])

        assert "当前持仓:无" in result
        assert "合计市值:$0" in result
        assert "合计浮盈亏:$0" in result

    def test_compose_position_section_with_data(self):
        """测试有持仓数据的情况。"""
        position = PositionSummary(
            symbol_exchange="AAPL.US",
            side=PositionSide.LONG,
            quantity=100,
            available_quantity=100,
            average_cost=Decimal("145.0"),
            market_price=Decimal("150.0"),
            market_value=Decimal("15000.0"),
            unrealized_pnl=Decimal("500.0"),
            realized_pnl=Decimal("0"),
            profit_target=Decimal("160.0"),
            stop_loss=Decimal("140.0"),
            notes=None,
        )

        result = PromptComposer.compose_position_section([position])

        assert "当前持仓: AAPL.US" in result
        assert "合计市值:$15000.0" in result
        assert "合计浮盈亏:$500.0" in result
        assert "'symbol': 'AAPL.US'" in result
        assert "'quantity': 100" in result
        assert "'entry_price': 145.0" in result
        assert "'current_price': 150.0" in result

    def test_compose_position_section_multiple_positions(self):
        """测试多个持仓的情况。"""
        positions = [
            PositionSummary(
                symbol_exchange="AAPL.US",
                side=PositionSide.LONG,
                quantity=100,
                available_quantity=100,
                average_cost=Decimal("145.0"),
                market_price=Decimal("150.0"),
                market_value=Decimal("15000.0"),
                unrealized_pnl=Decimal("500.0"),
                realized_pnl=Decimal("0"),
                profit_target=Decimal("160.0"),
                stop_loss=Decimal("140.0"),
                notes=None,
            ),
            PositionSummary(
                symbol_exchange="TSLA.US",
                side=PositionSide.LONG,
                quantity=50,
                available_quantity=50,
                average_cost=Decimal("200.0"),
                market_price=Decimal("210.0"),
                market_value=Decimal("10500.0"),
                unrealized_pnl=Decimal("500.0"),
                realized_pnl=Decimal("0"),
                profit_target=Decimal("220.0"),
                stop_loss=Decimal("190.0"),
                notes=None,
            ),
        ]

        result = PromptComposer.compose_position_section(positions)

        assert "AAPL.US 、 TSLA.US" in result
        assert "合计市值:$25500.0" in result
        assert "合计浮盈亏:$1000.0" in result

    def test_compose_full_prompt(self):
        """测试完整 Prompt 组装。"""
        market_snapshot = MarketSnapshot(
            symbol="AAPL.US",
            current_price=150.5,
            current_ema20=149.0,
            current_macd=1.2,
            current_rsi7=65.5,
            short_term_mid_prices=[150.5],
            short_term_ema20=[149.0],
            short_term_macd=[1.2],
            short_term_rsi7=[65.5],
            short_term_rsi14=[62.0],
            long_term_ema20=145.0,
            long_term_ema50=140.0,
            long_term_atr3=2.5,
            long_term_atr14=3.0,
            long_term_volume_current=1000000.0,
            long_term_volume_avg=950000.0,
            long_term_macd=[1.2],
            long_term_rsi14=[62.0],
        )

        account = AccountOverview(
            account_number="ACC001",
            name="测试账户",
            cash_available=Decimal("10000.0"),
            buying_power=Decimal("10000.0"),
            realized_pnl=Decimal("500.0"),
            return_pct=5.0,
            sharpe_ratio=1.5,
        )

        position = PositionSummary(
            symbol_exchange="AAPL.US",
            side=PositionSide.LONG,
            quantity=100,
            available_quantity=100,
            average_cost=Decimal("145.0"),
            market_price=Decimal("150.0"),
            market_value=Decimal("15000.0"),
            unrealized_pnl=Decimal("500.0"),
            realized_pnl=Decimal("0"),
            profit_target=Decimal("160.0"),
            stop_loss=Decimal("140.0"),
            notes=None,
        )

        result = PromptComposer.compose_full_prompt(
            market_snapshots=[market_snapshot],
            account_overview=account,
            position_summaries=[position],
        )

        # 验证所有主要部分都存在
        assert "## 当前所有标的的市场数据" in result
        assert "AAPL.US DATA" in result
        assert "## 账户与持仓信息" in result
        assert "绩效指标" in result
        assert "当前实时仓位与表现" in result
        assert "基于以上数据给出你的交易决策" in result

        # 验证完整性
        assert len(result) > 0
        assert result.count("##") >= 2  # 至少两个主标题
