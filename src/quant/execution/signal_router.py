"""Strategies for aggregating Agent trade signals."""

from __future__ import annotations

from collections.abc import Sequence

from quant.core.types import TradeSignal


class ConfidenceWeightedRouter:
    """Pick the signal with the highest confidence score."""

    def route(self, signals: Sequence[TradeSignal]) -> TradeSignal | None:
        """Return the top signal or None when no signals are provided."""
        if not signals:
            return None
        return max(signals, key=lambda signal: signal.confidence)
