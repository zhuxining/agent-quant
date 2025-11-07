"""Indicator calculation orchestration."""

from __future__ import annotations

from collections.abc import Sequence

from src.quant.core.interfaces import IndicatorCalculator
from src.quant.core.types import IndicatorSnapshot, MarketBar


class IndicatorService:
	"""Delegates indicator calculation to the configured calculator."""

	def __init__(self, calculator: IndicatorCalculator) -> None:
		self._calculator = calculator

	def compute(self, bars: Sequence[MarketBar]) -> IndicatorSnapshot:
		"""Compute indicators for the provided price bars."""
		return self._calculator.compute(bars)
