"""Centralized logging helpers for Agent interactions."""

from __future__ import annotations

from loguru import logger

from src.quant.core.types import AccountSnapshot, AgentResponse, PromptPayload, TradeSignal


class ExecutionLogger:
    """Thin wrapper around Loguru for structured logging."""

    def log_prompt(self, prompt: PromptPayload) -> None:
        """Log the prompt content and metadata."""
        logger.bind(component="prompt").info(
            "Prompt dispatched",
            payload=prompt.metadata,
            content=prompt.content,
        )

    def log_agent_response(self, response: AgentResponse) -> None:
        """Log the raw Agent response."""
        logger.bind(component="agent").info(
            "Agent response received", metadata=response.metadata, latency_ms=response.latency_ms
        )

    def log_signal(self, signal: TradeSignal) -> None:
        """Log the final trade signal."""
        logger.bind(component="signal").info(
            "Signal selected",
            symbol=signal.symbol,
            side=signal.side,
            quantity=signal.quantity,
            confidence=signal.confidence,
        )

    def log_execution(self, snapshot: AccountSnapshot) -> None:
        """Log the account snapshot after execution."""
        positions_payload = {
            symbol: position.as_dict()
            for symbol, position in snapshot.positions.items()
        }
        logger.bind(component="execution").info(
            "Account updated",
            cash=snapshot.cash,
            positions=positions_payload,
            realized_pnl=snapshot.realized_pnl,
            timestamp=snapshot.timestamp.isoformat(),
        )
