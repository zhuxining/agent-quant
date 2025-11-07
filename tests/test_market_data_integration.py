"""Integration-style tests for the market data pipeline."""

from __future__ import annotations

import json

import pytest
from loguru import logger

from src.core.config import settings
from src.quant.agents import create_default_agent_runner
from src.quant.core.types import PromptPayload
from src.quant.data_pipeline.indicators import IndicatorService
from src.quant.data_pipeline.longport_source import LongportMarketDataSource
from src.quant.data_pipeline.market_feed import MarketDataService, PromptSnapshotService
from src.quant.data_pipeline.snapshots import SnapshotAssembler
from src.quant.data_pipeline.talib_calculator import TalibIndicatorCalculator


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


@pytest.mark.integration
def test_deepseek_prompt_generation(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Fetch 510300.SH snapshot, build a prompt, call DeepSeek, and print the output."""

	if not settings.DEEPSEEK_API_KEY:
		pytest.skip("缺少 DeepSeek API Key，跳过 DeepSeek 调用测试")

	try:
		data_source = LongportMarketDataSource()
	except Exception as exc:  # pragma: no cover - environment specific
		pytest.skip(f"Longport 配置缺失: {exc}")

	service = MarketDataService(data_source)
	calculator = TalibIndicatorCalculator()
	indicator_service = IndicatorService(calculator)
	snapshot_service = PromptSnapshotService(
		market_data=service,
		indicator_service=indicator_service,
		assembler=SnapshotAssembler(),
	)

	snapshot = snapshot_service.build_snapshot("510300.SH")
	user_prompt = "请根据以下市场快照评估交易机会:\n" + json.dumps(
		snapshot,
		ensure_ascii=False,
		indent=2,
	)
	system_prompt = "你是一名量化交易助手，请基于提供的行情快照给出清晰的交易建议。"
	payload = PromptPayload(
		content=user_prompt,
		metadata={"system": system_prompt, "user": user_prompt},
	)

	runner = create_default_agent_runner()
	response = runner.generate(payload)
	print("DeepSeek response:", response.raw_text)
	if response.metadata.get("error"):
		pytest.skip(f"DeepSeek 调用失败: {response.metadata['error']}")
	assert response.raw_text, "DeepSeek 未返回结果"
