"""Utility functions for converting Agent output to trade signals."""

from __future__ import annotations

import json
from collections.abc import Iterable

from src.quant.core.types import TradeSignal


def parse_trade_suggestions(payload: str | bytes | None) -> list[TradeSignal]:
	"""Parse Agent JSON output into a list of ``TradeSignal`` objects.

	The Agent is expected to return a JSON array of objects containing
	``symbol``, ``action``/``side``, ``quantity`` and optionally ``confidence``.
	Invalid entries are ignored to keep the pipeline resilient.
	"""

	if not payload:
		return []
	if isinstance(payload, bytes):
		payload = payload.decode("utf-8", errors="ignore")
	try:
		parsed = json.loads(payload)
	except json.JSONDecodeError:
		return []

	if isinstance(parsed, dict):
		parsed = [parsed]
	if not isinstance(parsed, Iterable):
		return []

	signals: list[TradeSignal] = []
	for item in parsed:
		if not isinstance(item, dict):
			continue
		symbol = item.get("symbol") or item.get("ticker")
		if not symbol:
			continue
		side = (item.get("action") or item.get("side") or "HOLD").upper()
		quantity = item.get("quantity") or item.get("size") or 0
		try:
			quantity = float(quantity)
		except (TypeError, ValueError):
			continue
		confidence = item.get("confidence")
		try:
			confidence = float(confidence) if confidence is not None else 0.0
		except (TypeError, ValueError):
			confidence = 0.0
		signals.append(
			TradeSignal(
				symbol=str(symbol),
				side=side,
				quantity=quantity,
				confidence=confidence,
				metadata={"raw": item},
			)
		)
	return signals


__all__ = ["parse_trade_suggestions"]
