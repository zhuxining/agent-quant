"""Helpers to format backtest reports for presentation."""

from __future__ import annotations

from src.quant.core.types import BacktestReport


class BacktestReporter:
    """Produce textual or HTML representations of backtest results."""

    def summary(self, report: BacktestReport) -> str:
        """Return a one-line summary string."""
        signal_count = int(report.metrics.get("signal_count", 0))
        return (
            f"Backtest from {report.started_at.isoformat()} to {report.ended_at.isoformat()} "
            f"with {signal_count} signals."
        )

    def as_dict(self, report: BacktestReport) -> dict[str, float]:
        """Return metrics as a plain dictionary for API responses."""
        return dict(report.metrics)
