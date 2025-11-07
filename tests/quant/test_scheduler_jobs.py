from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import pytest

from quant.core.types import AgentResponse, PromptPayload, TradeSignal
from quant.data_pipeline.symbols import SymbolRegistry
from quant.scheduler.jobs import QuantScheduler, ScheduledJob
from quant.scheduler.trading import TradingJobRunner


class SpyNotifier:
	def __init__(self) -> None:
		self.messages: list[tuple[str, str, Sequence[str]]] = []

	def notify(self, title: str, message: str, *, tags: Sequence[str] | None = None) -> None:
		self.messages.append((title, message, tuple(tags or ())))


class StubSnapshotService:
	def build_snapshot(self, symbol: str) -> dict[str, Any]:
		return {"symbol": symbol, "current_price": 10.0}


class StubAgentRunner:
	def generate(self, prompt: PromptPayload) -> AgentResponse:
		return AgentResponse(
			raw_text="buy",
			signals=[
				TradeSignal(
					symbol=prompt.metadata["symbol"],
					side="BUY",
					quantity=1,
					confidence=0.9,
					metadata={"timestamp": datetime.now(UTC)},
				)
			],
		)


class StubSignalRouter:
	def route(self, signals: Sequence[TradeSignal]) -> TradeSignal | None:
		return signals[0] if signals else None


class StubOrderExecutor:
	def __init__(self) -> None:
		self.executed: list[TradeSignal] = []

	def execute(self, signal: TradeSignal):
		self.executed.append(signal)
		return type("Snapshot", (), {"cash": 1000.0, "positions": {}, "realized_pnl": 0.0})()


@pytest.mark.asyncio
async def test_quant_scheduler_executes_job_and_notifies() -> None:
	notifier = SpyNotifier()
	scheduler = QuantScheduler(notifier=notifier)
	counter = {"runs": 0}

	def handler() -> None:
		counter["runs"] += 1

	job = ScheduledJob(name="ping", cron="* * * * *", handler=handler)
	scheduler.register(job)

	await scheduler.execute_now("ping")

	assert counter["runs"] == 1
	assert notifier.messages[0][0].startswith("任务 ping")


def test_trading_job_runner_executes_signals(monkeypatch: pytest.MonkeyPatch) -> None:
	registry = SymbolRegistry(seed=["AAPL.US"])
	snapshot_service = StubSnapshotService()
	agent = StubAgentRunner()
	router = StubSignalRouter()
	executor = StubOrderExecutor()
	notifier = SpyNotifier()

	runner = TradingJobRunner(
		symbol_registry=registry,
		snapshot_service=snapshot_service,
		agent_runner=agent,
		signal_router=router,
		order_executor=executor,
		notifier=notifier,
	)

	summary = runner()
	assert summary["processed"] == 1
	assert summary["executed"] == 1
	assert executor.executed[0].symbol == "AAPL.US"
	assert notifier.messages
