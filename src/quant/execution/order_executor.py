"""Order execution service coordinating with the account layer."""

from __future__ import annotations

from quant.accounts.services import AccountService
from quant.core.event_bus import EventBus
from quant.core.types import AccountSnapshot, TradeSignal


class OrderExecutorService:
    """Execute signals through the AccountService and emit lifecycle events."""

    def __init__(self, account_service: AccountService, event_bus: EventBus | None = None) -> None:
        self._account_service = account_service
        self._event_bus = event_bus

    def execute(self, signal: TradeSignal) -> AccountSnapshot:
        """Execute a trade signal and broadcast the outcome."""
        execution_price = float(signal.metadata.get("price") or 0.0)
        snapshot = self._account_service.apply_signal(signal, execution_price)

        if self._event_bus:
            self._event_bus.emit(
                "order.executed",
                {
                    "signal": signal,
                    "snapshot": snapshot,
                },
            )
        return snapshot
