"""Integration-style tests for the market data pipeline."""

from __future__ import annotations

import pytest
from loguru import logger

from quant.data_pipeline.indicators import IndicatorService
from quant.data_pipeline.longport_source import LongportMarketDataSource
from quant.data_pipeline.market_feed import MarketDataService, PromptSnapshotService
from quant.data_pipeline.snapshots import SnapshotAssembler
from quant.data_pipeline.talib_calculator import TalibIndicatorCalculator


@pytest.mark.integration
@pytest.mark.parametrize("symbol", ["AAPL.US", "510300.SH"])
def test_longport_market_data_fetch(symbol: str) -> None:
	"""Ensure we can fetch a small window of market data from Longport."""

	data_source = LongportMarketDataSource()
	service = MarketDataService(data_source)

	bars = service.fetch_period(symbol, period="1d", count=5)
	logger.info("{symbol} bars: {bars}", symbol=symbol, bars=bars)

	calculator = TalibIndicatorCalculator()
	indicator_service = IndicatorService(calculator)

	short_indicators = indicator_service.compute(bars)
	logger.info(
		"{symbol} indicator values: {values}",
		symbol=symbol,
		values=short_indicators.values,
	)

	snapshot_service = PromptSnapshotService(
		market_data=service,
		indicator_service=indicator_service,
		assembler=SnapshotAssembler(),
	)

	snapshot = snapshot_service.build_snapshot(symbol)
	logger.info(
		"{symbol} prompt snapshot: {snapshot}",
		symbol=symbol,
		snapshot=snapshot,
	)

	assert len(bars) > 0, f"未能获取到 {symbol} 的行情数据"
	assert bars[-1].close is not None
	assert bars[-1].close > 0
