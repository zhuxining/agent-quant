"""Account service layer coordinating repository operations."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime

from quant.core.interfaces import AccountRepository
from quant.core.types import AccountSnapshot, TradeSignal


class AccountService:
    """Applies trade signals to the stored account snapshot."""

    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    def get_snapshot(self) -> AccountSnapshot:
        """Return the latest stored snapshot."""
        return self._repository.load()

    def apply_signal(self, signal: TradeSignal, execution_price: float) -> AccountSnapshot:
        """Update the account snapshot according to the trade signal."""
        snapshot = deepcopy(self._repository.load())
        quantity = signal.quantity

        positions = snapshot.positions
        if signal.side.upper() == "BUY":
            snapshot.cash -= execution_price * quantity
            positions[signal.symbol] = positions.get(signal.symbol, 0.0) + quantity
        elif signal.side.upper() == "SELL":
            snapshot.cash += execution_price * quantity
            positions[signal.symbol] = positions.get(signal.symbol, 0.0) - quantity
        else:
            return snapshot

        snapshot.timestamp = datetime.utcnow()
        self._repository.save(snapshot)
        return snapshot
