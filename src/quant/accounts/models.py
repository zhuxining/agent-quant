"""Domain models for account state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from quant.core.types import AccountSnapshot, PositionSnapshot


@dataclass(slots=True)
class Position:
	"""Represents a single open position."""

	symbol: str
	quantity: float
	avg_price: float
	last_price: float | None = None

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
	realized_pnl: float = 0.0

	def equity(self, pricing: dict[str, float]) -> float:
		"""Return current equity using provided pricing snapshot."""
		holdings = sum(
			position.market_value(pricing[position.symbol])
			for position in self.positions.values()
			if position.symbol in pricing
		)
		return self.cash + holdings

	def to_snapshot(self) -> AccountSnapshot:
		"""Convert the domain entity into a snapshot for storage."""
		return AccountSnapshot(
			cash=self.cash,
			positions={
				symbol: PositionSnapshot(
					symbol=symbol,
					quantity=position.quantity,
					avg_price=position.avg_price,
					last_price=position.last_price,
				)
				for symbol, position in self.positions.items()
			},
			realized_pnl=self.realized_pnl,
			timestamp=self.updated_at,
		)

	@classmethod
	def from_snapshot(cls, account_id: str, snapshot: AccountSnapshot) -> Account:
		"""Restore the domain entity from a persisted snapshot."""
		return cls(
			account_id=account_id,
			cash=snapshot.cash,
			positions={
				symbol: Position(
					symbol=symbol,
					quantity=position.quantity,
					avg_price=position.avg_price,
					last_price=position.last_price,
				)
				for symbol, position in snapshot.positions.items()
			},
			updated_at=snapshot.timestamp,
			realized_pnl=snapshot.realized_pnl,
		)
