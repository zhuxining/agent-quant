"""Strategies for aggregating Agent trade signals."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from src.quant.core.types import TradeSignal

if TYPE_CHECKING:
	from src.quant.execution.logger import ExecutionLogger


class ConfidenceWeightedRouter:
	"""Pick the signal with the highest confidence score."""

	def __init__(self, *, logger: ExecutionLogger | None = None) -> None:
		self._logger = logger

	def route(self, signals: Sequence[TradeSignal]) -> TradeSignal | None:
		"""Return the top signal or None when no signals are provided."""
		if not signals:
			return None
		selected = max(signals, key=lambda signal: signal.confidence)
		if self._logger:
			self._logger.log_signal(selected)
		return selected
