"""Definitions for recurring quant jobs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(slots=True)
class ScheduledJob:
    """Represents a scheduled quant task."""

    name: str
    cron: str
    handler: Callable[[], None]


class QuantScheduler:
    """Minimal registry for quant background jobs."""

    def __init__(self) -> None:
        self._jobs: dict[str, ScheduledJob] = {}

    def register(self, job: ScheduledJob) -> None:
        """Register or replace a job."""
        self._jobs[job.name] = job

    def list_jobs(self) -> list[ScheduledJob]:
        """Return registered jobs."""
        return list(self._jobs.values())
