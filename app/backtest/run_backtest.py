#!/usr/bin/env python
"""回测运行脚本。

使用方法:
    uv run python -m app.backtest.run_backtest

可选参数通过修改下方配置调整。
"""

import asyncio
from datetime import date
from decimal import Decimal

from loguru import logger

from app.backtest import BacktestConfig, BacktestEngine, BacktestReporter
from app.core.db import async_session_maker, create_db_and_tables

# ==================== 回测配置 ====================

BACKTEST_CONFIG = BacktestConfig(
    name="NOF1策略回测",
    symbols=["159300.SZ"],  # 沪深300 ETF
    start_date=date(2025, 11, 19),
    end_date=date(2025, 12, 5),
    initial_capital=Decimal("100000"),
    interval_days=1,  # 每 N 天决策一次
)

# 是否生成 HTML 报告
GENERATE_HTML_REPORT = True
HTML_REPORT_PATH = "tmp/backtest_report.html"

# ==================== 回测执行 ====================


async def main() -> None:
    """执行回测主函数。"""
    # 确保数据库表存在
    await create_db_and_tables()

    config = BACKTEST_CONFIG

    logger.info("=" * 60)
    logger.info(f"回测名称: {config.name}")
    logger.info(f"标的: {config.symbols}")
    logger.info(f"日期范围: {config.start_date} → {config.end_date}")
    logger.info(f"初始资金: {config.initial_capital}")
    logger.info(f"决策间隔: {config.interval_days} 天")
    logger.info("=" * 60)

    async with async_session_maker() as session:
        engine = BacktestEngine(config=config, session=session)
        result = await engine.run()

    logger.info("=" * 60)
    logger.info("回测完成!")
    logger.info(f"Run ID: {result.run_id}")

    if result.total_return is not None:
        logger.info(f"总收益率: {result.total_return:.2f}%")
    else:
        logger.info("总收益率: N/A")

    # 生成报告
    reporter = BacktestReporter(result.equity_curve)
    reporter.print_summary()

    if GENERATE_HTML_REPORT:
        try:
            report_path = reporter.generate_html_report(
                output_path=HTML_REPORT_PATH,
                title=config.name,
            )
            logger.info(f"HTML 报告已生成: {report_path}")
        except ImportError:
            logger.warning("quantstats 未安装, 跳过 HTML 报告生成")
        except Exception as e:
            logger.error(f"生成 HTML 报告失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
