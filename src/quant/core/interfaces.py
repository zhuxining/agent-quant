"""Protocol definitions for the quant orchestration pipeline."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Protocol, runtime_checkable

from .types import (
	AccountSnapshot,
	AgentResponse,
	BacktestReport,
	IndicatorSnapshot,
	MarketBar,
	PromptPayload,
	TradeSignal,
)


@runtime_checkable
class MarketDataSource(Protocol):
	"""Provides access to historical or real-time market data."""

	def fetch_ohlcv(
		self,
		symbol: str,
		start: datetime,
		end: datetime,
		*,
		interval: str = "1d",
	) -> Sequence[MarketBar]: ...


@runtime_checkable
class IndicatorCalculator(Protocol):
	"""Computes derived features from market data."""

	def compute(self, bars: Sequence[MarketBar]) -> IndicatorSnapshot: ...


@runtime_checkable
class AccountRepository(Protocol):
	"""Persists and retrieves account snapshots."""

	def load(self) -> AccountSnapshot: ...

	def save(self, snapshot: AccountSnapshot) -> None: ...


@runtime_checkable
class PromptBuilder(Protocol):
	"""Builds Agent prompts from market and account context."""

	def build(
		self,
		symbol: str,
		bars: Sequence[MarketBar],
		snapshot: AccountSnapshot,
	) -> PromptPayload: ...


@runtime_checkable
class AgentRunner(Protocol):
	"""Executes Agent calls and aggregates their responses."""

	def generate(self, prompt: PromptPayload) -> AgentResponse: ...


@runtime_checkable
class SignalValidator(Protocol):
	"""Validates Agent responses and extracts executable signals."""

	def validate(self, response: AgentResponse) -> Sequence[TradeSignal]: ...


@runtime_checkable
class SignalRouter(Protocol):
	"""Selects or aggregates signals ahead of execution."""

	def route(self, signals: Sequence[TradeSignal]) -> TradeSignal | None: ...


@runtime_checkable
class OrderExecutor(Protocol):
	"""Executes trade signals and returns the updated account snapshot."""

	def execute(self, signal: TradeSignal) -> AccountSnapshot: ...


@runtime_checkable
class BacktestEngine(Protocol):
	"""Runs quantitative backtests over a sequence of signals."""

	def run(self, signals: Iterable[TradeSignal]) -> BacktestReport: ...


@runtime_checkable
class Notifier(Protocol):
	"""Dispatches notifications to external channels."""

	def notify(self, title: str, message: str, *, tags: Sequence[str] | None = None) -> None: ...
