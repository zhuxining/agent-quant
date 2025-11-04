"""Backtest engine adapters."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from quant.core.types import BacktestReport, TradeSignal


class QuantstatsBacktestEngine:
    """Placeholder backtest engine that records invocation metadata."""

    def run(self, signals: Iterable[TradeSignal]) -> BacktestReport:
        """Return a stub report while the full pipeline is being implemented."""
        consumed: list[TradeSignal] = list(signals)
        now = datetime.utcnow()
        return BacktestReport(
            started_at=now,
            ended_at=now,
            metrics={"signal_count": float(len(consumed))},
            artifacts={},
        )
