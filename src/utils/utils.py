"""Shared utility helpers for the quant stack."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
	"""Return the current UTC timestamp with timezone information."""
	return datetime.now(UTC)
