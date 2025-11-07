"""Utility classes for maintaining the tradable symbol universe."""

from __future__ import annotations

from collections.abc import Callable, Iterable, MutableSet
from pathlib import Path

from sqlmodel import Session, select

try:
	from src.models.symbol import SymbolRecord
except ModuleNotFoundError:  # pragma: no cover - support direct invocation without editable install
	import sys

	sys.path.append(str(Path(__file__).resolve().parents[3]))
	from src.models.symbol import SymbolRecord  # type: ignore[no-redef]

try:
	from src.core.db import engine as _async_engine
except ModuleNotFoundError:  # pragma: no cover - fallback when DB is unavailable
	_async_engine = None


class SymbolRegistry:
	"""In-memory registry of symbols to drive data ingestion."""

	def __init__(self, seed: Iterable[str] | None = None) -> None:
		initial = [symbol.upper() for symbol in seed or []]
		self._symbols: MutableSet[str] = set(initial)
		self._ordered: list[str] | None = sorted(initial) if initial else None

	def list_all(self) -> list[str]:
		"""Return the sorted list of configured symbols."""
		if self._ordered is not None:
			return list(self._ordered)
		return sorted(self._symbols)

	def add(self, symbol: str) -> None:
		"""Register a symbol."""
		self._symbols.add(symbol.upper())
		self._ordered = None

	def remove(self, symbol: str) -> None:
		"""Remove a symbol if it exists."""
		self._symbols.discard(symbol.upper())
		self._ordered = None

	def clear(self) -> None:
		"""Reset the registry."""
		self._symbols.clear()
		self._ordered = None


def _default_session_factory() -> Session:
	if _async_engine is None:
		raise RuntimeError("Database engine is not configured.")
	return Session(_async_engine.sync_engine)


class DatabaseSymbolRegistry(SymbolRegistry):
	"""Registry powered by the primary SQL database."""

	def __init__(self, session_factory: Callable[[], Session] | None = None) -> None:
		super().__init__()
		self._session_factory = session_factory or _default_session_factory

	def refresh(self, *, include_inactive: bool = False) -> list[str]:
		"""Reload the registry from the DB and return the sorted list."""
		with self._session_factory() as session:
			statement = select(SymbolRecord.symbol).order_by(
				SymbolRecord.priority.desc(),
				SymbolRecord.symbol,
			)
			if not include_inactive:
				statement = statement.where(SymbolRecord.is_active.is_(True))
			rows = session.exec(statement).all()
		ordered = [symbol.upper() for symbol in rows]
		self._symbols = set(ordered)
		self._ordered = ordered
		return list(self._ordered)
