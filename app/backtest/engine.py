"""回测引擎: 遍历历史日期, 调用 Workflow 执行策略。"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid7

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.backtest.equity import EquityCurve, EquityPoint
from app.backtest.vectorized_technical import (
    VectorizedBacktestConfig as VectorizedConfig,
    VectorizedBacktestEngine,
)
from app.data_feed.technical_indicator import TechnicalIndicatorFeed
from app.models import (
    BacktestDailyEquity,
    BacktestRun,
    BacktestStatus,
    VirtualTradeAccount,
)
from app.models.backtest import (
    BacktestMode,
)
from app.paper_trading.position import list_position_overviews
from app.workflow.nof1_workflow import run_nof1_workflow

# 默认配置
DEFAULT_INITIAL_CAPITAL = Decimal("1000000")
DEFAULT_INTERVAL_DAYS = 1


@dataclass
class BacktestConfig:
    """回测配置。"""

    name: str
    symbols: list[str]
    start_date: date
    end_date: date
    initial_capital: Decimal = DEFAULT_INITIAL_CAPITAL
    interval_days: int = DEFAULT_INTERVAL_DAYS
    mode: BacktestMode = BacktestMode.VIRTUAL


@dataclass
class BacktestResult:
    """回测结果。"""

    run_id: UUID
    equity_curve: EquityCurve
    total_return: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown: float | None = None
    error_message: str | None = None


class BacktestEngine:
    """回测引擎。

    支持两种模式：
    1. VIRTUAL - 遍历日期，调用 Workflow（Multi-Agent）
    2. VECTORIZED - 向量化技术面回测（快速验证）

    遍历指定日期范围, 记录每日净值并生成绩效报告。
    """

    def __init__(self, config: BacktestConfig, session: AsyncSession) -> None:
        self.config = config
        self.session = session
        self.equity_curve = EquityCurve()
        self._backtest_run: BacktestRun | None = None
        self._account: VirtualTradeAccount | None = None
        self._feed = TechnicalIndicatorFeed()

        if config.mode == BacktestMode.VECTORIZED:
            vectorized_config = VectorizedConfig(
                mode=BacktestMode.VECTORIZED,
                symbols=config.symbols,
                start_date=config.start_date,
                end_date=config.end_date,
                initial_capital=config.initial_capital,
            )
            self._vectorized_engine = VectorizedBacktestEngine(vectorized_config)

    async def run(self) -> BacktestResult:
        """执行回测。"""
        if self.config.mode == BacktestMode.VECTORIZED:
            return await self._run_vectorized_backtest()

        return await self._run_virtual_backtest()

    async def _run_virtual_backtest(self) -> BacktestResult:
        """执行虚拟回测（使用 Workflow）。"""
        try:
            await self._initialize()
            logger.info(f"开始回测: {self.config.name} (VIRTUAL 模式)")
            logger.info(
                f"日期范围: {self.config.start_date} → {self.config.end_date}, "
                f"间隔: {self.config.interval_days}天"
            )

            await self._update_status(BacktestStatus.RUNNING)

            trading_days = list(self._iter_trading_days())
            logger.info(f"共 {len(trading_days)} 个决策点")

            for i, sim_date in enumerate(trading_days):
                logger.info(f"[{i + 1}/{len(trading_days)}] 模拟日期: {sim_date}")

                await self._run_workflow_for_date(sim_date)
                await self._record_equity(sim_date)

            result = await self._finalize()
            logger.info(f"回测完成: 总收益率 {result.total_return:.2f}%")
            return result

        except Exception as e:
            logger.error(f"回测失败: {e}")
            await self._update_status(BacktestStatus.FAILED, error_message=str(e))
            raise

    async def _run_vectorized_backtest(self) -> BacktestResult:
        """执行向量化回测。"""
        try:
            await self._initialize_vectorized()
            logger.info(f"开始回测: {self.config.name} (VECTORIZED 模式)")
            logger.info(f"日期范围: {self.config.start_date} → {self.config.end_date}")

            await self._update_status(BacktestStatus.RUNNING)

            _result_df, metrics = self._vectorized_engine.run()

            logger.info(f"回测完成: 总收益率 {metrics.total_return:.2f}%")
            return BacktestResult(
                run_id=self._backtest_run.id,
                equity_curve=self.equity_curve,
                total_return=float(metrics.total_return),
                sharpe_ratio=float(metrics.sharpe_ratio) if metrics.sharpe_ratio else None,
                max_drawdown=float(metrics.max_drawdown),
            )

        except Exception as e:
            logger.error(f"回测失败: {e}")
            await self._update_status(BacktestStatus.FAILED, error_message=str(e))
            raise

    async def _initialize_vectorized(self) -> None:
        """初始化向量化回测记录。"""
        import json

        account_number = f"VT-{str(uuid7())[:12].upper()}"

        self._backtest_run = BacktestRun(
            name=self.config.name,
            symbols=json.dumps(self.config.symbols),
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            interval_days=0,
            initial_capital=self.config.initial_capital,
            account_number=account_number,
            status=BacktestStatus.PENDING,
        )
        self.session.add(self._backtest_run)
        await self.session.flush()

    async def _initialize(self) -> None:
        """初始化回测记录和专用账户。"""
        import json

        # 创建回测运行记录
        account_number = f"BT-{str(uuid7())[:12].upper()}"

        self._backtest_run = BacktestRun(
            name=self.config.name,
            symbols=json.dumps(self.config.symbols),
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            interval_days=self.config.interval_days,
            initial_capital=self.config.initial_capital,
            account_number=account_number,
            status=BacktestStatus.PENDING,
        )
        self.session.add(self._backtest_run)

        # 创建回测专用账户
        self._account = VirtualTradeAccount(
            name=f"回测账户-{self.config.name}",
            account_number=account_number,
            balance=self.config.initial_capital,
            buying_power=self.config.initial_capital,
            realized_pnl=Decimal("0"),
            is_active=True,
            description=f"回测专用: {self.config.start_date} ~ {self.config.end_date}",
        )
        self.session.add(self._account)
        await self.session.commit()

        # 记录初始净值
        initial_point = EquityPoint(
            date=self.config.start_date,
            equity=self.config.initial_capital,
            cash=self.config.initial_capital,
            market_value=Decimal("0"),
        )
        self.equity_curve.add(initial_point)

    def _iter_trading_days(self):
        """生成决策日期序列。

        TODO: 接入交易日历过滤非交易日
        """
        current = self.config.start_date
        while current <= self.config.end_date:
            # 跳过周末 (简化版本, 后续可接入交易日历)
            if current.weekday() < 5:
                yield current
            current += timedelta(days=self.config.interval_days)

    async def _run_workflow_for_date(self, sim_date: date) -> None:
        """在指定日期运行 Workflow。"""
        assert self._account is not None, "账户未初始化"
        sim_datetime = datetime.combine(sim_date, datetime.max.time())
        await run_nof1_workflow(
            symbols=self.config.symbols,
            account_number=self._account.account_number,
            end_date=sim_datetime,
            debug_mode=False,
        )

    async def _record_equity(self, sim_date: date) -> None:
        """记录当日净值。"""
        assert self._account is not None, "账户未初始化"
        assert self._backtest_run is not None, "回测记录未初始化"

        # 刷新账户数据
        await self.session.refresh(self._account)

        # 计算持仓市值
        market_value = await self._calculate_market_value(sim_date)
        equity = self._account.balance + market_value

        # 添加到曲线
        point = EquityPoint(
            date=sim_date,
            equity=equity,
            cash=self._account.balance,
            market_value=market_value,
        )
        self.equity_curve.add(point)

        # 保存到数据库
        daily_equity = BacktestDailyEquity(
            backtest_run_id=self._backtest_run.id,
            trade_date=sim_date,
            equity=equity,
            cash=self._account.balance,
            market_value=market_value,
            daily_return=point.daily_return,
        )
        self.session.add(daily_equity)
        await self.session.flush()

    async def _calculate_market_value(self, sim_date: date) -> Decimal:
        """计算持仓市值。"""
        assert self._account is not None, "账户未初始化"

        positions = await list_position_overviews(
            self.session,
            account_number=self._account.account_number,
        )

        total_value = Decimal("0")
        sim_datetime = datetime.combine(sim_date, datetime.max.time())

        for pos in positions:
            if pos.quantity <= 0:
                continue
            # 获取当日收盘价
            price = self._feed.get_latest_price(pos.symbol_exchange, end_date=sim_datetime)
            if price:
                total_value += price * Decimal(pos.quantity)
            elif pos.market_price:
                # 回退到记录的市场价格
                total_value += pos.market_price * Decimal(pos.quantity)

        return total_value

    async def _update_status(
        self,
        status: BacktestStatus,
        error_message: str | None = None,
    ) -> None:
        """更新回测状态。"""
        assert self._backtest_run is not None, "回测记录未初始化"
        self._backtest_run.status = status
        if error_message:
            self._backtest_run.error_message = error_message
        await self.session.commit()

    async def _finalize(self) -> BacktestResult:
        """完成回测, 计算绩效指标。"""
        assert self._backtest_run is not None, "回测记录未初始化"

        # 计算指标
        total_return = self.equity_curve.total_return
        final_equity = self.equity_curve.final_equity

        # TODO: 接入 quantstats 计算夏普比率、最大回撤
        sharpe_ratio = None
        max_drawdown = None

        # 更新回测记录
        self._backtest_run.status = BacktestStatus.COMPLETED
        self._backtest_run.final_equity = final_equity
        self._backtest_run.total_return = total_return
        self._backtest_run.sharpe_ratio = sharpe_ratio
        self._backtest_run.max_drawdown = max_drawdown
        await self.session.commit()

        return BacktestResult(
            run_id=self._backtest_run.id,
            equity_curve=self.equity_curve,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
        )


__all__ = [
    "BacktestConfig",
    "BacktestEngine",
    "BacktestResult",
]
