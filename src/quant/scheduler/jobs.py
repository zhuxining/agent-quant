"""Definitions for recurring quant jobs."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from src.quant.core.interfaces import Notifier

Handler = Callable[[], Awaitable[None] | None]


@dataclass(slots=True)
class ScheduledJob:
	"""Represents a scheduled quant task."""

	name: str
	cron: str
	handler: Handler
	description: str | None = None


class QuantScheduler:
	"""AsyncIO-based scheduler for quant workloads."""

	def __init__(self, *, notifier: Notifier | None = None, timezone: str = "UTC") -> None:
		self._scheduler = AsyncIOScheduler(timezone=timezone)
		self._jobs: dict[str, ScheduledJob] = {}
		self._notifier = notifier

	def register(self, job: ScheduledJob) -> None:
		"""Register or replace a job."""
		trigger = CronTrigger.from_crontab(job.cron)
		self._jobs[job.name] = job

		if self._scheduler.get_job(job.name):
			self._scheduler.remove_job(job.name)
		self._scheduler.add_job(
			self._execute_job,
			trigger=trigger,
			id=job.name,
			kwargs={"job": job},
			replace_existing=True,
		)

	def list_jobs(self) -> list[ScheduledJob]:
		"""Return registered jobs."""
		return list(self._jobs.values())

	def start(self) -> None:
		"""Start the underlying APScheduler."""
		if not self._scheduler.running:
			self._scheduler.start()

	def shutdown(self) -> None:
		"""Shutdown the scheduler."""
		if self._scheduler.running:
			self._scheduler.shutdown(wait=False)

	async def execute_now(self, job_name: str) -> None:
		"""Execute a registered job immediately (useful for tests/manual runs)."""
		job = self._jobs.get(job_name)
		if job is None:
			msg = f"Job {job_name} 未注册"
			raise KeyError(msg)
		started = datetime.now(UTC)
		try:
			await self._run_handler(job)
		except Exception as exc:
			self._notify(job, started, "failed", str(exc))
			raise
		else:
			self._notify(job, started, "completed", "manual trigger")

	async def _execute_job(self, job: ScheduledJob) -> None:
		started = datetime.now(UTC)
		try:
			await self._run_handler(job)
		except Exception as exc:  # pragma: no cover - runtime specific
			logger.exception("Scheduled job {name} failed: {error}", name=job.name, error=exc)
			self._notify(job, started, "failed", str(exc))
		else:
			duration = (datetime.now(UTC) - started).total_seconds()
			self._notify(job, started, "completed", f"{duration:.2f}s")

	async def _run_handler(self, job: ScheduledJob) -> None:
		result = job.handler()
		if inspect.isawaitable(result):
			await result

	def _notify(
		self,
		job: ScheduledJob,
		started: datetime,
		status: str,
		message: str,
	) -> None:
		if not self._notifier:
			return
		title = f"任务 {job.name} {status}"
		body = f"{message} | 启动: {started.isoformat()}"
		self._notifier.notify(title, body, tags=["scheduler", job.name])
