"""Domain models for account state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Position:
    """Represents a single open position."""

    symbol: str
    quantity: float
    avg_price: float

    def market_value(self, last_price: float) -> float:
        """Return position market value."""
        return last_price * self.quantity


@dataclass(slots=True)
class Account:
    """Represents an investing account with cash and positions."""

    account_id: str
    cash: float = 0.0
    positions: dict[str, Position] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def equity(self, pricing: dict[str, float]) -> float:
        """Return current equity using provided pricing snapshot."""
        holdings = sum(
            position.market_value(pricing[position.symbol])
            for position in self.positions.values()
            if position.symbol in pricing
        )
        return self.cash + holdings
