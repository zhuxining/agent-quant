from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quant.core.types import (
	AccountSnapshot,
	AgentResponse,
	IndicatorSnapshot,
	MarketBar,
	PromptPayload,
	TradeSignal,
)
from quant.execution.order_executor import OrderExecutorService
from quant.execution.signal_router import ConfidenceWeightedRouter
from quant.prompting.agents import AgentCoordinator
from quant.prompting.builder import PromptBuilderService


class SpyLogger:
	def __init__(self) -> None:
		self.prompts: list[PromptPayload] = []
		self.responses: list[AgentResponse] = []
		self.signals: list[TradeSignal] = []
		self.snapshots: list[AccountSnapshot] = []

	def log_prompt(self, prompt: PromptPayload) -> None:
		self.prompts.append(prompt)

	def log_agent_response(self, response: AgentResponse) -> None:
		self.responses.append(response)

	def log_signal(self, signal: TradeSignal) -> None:
		self.signals.append(signal)

	def log_execution(self, snapshot: AccountSnapshot) -> None:
		self.snapshots.append(snapshot)


@pytest.fixture()
def spy_logger() -> SpyLogger:
	return SpyLogger()


def test_prompt_builder_logs_payload(spy_logger: SpyLogger) -> None:
	builder = PromptBuilderService(logger=spy_logger)
	bars = [
		MarketBar(
			symbol="AAPL.US",
			timestamp=datetime.now(UTC),
			open=100,
			high=105,
			low=98,
			close=103,
			volume=1_000,
		)
	]
	indicators = IndicatorSnapshot(
		symbol="AAPL.US",
		timestamp=datetime.now(UTC),
		values={"ema": 101},
	)
	account = AccountSnapshot(cash=10_000.0)

	payload = builder.build("AAPL.US", bars, indicators, account)
	assert spy_logger.prompts == [payload]


class _FakeRunner:
	def __init__(self, response: AgentResponse) -> None:
		self._response = response

	def generate(self, prompt: PromptPayload) -> AgentResponse:
		return self._response


def test_agent_coordinator_logs_prompt_and_response(spy_logger: SpyLogger) -> None:
	response = AgentResponse(raw_text="ok")
	coordinator = AgentCoordinator([_FakeRunner(response)], logger=spy_logger)
	prompt = PromptPayload(content="trade", metadata={"symbol": "AAPL.US"})

	result = coordinator.gather(prompt)

	assert result == [response]
	assert spy_logger.prompts == [prompt]
	assert spy_logger.responses == [response]


def test_confidence_router_logs_selection(spy_logger: SpyLogger) -> None:
	router = ConfidenceWeightedRouter(logger=spy_logger)
	signals = [
		TradeSignal(symbol="AAPL.US", side="BUY", quantity=1, confidence=0.5),
		TradeSignal(symbol="TSLA.US", side="SELL", quantity=0.5, confidence=0.9),
	]

	selected = router.route(signals)

	assert selected is signals[1]
	assert spy_logger.signals == [signals[1]]


def test_order_executor_logs_signal_and_snapshot(spy_logger: SpyLogger) -> None:
	class _StubAccountService:
		def __init__(self, snapshot: AccountSnapshot) -> None:
			self._snapshot = snapshot
			self.applied: list[tuple[TradeSignal, float | None]] = []

		def apply_signal(
			self,
			signal: TradeSignal,
			execution_price: float | None,
		) -> AccountSnapshot:
			self.applied.append((signal, execution_price))
			return self._snapshot

	snapshot = AccountSnapshot(cash=5_000.0)
	account_service = _StubAccountService(snapshot)
	executor = OrderExecutorService(account_service, logger=spy_logger)
	signal = TradeSignal(
		symbol="AAPL.US",
		side="BUY",
		quantity=1,
		confidence=0.8,
		metadata={"price": 123.45},
	)

	result = executor.execute(signal)

	assert result is snapshot
	assert account_service.applied == [(signal, 123.45)]
	assert spy_logger.signals == [signal]
	assert spy_logger.snapshots == [snapshot]
