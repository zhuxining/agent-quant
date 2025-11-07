"""Notification adapters used by scheduled jobs."""

from __future__ import annotations

import json
import smtplib
from collections.abc import Sequence
from email.message import EmailMessage
from typing import Any
from urllib import error, request

from loguru import logger


class ConsoleNotifier:
	"""Simple notifier that logs messages to the console."""

	def notify(self, title: str, message: str, *, tags: Sequence[str] | None = None) -> None:
		"""Log the notification content."""
		logger.bind(component="notifier", tags=list(tags or [])).info("%s - %s", title, message)


class WebhookNotifier:
	"""Dispatch notifications to an HTTP endpoint via POST."""

	def __init__(self, url: str, *, timeout: float = 5.0) -> None:
		self._url = url
		self._timeout = timeout

	def notify(
		self,
		title: str,
		message: str,
		*,
		tags: Sequence[str] | None = None,
		extra: dict[str, Any] | None = None,
	) -> None:
		payload = {
			"title": title,
			"message": message,
			"tags": list(tags or []),
		}
		if extra:
			payload["extra"] = extra
		data = json.dumps(payload).encode("utf-8")
		req = request.Request(
			self._url,
			data=data,
			headers={"Content-Type": "application/json"},
			method="POST",
		)
		try:
			with request.urlopen(req, timeout=self._timeout):
				return
		except error.URLError as exc:  # pragma: no cover - network dependent
			logger.warning("Webhook notification failed: %s", exc)


class EmailNotifier:
	"""Send notifications through SMTP."""

	def __init__(
		self,
		host: str,
		port: int,
		*,
		username: str | None = None,
		password: str | None = None,
		use_tls: bool = True,
		from_address: str,
		to_addresses: Sequence[str],
		timeout: float = 10.0,
	) -> None:
		if not to_addresses:
			msg = "Email notifier requires at least one recipient"
			raise ValueError(msg)
		self._host = host
		self._port = port
		self._username = username
		self._password = password
		self._use_tls = use_tls
		self._from = from_address
		self._to = list(to_addresses)
		self._timeout = timeout

	def notify(
		self,
		title: str,
		message: str,
		*,
		tags: Sequence[str] | None = None,
	) -> None:
		email = EmailMessage()
		email["Subject"] = title
		email["From"] = self._from
		email["To"] = ", ".join(self._to)
		body = f"{message}\n\nTags: {', '.join(tags or [])}"
		email.set_content(body)

		try:
			with smtplib.SMTP(self._host, self._port, timeout=self._timeout) as client:
				if self._use_tls:
					client.starttls()
				if self._username and self._password:
					client.login(self._username, self._password)
				client.send_message(email)
		except Exception as exc:  # pragma: no cover - external service
			logger.warning("Email notification failed: %s", exc)
