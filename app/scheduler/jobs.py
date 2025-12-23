"""调度任务定义。

使用 APScheduler 实现后台定时任务:
- nof1_workflow_job: 每小时运行一次 NOF1 工作流
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from app.workflow.nof1_workflow import run_nof1_workflow

# 创建全局调度器实例
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def nof1_workflow_job() -> None:
    """NOF1 工作流定时任务。"""
    logger.info("⏰ Scheduler: Starting NOF1 workflow job")
    try:
        result = await run_nof1_workflow()
        logger.success(f"✅ Scheduler: NOF1 workflow completed: {result}")
    except Exception as e:
        logger.error(f"❌ Scheduler: NOF1 workflow failed: {e}")


def start_scheduler() -> None:
    """启动调度器并注册任务。"""
    from datetime import datetime

    # 注册 NOF1 工作流任务: 立即执行一次, 然后每小时执行一次
    scheduler.add_job(
        nof1_workflow_job,
        trigger=IntervalTrigger(hours=1),
        id="nof1_workflow_hourly",
        name="NOF1 Workflow (Hourly)",
        next_run_time=datetime.now(),
        replace_existing=True,
    )

    scheduler.start()
    logger.info("🚀 Scheduler started: NOF1 workflow job will run immediately and then hourly")


def stop_scheduler() -> None:
    """停止调度器。"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("🛑 Scheduler stopped")


__all__ = [
    "nof1_workflow_job",
    "scheduler",
    "start_scheduler",
    "stop_scheduler",
]
