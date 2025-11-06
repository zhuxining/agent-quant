"""Account repository implementations abstracting persistence layer."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from copy import deepcopy
from pathlib import Path
from threading import Lock

from sqlalchemy import delete
from sqlmodel import Session, select

from quant.core.interfaces import AccountRepository
from quant.core.types import AccountSnapshot, ExecutedTrade

try:
    from src.models.account import AccountRecord, PositionRecord, TradeRecord
except ModuleNotFoundError:  # pragma: no cover - support direct invocation without editable install
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[3]))
    from src.models.account import AccountRecord, PositionRecord, TradeRecord

try:
    from src.core.db import engine as _async_engine
except ModuleNotFoundError:  # pragma: no cover - fallback for isolated tests
    _async_engine = None

_DEFAULT_ACCOUNT_ID = "default"


class InMemoryAccountRepository(AccountRepository):
	"""Thread-safe in-memory repository useful for testing and prototyping."""

	def __init__(self, snapshots: dict[str, AccountSnapshot] | None = None) -> None:
		initial_snapshot = AccountSnapshot(cash=0.0)
		self._snapshots = {**{_DEFAULT_ACCOUNT_ID: initial_snapshot}, **(snapshots or {})}
		self._trades: dict[str, list[ExecutedTrade]] = defaultdict(list)
		for account_id, snapshot in self._snapshots.items():
			self._snapshots[account_id] = deepcopy(snapshot)
		self._lock = Lock()

	def load(self, account_id: str = _DEFAULT_ACCOUNT_ID) -> AccountSnapshot:
		"""Return the cached snapshot."""
		with self._lock:
			snapshot = self._snapshots.get(account_id)
			if snapshot is None:
				snapshot = AccountSnapshot(cash=0.0)
				self._snapshots[account_id] = snapshot
			return deepcopy(snapshot)

	def save(self, snapshot: AccountSnapshot, account_id: str = _DEFAULT_ACCOUNT_ID) -> None:
		"""Persist the snapshot in memory."""
		with self._lock:
			self._snapshots[account_id] = deepcopy(snapshot)

	def record_trade(self, trade: ExecutedTrade, account_id: str = _DEFAULT_ACCOUNT_ID) -> None:
		"""Append a trade fill record."""
		with self._lock:
			self._trades[account_id].append(deepcopy(trade))

	def list_trades(
		self,
		account_id: str = _DEFAULT_ACCOUNT_ID,
		*,
		limit: int | None = None,
	) -> Sequence[ExecutedTrade]:
		"""Return recent trades ordered by execution time descending."""
		with self._lock:
			history = sorted(
				(self._trades.get(account_id) or []),
				key=lambda trade: trade.executed_at,
				reverse=True,
			)
			if limit is not None:
				history = history[:limit]
			return tuple(deepcopy(trade) for trade in history)


def _default_session_factory() -> Session:
    if _async_engine is None:
        raise RuntimeError("Database engine is not configured.")
    return Session(_async_engine.sync_engine)


class SQLModelAccountRepository(AccountRepository):
	"""SQL-backed repository using the centralized model definitions."""

	def __init__(self, session_factory: Callable[[], Session] | None = None) -> None:
		self._session_factory = session_factory or _default_session_factory

	def load(self, account_id: str = _DEFAULT_ACCOUNT_ID) -> AccountSnapshot:
		session = self._session_factory()
		try:
			account = session.exec(
				select(AccountRecord).where(AccountRecord.account_id == account_id)
			).one_or_none()
			if account is None:
				return AccountSnapshot(cash=0.0)
			position_records = session.exec(
				select(PositionRecord).where(PositionRecord.account_id == account_id)
			).all()
			positions = {
				record.symbol: record.to_snapshot()
				for record in position_records
			}
			return account.to_snapshot(positions)
		finally:
			session.close()

	def save(self, snapshot: AccountSnapshot, account_id: str = _DEFAULT_ACCOUNT_ID) -> None:
		session = self._session_factory()
		try:
			account = session.exec(
				select(AccountRecord).where(AccountRecord.account_id == account_id)
			).one_or_none()
			if account is None:
				account = AccountRecord(account_id=account_id)
			account.apply_snapshot(snapshot)
			session.add(account)
			session.exec(delete(PositionRecord).where(PositionRecord.account_id == account_id))
			for position in snapshot.positions.values():
				record = PositionRecord.from_snapshot(account_id, position)
				session.add(record)
			session.commit()
		finally:
			session.close()

	def record_trade(self, trade: ExecutedTrade, account_id: str = _DEFAULT_ACCOUNT_ID) -> None:
		session = self._session_factory()
		try:
			session.add(TradeRecord.from_trade(account_id, trade))
			session.commit()
		finally:
			session.close()

	def list_trades(
		self,
		account_id: str = _DEFAULT_ACCOUNT_ID,
		*,
		limit: int | None = None,
	) -> Sequence[ExecutedTrade]:
		session = self._session_factory()
		try:
			statement = select(TradeRecord).where(TradeRecord.account_id == account_id)
			statement = statement.order_by(TradeRecord.executed_at.desc())
			if limit is not None:
				statement = statement.limit(limit)
			records = session.exec(statement).all()
			return tuple(record.to_trade() for record in records)
		finally:
			session.close()
