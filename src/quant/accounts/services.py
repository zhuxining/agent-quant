"""Account service layer coordinating repository operations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from quant.accounts.models import Account, Position
from quant.core.interfaces import AccountRepository
from quant.core.types import AccountSnapshot, ExecutedTrade, TradeSignal

_EPSILON = 1e-9


class AccountServiceError(RuntimeError):
	"""Base error raised for account service failures."""


class InvalidSignalError(AccountServiceError):
	"""Raised when a signal is malformed or cannot be executed."""


class InsufficientFundsError(AccountServiceError):
	"""Raised when cash is insufficient for a buy order."""


class PositionShortfallError(AccountServiceError):
	"""Raised when attempting to sell more than the held quantity."""


@dataclass(slots=True)
class AccountOverview:
	"""Lightweight view of the account state for reporting."""

	account_id: str
	cash: float
	realized_pnl: float
	equity: float
	positions: Sequence[Position]
	updated_at: datetime


class AccountService:
	"""Apply trade signals, manage cash, and expose account projections."""

	def __init__(self, repository: AccountRepository, account_id: str = "default") -> None:
		self._repository = repository
		self._account_id = account_id

	def initialize(
		self,
		*,
		cash: float,
		positions: Iterable[Position] | None = None,
		realized_pnl: float = 0.0,
	) -> AccountSnapshot:
		"""Bootstrap the account with an initial snapshot."""
		account = Account(
			account_id=self._account_id,
			cash=cash,
			realized_pnl=realized_pnl,
			positions={position.symbol: position for position in positions or []},
		)
		snapshot = account.to_snapshot()
		self._repository.save(snapshot, self._account_id)
		return snapshot

	def get_snapshot(self) -> AccountSnapshot:
		"""Return the latest stored snapshot."""
		return self._repository.load(self._account_id)

	def get_account(self) -> Account:
		"""Return the domain model representation of the account."""
		snapshot = self.get_snapshot()
		return Account.from_snapshot(self._account_id, snapshot)

	def list_positions(self) -> Sequence[Position]:
		"""Return the current list of open positions."""
		return tuple(self.get_account().positions.values())

	def list_trades(self, *, limit: int | None = None) -> Sequence[ExecutedTrade]:
		"""Retrieve recorded trade executions."""
		return tuple(self._repository.list_trades(self._account_id, limit=limit))

	def valuation(self, pricing: Mapping[str, float]) -> float:
		"""Return total equity for the account given pricing data."""
		snapshot = self.get_snapshot()
		return snapshot.equity(pricing)

	def overview(self, pricing: Mapping[str, float] | None = None) -> AccountOverview:
		"""Return an aggregate overview suitable for dashboards."""
		account = self.get_account()
		equity = account.equity(dict(pricing or {})) if pricing else account.cash
		return AccountOverview(
			account_id=self._account_id,
			cash=account.cash,
			realized_pnl=account.realized_pnl,
			equity=equity,
			positions=tuple(account.positions.values()),
			updated_at=account.updated_at,
		)

	def apply_signals(
		self,
		signals: Sequence[TradeSignal],
		pricing: Mapping[str, float],
	) -> AccountSnapshot:
		"""Apply a batch of signals sequentially and return the final snapshot."""
		snapshot: AccountSnapshot | None = None
		for signal in signals:
			price = pricing.get(signal.symbol)
			if price is None:
				raise InvalidSignalError(f"缺少 {signal.symbol} 的价格信息")
			snapshot = self.apply_signal(signal, price)
		return snapshot or self.get_snapshot()

	def apply_signal(
		self,
		signal: TradeSignal,
		execution_price: float | None = None,
	) -> AccountSnapshot:
		"""Update the account snapshot according to the trade signal."""
		account = self.get_account()
		side = signal.side.upper().strip()
		if side not in {"BUY", "SELL", "HOLD"}:
			raise InvalidSignalError(f"未知的交易方向: {signal.side}")
		if side == "HOLD" or signal.quantity <= _EPSILON:
			return account.to_snapshot()

		execution_price = self._resolve_price(signal.symbol, side, execution_price, account)
		quantity = signal.quantity

		realized_pnl = 0.0
		position = account.positions.get(signal.symbol)

		if side == "BUY":
			required_cash = execution_price * quantity
			if account.cash + _EPSILON < required_cash:
				raise InsufficientFundsError(
					f"账户现金不足，需 {required_cash:.2f}，当前 {account.cash:.2f}"
				)
			account.cash -= required_cash
			if position is None:
				position = Position(
					symbol=signal.symbol,
					quantity=quantity,
					avg_price=execution_price,
				)
				account.positions[signal.symbol] = position
			else:
				total_cost = position.avg_price * position.quantity + execution_price * quantity
				position.quantity += quantity
				position.avg_price = total_cost / position.quantity
			position.last_price = execution_price
		elif side == "SELL":
			if position is None or position.quantity + _EPSILON < quantity:
				raise PositionShortfallError(
					f"可用仓位不足，持仓 {position.quantity if position else 0.0}，"
					f"请求卖出 {quantity}"
				)
			realized_pnl = (execution_price - position.avg_price) * quantity
			position.quantity -= quantity
			account.cash += execution_price * quantity
			account.realized_pnl += realized_pnl
			if position.quantity <= _EPSILON:
				del account.positions[signal.symbol]
			else:
				position.last_price = execution_price

		account.updated_at = datetime.utcnow()
		snapshot = account.to_snapshot()
		if signal.symbol in snapshot.positions:
			snapshot.positions[signal.symbol].last_price = execution_price
		self._repository.save(snapshot, self._account_id)
		self._repository.record_trade(
			ExecutedTrade(
				symbol=signal.symbol,
				side=side,
				quantity=quantity,
				price=execution_price,
				realized_pnl=realized_pnl,
				metadata={
					"confidence": signal.confidence,
					"signal_metadata": signal.metadata,
				},
			),
			self._account_id,
		)
		return snapshot

	def _resolve_price(
		self,
		symbol: str,
		side: str,
		execution_price: float | None,
		account: Account,
	) -> float:
		"""Determine the execution price, falling back to stored values when possible."""
		if execution_price and execution_price > 0:
			return execution_price
		position = account.positions.get(symbol)
		if position and position.last_price and position.last_price > 0:
			return position.last_price
		if side == "SELL" and position:
			return position.avg_price
		raise InvalidSignalError(f"缺少 {symbol} 的成交价格")
