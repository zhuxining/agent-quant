from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from quant.backtest.engine import BacktestEngineConfig, QuantstatsBacktestEngine
from quant.core.types import TradeSignal


def test_quantstats_engine_generates_report(tmp_path: Path) -> None:
	config = BacktestEngineConfig(
		initial_capital=10_000.0,
		report_dir=tmp_path,
		render_report=False,
	)
	engine = QuantstatsBacktestEngine(config)
	signals = [
		TradeSignal(
			symbol="AAPL.US",
			side="BUY",
			quantity=10,
			confidence=0.8,
			metadata={
				"price": 100.0,
				"timestamp": datetime.now(UTC) - timedelta(days=2),
			},
		),
		TradeSignal(
			symbol="AAPL.US",
			side="SELL",
			quantity=10,
			confidence=0.9,
			metadata={
				"price": 110.0,
				"timestamp": datetime.now(UTC) - timedelta(days=1),
			},
		),
	]

	report = engine.run(signals)

	assert report.metrics["signal_count"] == 2
	assert report.metrics["total_return"] > 0
	assert "html_report" in report.artifacts
	assert Path(report.artifacts["html_report"]).exists()
