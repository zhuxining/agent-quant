"""Repository implementations for account persistence."""

from __future__ import annotations

from threading import Lock

from quant.core.types import AccountSnapshot


class InMemoryAccountRepository:
    """Thread-safe in-memory repository useful for testing and prototyping."""

    def __init__(self, snapshot: AccountSnapshot | None = None) -> None:
        self._snapshot = snapshot or AccountSnapshot(cash=0.0)
        self._lock = Lock()

    def load(self) -> AccountSnapshot:
        """Return the cached snapshot."""
        with self._lock:
            return self._snapshot

    def save(self, snapshot: AccountSnapshot) -> None:
        """Persist the snapshot in memory."""
        with self._lock:
            self._snapshot = snapshot
