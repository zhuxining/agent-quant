"""Default trading job runner wiring prompt, agent, and execution layers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from loguru import logger

from quant.core.interfaces import AgentRunner, Notifier, OrderExecutor, SignalRouter
from quant.core.types import PromptPayload
from quant.data_pipeline.market_feed import PromptSnapshotService
from quant.data_pipeline.symbols import SymbolRegistry


@dataclass(slots=True)
class TradingJobRunner:
	"""Callable job that iterates symbols, collects signals, and executes orders."""

	symbol_registry: SymbolRegistry
	snapshot_service: PromptSnapshotService
	agent_runner: AgentRunner
	signal_router: SignalRouter
	order_executor: OrderExecutor
	notifier: Notifier | None = None
	max_symbols: int | None = None

	def __call__(self) -> dict[str, Any]:
		symbols = self._load_symbols()
		executed = 0
		failures: dict[str, str] = {}

		for symbol in symbols:
			try:
				executed += self._process_symbol(symbol)
			except Exception as exc:  # pragma: no cover - runtime specific
				logger.exception(
					"自动交易任务处理 {symbol} 失败: {error}",
					symbol=symbol,
					error=exc,
				)
				failures[symbol] = str(exc)
		return {"processed": len(symbols), "executed": executed, "failures": failures}

	def _load_symbols(self) -> list[str]:
		symbols = self.symbol_registry.list_all()
		if not symbols:
			symbols = self.symbol_registry.refresh()
		if self.max_symbols:
			symbols = symbols[: self.max_symbols]
		return symbols

	def _process_symbol(self, symbol: str) -> int:
		snapshot = self.snapshot_service.build_snapshot(symbol)
		payload = self._build_prompt(symbol, snapshot)
		response = self.agent_runner.generate(payload)
		signal = self.signal_router.route(response.signals)
		if not signal:
			logger.info("无可执行信号 | symbol={symbol}", symbol=symbol)
			return 0

		signal.metadata.setdefault("price", snapshot.get("current_price"))
		snapshot_after = self.order_executor.execute(signal)
		logger.info(
			"自动信号执行完成 | symbol={symbol} side={side} qty={qty} cash={cash:.2f}",
			symbol=symbol,
			side=signal.side,
			qty=signal.quantity,
			cash=snapshot_after.cash,
		)
		if self.notifier:
			self.notifier.notify(
				f"{symbol} 自动交易",
				f"{signal.side} {signal.quantity} @ {signal.metadata.get('price')}",
				tags=["trade", "auto"],
			)
		return 1

	@staticmethod
	def _build_prompt(symbol: str, snapshot: dict[str, Any]) -> PromptPayload:
		content = json.dumps(snapshot, ensure_ascii=False, indent=2)
		return PromptPayload(
			content=content,
			metadata={
				"symbol": symbol,
				"user": content,
			},
		)
