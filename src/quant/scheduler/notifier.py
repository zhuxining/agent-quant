"""Notification adapters used by scheduled jobs."""

from __future__ import annotations

from collections.abc import Sequence

from loguru import logger


class ConsoleNotifier:
    """Simple notifier that logs messages to the console."""

    def notify(self, title: str, message: str, *, tags: Sequence[str] | None = None) -> None:
        """Log the notification content."""
        logger.bind(component="notifier", tags=list(tags or [])).info("%s - %s", title, message)
